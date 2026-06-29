from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("siim-download.drive")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
]


def get_service(credentials_path: str | Path):
    creds = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def resolve_or_create_folder(
    service,
    folder_name: str,
    parent_id: str,
) -> str:
    query = (
        f"name='{folder_name}' and "
        f"'{parent_id}' in parents and "
        f"mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    existing = (
        service.files()
        .list(q=query, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True)
        .execute()
    )
    items = existing.get("files", [])
    if items:
        return items[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = (
        service.files()
        .create(
            body=metadata,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    logger.info("Pasta criada no Drive: %s (ID: %s)", folder_name, folder["id"])
    return folder["id"]


def upload_pdf(
    file_path: str | Path,
    folder_id: str,
    credentials_path: str | Path,
    *,
    project_folder_name: Optional[str] = None,
    project_folder_id: Optional[str] = None,
    delete_local: bool = False,
) -> Optional[str]:
    try:
        service = get_service(credentials_path)

        target_folder = folder_id
        if project_folder_id:
            target_folder = project_folder_id
        elif project_folder_name:
            target_folder = resolve_or_create_folder(service, project_folder_name, folder_id)

        media = MediaFileUpload(str(file_path), mimetype="application/pdf")
        metadata = {
            "name": Path(file_path).name,
            "parents": [target_folder],
        }

        uploaded = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )

        file_id = uploaded["id"]
        link = uploaded.get("webViewLink", "")
        logger.info("PDF enviado para o Drive: %s (ID: %s)", link, file_id)

        if delete_local:
            Path(file_path).unlink(missing_ok=True)
            logger.info("Arquivo local removido: %s", file_path)

        return file_id

    except Exception:
        logger.exception("Erro ao enviar %s para o Drive", file_path)
        return None

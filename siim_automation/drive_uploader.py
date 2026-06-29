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


def upload_pdf(
    file_path: str | Path,
    folder_id: str,
    credentials_path: str | Path,
    *,
    delete_local: bool = False,
) -> Optional[str]:
    try:
        creds = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=SCOPES,
        )
        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        media = MediaFileUpload(str(file_path), mimetype="application/pdf")
        metadata = {
            "name": Path(file_path).name,
            "parents": [folder_id],
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

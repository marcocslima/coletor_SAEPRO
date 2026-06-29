from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger("siim-download.sheet")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def _col_letter_to_index(col: str | int) -> int:
    if isinstance(col, int):
        return col
    col = col.upper()
    result = 0
    for ch in col:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result


def get_document_types(
    spreadsheet_id: str,
    credentials_path: str | Path,
    tab_name: str = "config",
    header_rows: int = 1,
) -> List[str]:
    creds = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(spreadsheet_id).worksheet(tab_name)
    except gspread.WorksheetNotFound:
        logger.info("Aba '%s' nao encontrada na planilha.", tab_name)
        return []

    doc_names = sheet.col_values(1)
    flags = sheet.col_values(2)

    if header_rows > 0:
        doc_names = doc_names[header_rows:]
        flags = flags[header_rows:]

    result = []
    for name, flag in zip(doc_names, flags):
        name = name.strip()
        flag = flag.strip().lower()
        if name and flag == "x":
            result.append(name)

    logger.info(
        "Documentos marcados na aba '%s': %d encontrados.",
        tab_name,
        len(result),
    )
    return result


def get_projects(
    spreadsheet_id: str,
    credentials_path: str | Path,
    column: str | int = "A",
    header_rows: int = 1,
) -> List[str]:
    creds = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)

    sheet = client.open_by_key(spreadsheet_id).sheet1
    col_index = _col_letter_to_index(column)
    values = sheet.col_values(col_index)

    if header_rows > 0:
        values = values[header_rows:]

    projects = [v.strip() for v in values if v.strip()]
    logger.info(
        "Projetos carregados da planilha: %d encontrados.",
        len(projects),
    )
    return projects

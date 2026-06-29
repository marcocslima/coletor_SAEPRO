#!/usr/bin/env python3
"""
Automação SIIM/APROVE para download de PDFs de projetos SAEPRO.

Fluxo automatizado:
1. Login no SIIM com credenciais vindas do .env.
2. Continuação sem troca de senha, caso o alerta apareça.
3. Entrada no módulo SAEPRO.
4. Consulta dos projetos configurados.
5. Abertura da primeira linha de resultado pelo ícone de edição/lápis.
6. Navegação até ANÁLISE FISCALIZAÇÃO TRIBUTÁRIA > Documentos.
7. Download do documento PROJETO SIMPLIFICADO.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import quote

from dotenv import load_dotenv
from playwright.async_api import (
    Browser,
    BrowserContext,
    Download,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

import sheet_reader
import drive_uploader

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SIIM_URL = os.getenv("SIIM_URL", "https://siim21.cijun.sp.gov.br/CA").strip()
SIIM_ORGAO = os.getenv("SIIM_ORGAO", "PREFEITURA DO MUNICÍPIO DE JUNDIAÍ").strip()
SIIM_USER = os.getenv("SIIM_USER", "").strip()
SIIM_PASSWORD = os.getenv("SIIM_PASSWORD", "").strip()
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", str(Path.home() / "Downloads"))).expanduser()
HEADLESS = os.getenv("HEADLESS", "false").strip().lower() in {"1", "true", "yes", "sim"}
CHROME_PATH = os.getenv("CHROME_PATH", "").strip() or None
# Se CHROME_PATH não foi definido e o Playwright padrão não existe, tenta Chrome for Testing
if not CHROME_PATH:
    _cft = Path("/tmp/opencode/chrome-for-testing/chrome-linux64/chrome")
    if _cft.exists():
        CHROME_PATH = str(_cft)
        os.environ.setdefault("FONTCONFIG_PATH", "/tmp/opencode/extracted_libs/etc/fonts")
        os.environ.setdefault("XDG_DATA_HOME", "/tmp/opencode/extracted_libs/usr/share")
        lib_paths = os.environ.get("LD_LIBRARY_PATH", "")
        if "/tmp/opencode/extracted_libs/usr/lib/x86_64-linux-gnu" not in lib_paths:
            os.environ["LD_LIBRARY_PATH"] = "/tmp/opencode/extracted_libs/usr/lib/x86_64-linux-gnu:" + lib_paths
        print(f"INFO: Usando Chrome for Testing detectado em: {CHROME_PATH}")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS", "").strip()
GOOGLE_SHEET_CONFIG_TAB = os.getenv("GOOGLE_SHEET_CONFIG_TAB", "config").strip()
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()

PROJECTS: list[str] = []
if GOOGLE_SHEET_ID and GOOGLE_SHEET_CREDENTIALS:
    creds_path = Path(GOOGLE_SHEET_CREDENTIALS)
    if not creds_path.is_absolute():
        creds_path = BASE_DIR / creds_path
    if not creds_path.exists():
        print(f"ERRO: Arquivo de credenciais Google nao encontrado: {creds_path}")
        PROJECTS = []
    else:
        try:
            PROJECTS = sheet_reader.get_projects(GOOGLE_SHEET_ID, creds_path)
        except Exception as e:
            print(f"ERRO ao ler planilha Google: {e}")
            PROJECTS = []
else:
    PROJECTS = [p.strip() for p in os.getenv("PROJECTS", "SAEPRO2025/6485,SAEPRO2025/6865,SAEPRO2025/6884").split(",") if p.strip()]

DOCUMENT_TYPES: list[str] = []
if GOOGLE_SHEET_ID and GOOGLE_SHEET_CREDENTIALS:
    creds_path = Path(GOOGLE_SHEET_CREDENTIALS)
    if not creds_path.is_absolute():
        creds_path = BASE_DIR / creds_path
    if creds_path.exists():
        try:
            DOCUMENT_TYPES = sheet_reader.get_document_types(
                GOOGLE_SHEET_ID, creds_path, GOOGLE_SHEET_CONFIG_TAB
            )
        except Exception as e:
            print(f"ERRO ao ler configuração de documentos da planilha: {e}")
if not DOCUMENT_TYPES:
    DOCUMENT_TYPES = ["PROJETO SIMPLIFICADO"]

LOGIN_TIMEOUT = 45_000
PAGE_TIMEOUT = 45_000
ACTION_TIMEOUT = 15_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("siim-download")


def require_env() -> None:
    missing = []
    if not SIIM_USER:
        missing.append("SIIM_USER")
    if not SIIM_PASSWORD:
        missing.append("SIIM_PASSWORD")
    if missing:
        raise RuntimeError(f"Variáveis ausentes no .env: {', '.join(missing)}")
    if not PROJECTS:
        raise RuntimeError(
            "Nenhum projeto configurado. Defina PROJECTS no .env "
            "ou configure GOOGLE_SHEET_ID + GOOGLE_SHEET_CREDENTIALS."
        )
    if not DOCUMENT_TYPES:
        raise RuntimeError(
            "Nenhum tipo de documento configurado. Adicione a aba 'config' na planilha "
            "com os documentos desejados, ou o padrao 'PROJETO SIMPLIFICADO' sera usado."
        )
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def safe_project_name(project: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", project).strip("_")


def _resolve_creds_path() -> Optional[Path]:
    if not GOOGLE_SHEET_CREDENTIALS:
        return None
    p = Path(GOOGLE_SHEET_CREDENTIALS)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p if p.exists() else None


async def wait_ready(page: Page, timeout: int = PAGE_TIMEOUT) -> None:
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightTimeoutError:
        logger.debug("Timeout aguardando networkidle; continuando com o DOM carregado.")


async def click_first_visible(page: Page, selectors_or_texts: Iterable[str], timeout: int = ACTION_TIMEOUT) -> bool:
    for item in selectors_or_texts:
        try:
            if item.startswith("text=") or item.startswith("css=") or item.startswith("xpath="):
                loc = page.locator(item)
            else:
                loc = page.get_by_text(item, exact=False)
            if await loc.first.count() > 0:
                await loc.first.click(timeout=timeout)
                return True
        except PlaywrightError:
            continue
    return False


async def login(page: Page) -> None:
    logger.info("Acessando página de login: %s", SIIM_URL)
    await page.goto(SIIM_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
    await wait_ready(page)

    try:
        orgao_select = page.locator("select").first
        if await orgao_select.count() > 0:
            await orgao_select.select_option(label=SIIM_ORGAO, timeout=5_000)
            logger.info("Órgão selecionado: %s", SIIM_ORGAO)
    except PlaywrightError:
        logger.info("Não foi necessário selecionar órgão, ou o órgão já estava selecionado.")

    user_field = page.locator("input[placeholder*='Usuário'], input[placeholder*='E-mail'], input[type='email'], input[name*='user' i], input[name*='login' i]").first
    pass_field = page.locator("input[type='password']").first

    await user_field.fill(SIIM_USER, timeout=ACTION_TIMEOUT)
    await pass_field.fill(SIIM_PASSWORD, timeout=ACTION_TIMEOUT)

    logger.info("Enviando login.")
    async with page.expect_navigation(wait_until="domcontentloaded", timeout=LOGIN_TIMEOUT):
        await page.get_by_role("button", name=re.compile("login", re.I)).click(timeout=ACTION_TIMEOUT)
    await wait_ready(page)


async def handle_password_warning(page: Page) -> None:
    logger.info("Verificando alerta de troca de senha.")
    possible_links = [
        "continuar sem trocar a senha",
        "sob sua conta e risco",
        "text=ou clique aqui para continuar sem trocar a senha",
    ]
    clicked = await click_first_visible(page, possible_links, timeout=8_000)
    if clicked:
        logger.info("Alerta de troca de senha tratado: continuar sem trocar.")
        await wait_ready(page)
    else:
        logger.info("Alerta de troca de senha não apareceu, ou já foi dispensado.")


async def open_saepromodule(page: Page) -> None:
    logger.info("Entrando no módulo SAEPRO.")
    if "APROVE" in page.url.upper():
        logger.info("Módulo APROVE/SAEPRO já está aberto.")
        return

    # O link do SAEPRO usa target=_blank (abre nova aba), então navegamos diretamente
    # pela URL de abertura de aplicação do CA.
    SAEPRO_OPEN_URL = (
        "https://siim21.cijun.sp.gov.br/CA/Aplicacao/AbrirAplicacao"
        "?sigla_projeto=APROVE&tipo_projeto=10"
        "&descricao_projeto=SAEPRO%20-%20Aprova%C3%A7%C3%A3o%20de%20Projetos%20de%20Obras"
        "&possui_mobile=False&possui_computador=True&novo_servidor=21"
    )
    await page.goto(SAEPRO_OPEN_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
    await wait_ready(page)


async def dismiss_password_modal_if_present(page: Page) -> None:
    """Fecha o modal de troca de senha caso ele apareça em qualquer momento da navegação."""
    possible_links = [
        "continuar sem trocar a senha",
        "sob sua conta e risco",
        "text=ou clique aqui para continuar sem trocar a senha",
    ]
    for item in possible_links:
        try:
            if item.startswith("text="):
                loc = page.locator(item)
            else:
                loc = page.get_by_text(item, exact=False)
            if await loc.first.count() > 0:
                await loc.first.click(timeout=5_000)
                logger.info("Modal de senha dispensado durante navegação.")
                await wait_ready(page)
                return
        except PlaywrightError:
            continue


async def open_project_from_search(page: Page, project: str) -> None:
    logger.info("Consultando projeto %s.", project)
    encoded = quote(project, safe="")
    url = f"https://siim21.cijun.sp.gov.br/PMJ/APROVE/ConsultaDetalhada?filtroPesquisaRapida=&pesquisaRapida={encoded}"
    await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
    await wait_ready(page)

    # Verifica e fecha modal de senha que pode reaparecer ao navegar.
    # Após dispensar o modal, o sistema pode redirecionar para o portal principal,
    # então renavegamos para a URL do projeto.
    modal_dispensed = False
    possible_links = [
        "continuar sem trocar a senha",
        "sob sua conta e risco",
        "text=ou clique aqui para continuar sem trocar a senha",
    ]
    for item in possible_links:
        try:
            loc = page.locator(item) if item.startswith("text=") else page.get_by_text(item, exact=False)
            if await loc.first.count() > 0:
                await loc.first.click(timeout=5_000)
                logger.info("Modal de senha dispensado; renavegando para URL do projeto.")
                await wait_ready(page)
                modal_dispensed = True
                break
        except PlaywrightError:
            continue

    if modal_dispensed:
        # Renaviega para a URL do projeto após dispensar o modal
        await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
        await wait_ready(page)

    # Aguarda indicador de resultados com múltiplos seletores possíveis
    resultado_encontrado = False
    for resultado_sel in [
        "text=Resultados",
        "text=resultado",
        "table tbody tr",
        ".resultado",
        "[class*='result']",
    ]:
        try:
            await page.locator(resultado_sel).first.wait_for(timeout=10_000)
            resultado_encontrado = True
            logger.info("Resultados detectados via seletor: %s", resultado_sel)
            break
        except PlaywrightTimeoutError:
            continue

    if not resultado_encontrado:
        # Tira screenshot diagnóstico e lança erro descritivo
        diag = DOWNLOAD_DIR / f"diag_{safe_project_name(project)}_sem_resultado.png"
        try:
            await page.screenshot(path=str(diag), full_page=True)
            logger.warning("Screenshot diagnóstico salvo: %s", diag)
        except PlaywrightError:
            pass
        raise RuntimeError(
            f"Nenhum resultado encontrado para '{project}'. "
            "Verifique o screenshot diagnóstico e confirme se o projeto existe no sistema."
        )

    # Verifica se os resultados correspondem ao projeto esperado
    page_text = await page.locator("body").inner_text(timeout=5_000)
    if project not in page_text:
        logger.warning("Projeto '%s' não encontrado no texto da página; forçando recarga.", project)
        await page.reload(wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
        await wait_ready(page)
        # Tenta novamente detectar resultados após recarga
        for resultado_sel in ["text=Resultados", "text=resultado", "table tbody tr", ".resultado", "[class*='result']"]:
            try:
                await page.locator(resultado_sel).first.wait_for(timeout=10_000)
                break
            except PlaywrightTimeoutError:
                continue

    await page.mouse.wheel(0, 1000)
    await asyncio.sleep(0.5)

    logger.info("Abrindo primeira linha dos resultados pelo ícone de edição.")
    await asyncio.sleep(1.0)  # aguarda renderização completa da tabela

    # Tenta localizar a tabela de resultados (evitando outras tabelas na página)
    # A tabela de resultados geralmente tem cabeçalhos como "Projeto", "Interessado", etc.
    result_table = page.locator("table.table-striped thead").filter(has_text=re.compile(r"Projeto|Interessado|Situação", re.I)).locator("xpath=..")
    if await result_table.count() == 0:
        result_table = page.locator("table").nth(0)
    first_row = result_table.locator("tbody tr").first
    if await first_row.count() == 0:
        first_row = page.locator("table tbody tr").first
    if await first_row.count() == 0:
        first_row = page.locator("xpath=(//*[contains(., '" + project + "')]/ancestor::*[self::tr or contains(@class,'row')])[1]")

    # Extrai o CodigoProjeto da linha de resultados ANTES de clicar
    project_id_da_linha = await page.evaluate("""(proj) => {
        try {
            const links = document.querySelectorAll('a[onclick*="codigoProjeto"], button[onclick*="codigoProjeto"], i[onclick*="codigoProjeto"]');
            for (const el of links) {
                const m = el.getAttribute('onclick').match(/codigoProjeto[=:](\\d+)/i) || el.getAttribute('data-id') || el.getAttribute('data-codigo');
                if (m && m[1]) return parseInt(m[1]);
                if (el.getAttribute('data-id')) return parseInt(el.getAttribute('data-id'));
                if (el.getAttribute('data-codigo')) return parseInt(el.getAttribute('data-codigo'));
            }
            const trs = document.querySelectorAll('table tbody tr');
            for (const tr of trs) {
                if (tr.textContent.includes(proj)) {
                    const html = tr.innerHTML;
                    const m = html.match(/codigoProjeto[=:"](\\d+)/i);
                    if (m) return parseInt(m[1]);
                }
            }
        } catch(e) {}
        return null;
    }""", project)
    if project_id_da_linha:
        logger.info("CodigoProjeto extraído da linha de resultados: %s", project_id_da_linha)

    try:
        await first_row.scroll_into_view_if_needed(timeout=5_000)
    except PlaywrightError:
        pass

    edit_icon = first_row.locator("i.fa-pencil, i.glyphicon-pencil, .fa-pencil, .glyphicon-pencil, [title*='Editar' i], a:has(i)").first
    if await edit_icon.count() > 0:
        await edit_icon.click(timeout=ACTION_TIMEOUT)
    else:
        await first_row.locator("a, button, i").nth(0).click(timeout=ACTION_TIMEOUT)
    await wait_ready(page)
    logger.info("URL após edição: %s", page.url)

    # Armazena o project_id para uso posterior
    if project_id_da_linha:
        await page.evaluate("window._projectId = " + str(project_id_da_linha))


async def get_project_id(page: Page) -> tuple[int | None, str | None]:
    """Extrai CodigoProjeto da URL, window._projectId, Angular scope ou window.model."""
    import re as _re

    # 0. Tenta do window._projectId (definido antes de navegar)
    stored_id = await page.evaluate("window._projectId || null")
    if stored_id:
        return stored_id, None

    # 1. Tenta da URL atual
    m = _re.search(r"codigoProjeto[=:](\d+)", page.url, re.I)
    if m:
        return int(m.group(1)), None

    # 2. Tenta do Angular scope do controller ativo
    info = await page.evaluate("""() => {
        try {
            var el = document.querySelector('[ng-controller="InformacoesProjetoController"]');
            if (el) {
                var s = angular.element(el).scope();
                if (s && s.Model && s.Model.CodigoProjeto)
                    return { id: s.Model.CodigoProjeto, desc: s.Model.DescricaoNumProjeto };
            }
        } catch(e) {}
        // Fallback para window.model
        var m = window.model;
        if (m) return { id: m.CodigoProjeto || m.Id, desc: m.DescricaoNumProjeto };
        return null;
    }""")
    if info:
        return info["id"], info["desc"]
    return None, None


async def go_to_fiscalizacao_documentos(page: Page, project: str) -> None:
    logger.info("Navegando até Documentos da análise.")

    project_id = None

    # Tenta obter o project_id pelo Angular scope ou window.model
    info = await page.evaluate("""() => {
        try {
            var el = document.querySelector('[ng-controller="InformacoesProjetoController"]');
            if (el) {
                var s = angular.element(el).scope();
                if (s && s.Model && s.Model.CodigoProjeto)
                    return s.Model.CodigoProjeto;
            }
        } catch(e) {}
        var m = window.model;
        if (m) return m.CodigoProjeto || m.Id;
        return null;
    }""")
    if info:
        project_id = info

    # Fallback: window._projectId (definido na busca)
    if not project_id:
        project_id = await page.evaluate("window._projectId || null")

    # Fallback: regex na URL
    if not project_id:
        import re as _re
        m = _re.search(r"codigoProjeto[=:](\d+)", page.url, re.I)
        if m:
            project_id = int(m.group(1))

    if not project_id:
        raise RuntimeError(
            f"Não foi possível obter o ID do projeto '{project}' "
            "para navegar até a página de Documentos."
        )

    logger.info("ID do projeto: %s", project_id)
    await dismiss_password_modal_if_present(page)

    # Tenta navegar via Angular AbrirDocumentosProjeto com retry
    navegou = False
    for tentativa in range(5):
        navegou = await page.evaluate("""() => {
            try {
                var el = document.querySelector('[ng-controller="InformacoesProjetoController"]');
                if (!el) el = document.getElementById('APROVE');
                if (el) {
                    var scope = angular.element(el).scope();
                    if (scope && scope.AbrirDocumentosProjeto) {
                        scope.AbrirDocumentosProjeto();
                        return true;
                    }
                }
            } catch(e) {}
            return false;
        }""")
        if navegou:
            logger.info("AbrirDocumentosProjeto() executado (tentativa %d).", tentativa + 1)
            break
        await asyncio.sleep(1)

    if navegou:
        # Aguarda a SPA carregar
        for _ in range(20):
            await asyncio.sleep(1)
            if "Analise/Documentos" in page.url:
                break
        await wait_ready(page)
        await asyncio.sleep(2)

    # Se não navegou ou a URL não mudou, constrói a URL a partir dos parâmetros atuais
    if not navegou or "Analise/Documentos" not in page.url:
        import re as _re
        # Extrai os parâmetros da URL atual para repassar
        qparams = []
        for pname in ["codigoProjeto", "codigoFluxo", "codigoEtapa", "codigoTipoAnalise"]:
            val = _re.search(rf"{pname}=([^&]+)", page.url)
            if val:
                qparams.append(f"{pname}={val.group(1)}")
        if not any("codigoProjeto=" in p for p in qparams):
            qparams.append(f"codigoProjeto={project_id}")
        if not any("codigoTipoAnalise=" in p for p in qparams):
            qparams.append("codigoTipoAnalise=null")

        url = f"https://siim21.cijun.sp.gov.br/PMJ/APROVE/Analise/Documentos?{'&'.join(qparams)}"
        logger.info("Navegação direta para: %s", url)
        await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
        await wait_ready(page)
        await dismiss_password_modal_if_present(page)

    # Aguarda conteúdo da página de Documentos aparecer
    for doc_content_sel in [
        "table.table-striped tbody tr",
        "table tbody tr",
        "tbody",
        "text=Documentos obrigatórios",
    ]:
        try:
            await page.locator(doc_content_sel).first.wait_for(timeout=20_000)
            logger.info("Conteúdo da página Documentos detectado via: %s", doc_content_sel)
            break
        except PlaywrightTimeoutError:
            continue


async def list_available_documents(page: Page) -> list[str]:
    try:
        all_rows = await page.locator("table tbody tr").all_text_contents()
        doc_names = [re.sub(r"\s+", " ", r).strip() for r in all_rows if r.strip()]
        if doc_names:
            logger.info("Documentos encontrados na aba (%d): %s", len(doc_names), doc_names)
        else:
            logger.warning("Nenhuma linha de documento encontrada na tabela.")
        return doc_names
    except PlaywrightError:
        return []


async def save_download(download: Download, project: str, doc_name: str) -> Path:
    safe_doc = safe_project_name(doc_name)
    suggested = download.suggested_filename or f"{safe_doc}.pdf"
    ext = Path(suggested).suffix or ".pdf"
    target = DOWNLOAD_DIR / f"{safe_project_name(project)}_{safe_doc}{ext}"
    await download.save_as(str(target))
    logger.info("Arquivo salvo: %s", target)
    return target


async def download_document(page: Page, context: BrowserContext, project: str, doc_name: str) -> Optional[Path]:
    logger.info("Localizando linha '%s'.", doc_name)

    row = page.locator("tr", has_text=re.compile(re.escape(doc_name), re.I)).first
    try:
        await row.wait_for(timeout=PAGE_TIMEOUT)
    except PlaywrightTimeoutError:
        row = page.locator("td", has_text=re.compile(re.escape(doc_name), re.I)).first
        await row.wait_for(timeout=10_000)
        row = row.locator("xpath=ancestor::tr[1]")

    download_icon = row.locator("i.fa-download, .fa-download, [title*='Download' i], a[href*='arquivo'], a:has(i), button:has(i)").first
    if await download_icon.count() == 0:
        links = row.locator("a, button")
        count = await links.count()
        if count == 0:
            raise RuntimeError(f"Linha '{doc_name}' encontrada, mas sem botão/link de download.")
        download_icon = links.nth(min(1, count - 1))

    logger.info("Clicando no ícone de download do documento '%s'.", doc_name)

    try:
        async with page.expect_download(timeout=12_000) as download_info:
            await download_icon.click(timeout=ACTION_TIMEOUT)
        return await save_download(await download_info.value, project, doc_name)
    except PlaywrightTimeoutError:
        logger.info("Não houve download direto; verificando abertura de aba com PDF.")

    pdf_page: Optional[Page] = None
    try:
        async with context.expect_page(timeout=12_000) as new_page_info:
            await download_icon.click(timeout=ACTION_TIMEOUT)
        pdf_page = await new_page_info.value
        await wait_ready(pdf_page)
    except PlaywrightTimeoutError:
        pdf_page = page

    logger.info("Tentando baixar PDF pelo visualizador/URL.")
    try:
        async with pdf_page.expect_download(timeout=20_000) as download_info:
            clicked = await click_first_visible(
                pdf_page,
                [
                    "#download",
                    "button[title*='Download' i]",
                    "cr-icon-button[title*='Download' i]",
                    "[aria-label*='Download' i]",
                    "[title*='Baixar' i]",
                ],
                timeout=8_000,
            )
            if not clicked:
                await pdf_page.keyboard.press("Control+S")
        saved = await save_download(await download_info.value, project, doc_name)
    except PlaywrightTimeoutError:
        pdf_url = pdf_page.url
        logger.info("Download pelo visualizador não disparou; tentando obter conteúdo pela URL autenticada.")
        response = await context.request.get(pdf_url, timeout=PAGE_TIMEOUT)
        if not response.ok:
            raise RuntimeError(f"Falha ao baixar PDF pela URL: HTTP {response.status}")
        safe_doc = safe_project_name(doc_name)
        target = DOWNLOAD_DIR / f"{safe_project_name(project)}_{safe_doc}.pdf"
        target.write_bytes(await response.body())
        logger.info("Arquivo salvo por requisição autenticada: %s", target)
        saved = target

    if pdf_page is not page:
        await pdf_page.close()
    return saved


async def process_project(page: Page, context: BrowserContext, project: str) -> None:
    try:
        await open_project_from_search(page, project)
        await go_to_fiscalizacao_documentos(page, project)

        available = await list_available_documents(page)
        if not available:
            logger.warning("Nenhum documento encontrado na aba do projeto %s.", project)
            return

        creds_path = _resolve_creds_path()
        project_folder_id: Optional[str] = None
        if GOOGLE_DRIVE_FOLDER_ID and creds_path:
            svc = drive_uploader.get_service(creds_path)
            project_folder_id = drive_uploader.resolve_or_create_folder(
                svc, safe_project_name(project), GOOGLE_DRIVE_FOLDER_ID
            )

        for doc_name in DOCUMENT_TYPES:
            matched = any(doc_name.upper() in avail.upper() for avail in available)
            if not matched:
                logger.warning(
                    "Documento '%s' nao encontrado no projeto %s. Disponiveis: %s",
                    doc_name, project, [a[:40] for a in available],
                )
                continue

            saved = await download_document(page, context, project, doc_name)

            if GOOGLE_DRIVE_FOLDER_ID and creds_path:
                drive_uploader.upload_pdf(
                    saved,
                    GOOGLE_DRIVE_FOLDER_ID,
                    creds_path,
                    project_folder_id=project_folder_id,
                    delete_local=True,
                )

            logger.info("Documento '%s' do projeto %s concluido.", doc_name, project)

        logger.info("Projeto %s totalmente processado.", project)
    except Exception as exc:
        logger.exception("Erro ao processar projeto %s: %s", project, exc)
        screenshot = DOWNLOAD_DIR / f"erro_{safe_project_name(project)}.png"
        try:
            await page.screenshot(path=str(screenshot), full_page=True)
            logger.info("Screenshot de erro salvo em: %s", screenshot)
        except PlaywrightError:
            logger.warning("Não foi possível salvar screenshot de erro.")


async def run() -> None:
    require_env()
    logger.info("Projetos configurados: %s", ", ".join(PROJECTS))
    logger.info("Documentos a baixar: %s", ", ".join(DOCUMENT_TYPES))
    logger.info("Pasta de downloads: %s", DOWNLOAD_DIR)

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(
            headless=HEADLESS,
            executable_path=CHROME_PATH,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
            locale="pt-BR",
        )
        page = await context.new_page()
        page.set_default_timeout(ACTION_TIMEOUT)

        try:
            await login(page)
            await handle_password_warning(page)
            await open_saepromodule(page)

            for project in PROJECTS:
                await process_project(page, context, project)
        finally:           
           await context.close()
           await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
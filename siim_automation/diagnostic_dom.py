import asyncio
import logging
import os
import re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright, Page, Error as PlaywrightError

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SIIM_URL = os.getenv("SIIM_URL", "https://siim21.cijun.sp.gov.br/CA").strip()
SIIM_ORGAO = os.getenv("SIIM_ORGAO", "PREFEITURA DO MUNICÍPIO DE JUNDIAÍ").strip()
SIIM_USER = os.getenv("SIIM_USER", "").strip()
SIIM_PASSWORD = os.getenv("SIIM_PASSWORD", "")
PROJECTS = [p.strip() for p in os.getenv("PROJECTS", "").split(",") if p.strip()]
CHROME_PATH = os.getenv("CHROME_PATH", "").strip() or None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("diagnostic")

async def wait_ready(page: Page) -> None:
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

async def login(page: Page):
    logger.info("Acessando login...")
    await page.goto(SIIM_URL, wait_until="domcontentloaded")
    await wait_ready(page)
    
    try:
        await page.locator("select").first.select_option(label=SIIM_ORGAO, timeout=5000)
        logger.info("Órgão selecionado")
    except Exception:
        pass
        
    user_field = page.locator("input[placeholder*='Usuário'], input[placeholder*='E-mail'], input[type='email'], input[name*='user' i], input[name*='login' i]").first
    pass_field = page.locator("input[type='password']").first
    await user_field.fill(SIIM_USER)
    await pass_field.fill(SIIM_PASSWORD)
    
    logger.info("Enviando formulário...")
    async with page.expect_navigation(wait_until="domcontentloaded", timeout=45000):
        await page.get_by_role("button", name=re.compile("login", re.I)).click()
    await wait_ready(page)
    logger.info("Login efetuado")

async def handle_password_warning(page: Page):
    possible_links = [
        "continuar sem trocar a senha",
        "sob sua conta e risco",
        "text=ou clique aqui para continuar sem trocar a senha",
    ]
    for item in possible_links:
        try:
            loc = page.locator(item) if item.startswith("text=") else page.get_by_text(item, exact=False)
            if await loc.first.count() > 0:
                await loc.first.click(timeout=5000)
                logger.info("Aviso de senha dispensado")
                await wait_ready(page)
                return
        except Exception:
            continue

async def open_saepro(page: Page):
    logger.info("Abrindo SAEPRO...")
    SAEPRO_OPEN_URL = (
        "https://siim21.cijun.sp.gov.br/CA/Aplicacao/AbrirAplicacao"
        "?sigla_projeto=APROVE&tipo_projeto=10"
        "&descricao_projeto=SAEPRO%20-%20Aprova%C3%A7%C3%A3o%20de%20Projetos%20de%20Obras"
        "&possui_mobile=False&possui_computador=True&novo_servidor=21"
    )
    await page.goto(SAEPRO_OPEN_URL, wait_until="domcontentloaded", timeout=45000)
    await wait_ready(page)

async def open_project_from_search(page: Page, project: str) -> None:
    logger.info("Consultando projeto %s.", project)
    encoded = quote(project, safe="")
    url = f"https://siim21.cijun.sp.gov.br/PMJ/APROVE/ConsultaDetalhada?filtroPesquisaRapida=&pesquisaRapida={encoded}"
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await wait_ready(page)

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
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await wait_ready(page)

    resultado_encontrado = False
    for resultado_sel in ["text=Resultados", "text=resultado", "table tbody tr", ".resultado", "[class*='result']"]:
        try:
            await page.locator(resultado_sel).first.wait_for(timeout=10_000)
            resultado_encontrado = True
            logger.info("Resultados detectados via seletor: %s", resultado_sel)
            break
        except Exception:
            continue

    if not resultado_encontrado:
        diag_path = BASE_DIR / f"diag_{safe_project_name(project)}_sem_resultado.png"
        try:
            await page.screenshot(path=str(diag_path), full_page=True)
            logger.warning("Screenshot diagnostico salvo: %s", diag_path)
        except Exception:
            pass
        raise RuntimeError(f"Nenhum resultado encontrado para '{project}'. Screenshot salvo para diagnostico.")

    await page.mouse.wheel(0, 1000)
    await asyncio.sleep(0.5)

    logger.info("Abrindo primeira linha dos resultados pelo icone de edicao.")
    await asyncio.sleep(1.0)

    result_table = page.locator("table.table-striped thead").filter(has_text=re.compile(r"Projeto|Interessado|Situacao", re.I)).locator("xpath=..")
    if await result_table.count() == 0:
        result_table = page.locator("table").nth(0)
    first_row = result_table.locator("tbody tr").first
    if await first_row.count() == 0:
        first_row = page.locator("table tbody tr").first
    if await first_row.count() == 0:
        first_row = page.locator("xpath=(//*[contains(., '" + project + "')]/ancestor::*[self::tr or contains(@class,'row')])[1]")

    try:
        await first_row.scroll_into_view_if_needed(timeout=5_000)
    except PlaywrightError:
        pass

    edit_icon = first_row.locator("i.fa-pencil, i.glyphicon-pencil, .fa-pencil, .glyphicon-pencil, [title*='Editar' i], a:has(i)").first
    if await edit_icon.count() > 0:
        await edit_icon.click(timeout=15000)
    else:
        await first_row.locator("a, button, i").nth(0).click(timeout=15000)
    await wait_ready(page)


def safe_project_name(project: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", project).strip("_")


async def main():
    if not SIIM_USER or not SIIM_PASSWORD:
        logger.error("SIIM_USER e SIIM_PASSWORD sao obrigatorios no .env")
        return
    if not PROJECTS:
        logger.error("Defina ao menos um projeto em PROJECTS no .env")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROME_PATH,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
            locale="pt-BR",
        )
        page = await context.new_page()

        await login(page)
        await handle_password_warning(page)
        await open_saepro(page)

        project = PROJECTS[0]
        await open_project_from_search(page, project)
        await asyncio.sleep(3)

        logger.info("=== DIAGNÓSTICO DOS ELEMENTOS ===")

        all_elements = await page.locator("a, button, [role='tab'], li, div").all()
        logger.info("Total de a/button/tab/li/div: %d", len(all_elements))

        for sel in ["a", "button", "[role='tab']", "li", "span", "div"]:
            loc = page.locator(sel)
            count = await loc.count()
            for i in range(count):
                el = loc.nth(i)
                try:
                    text = await el.text_content()
                    if not text:
                        continue
                    text_clean = text.strip().replace("\n", " ")
                    if "Documentos" in text_clean:
                        visible = await el.is_visible()
                        tag = await el.evaluate("el => el.tagName")
                        classes = await el.evaluate("el => el.className")
                        outer_html = await el.evaluate("el => el.outerHTML")
                        outer_html_snippet = outer_html.strip().replace("\n", " ")[:140]
                        logger.info("MATCH: Tag=%s | Visible=%s | Text='%s' | Classes='%s'", tag, visible, text_clean[:60], classes)
                        logger.info("  Snippet: %s", outer_html_snippet)
                except Exception:
                    pass

        html_content = await page.content()
        dump_path = BASE_DIR / "page_dump.html"
        dump_path.write_text(html_content, encoding="utf-8")
        logger.info("HTML da pagina salvo em %s", dump_path)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

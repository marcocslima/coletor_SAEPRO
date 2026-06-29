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
    
    # Seleciona órgão
    try:
        await page.locator("select").first.select_option(label=SIIM_ORGAO, timeout=5000)
        logger.info("Órgão selecionado")
    except Exception:
        pass
        
    # Preenche login
    await page.locator("input[placeholder*='Usuário'], input[placeholder*='E-mail'], input[type='email'], input[name*='user' i], input[name*='login' i]").first.fill(SIIM_USER)
    await page.locator("input[type='password']").first.fill(SIIM_PASSWORD)
    
    logger.info("Enviando formulário...")
    async with page.expect_navigation(wait_until="domcontentloaded"):
        await page.get_by_role("button", name="login").click()
    await wait_ready(page)
    logger.info("Login efetuado")

async def handle_password_warning(page: Page):
    try:
        loc = page.get_by_text("continuar sem trocar a senha", exact=False)
        if await loc.first.count() > 0:
            await loc.first.click(timeout=5000)
            logger.info("Aviso de senha dispensado")
            await wait_ready(page)
    except Exception:
        pass

async def open_saepro(page: Page):
    logger.info("Abrindo SAEPRO...")
    await page.mouse.wheel(0, 1600)
    await asyncio.sleep(1)
    await page.get_by_text("SAEPRO - Aprovação de Projetos de Obras", exact=False).first.click()
    await page.wait_for_load_state("domcontentloaded")
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

    # Aguarda indicador de resultados
    resultado_encontrado = False
    for resultado_sel in ["text=Resultados", "text=resultado", "table tbody tr", ".resultado"]:
        try:
            await page.locator(resultado_sel).first.wait_for(timeout=10_000)
            resultado_encontrado = True
            logger.info("Resultados detectados via seletor: %s", resultado_sel)
            break
        except Exception:
            continue

    if not resultado_encontrado:
        raise RuntimeError(f"Nenhum resultado encontrado para '{project}'.")

    await page.mouse.wheel(0, 1000)
    await asyncio.sleep(0.5)

    logger.info("Abrindo primeira linha dos resultados pelo ícone de edição.")
    await asyncio.sleep(1.0)

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

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        
        await login(page)
        await handle_password_warning(page)
        await open_saepro(page)
        
        project = PROJECTS[0]
        await open_project_from_search(page, project)
        await asyncio.sleep(5)
        
        logger.info("=== DIAGNÓSTICO DOS ELEMENTOS ===")
        
        # 1. Buscar todos os elementos
        all_elements = await page.locator("a, button, [role='tab'], li, div").all()
        logger.info(f"Total de a/button/tab/li/div: {len(all_elements)}")
        
        # 2. Vamos listar elementos com texto Documentos
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
                        logger.info(f"MATCH: Tag={tag} | Visible={visible} | Text='{text_clean[:60]}' | Classes='{classes}'")
                        logger.info(f"  Snippet: {outer_html_snippet}")
                except Exception as e:
                    pass
                
        # Salvar o HTML
        html_content = await page.content()
        with open("page_dump.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("HTML da página salvo em page_dump.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

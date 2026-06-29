# Automação SIIM — download de PDFs de projetos

Este projeto automatiza, com Playwright, o login no SIIM de Jundiaí/SP e o download do documento **PROJETO SIMPLIFICADO** para uma lista de projetos SAEPRO.

O script realiza login, trata o aviso de troca de senha, entra no módulo **SAEPRO - Aprovação de Projetos de Obras**, consulta cada projeto, abre a primeira linha dos resultados, navega até a aba **Documentos** da análise (via Angular `AbrirDocumentosProjeto()` ou navegação direta), localiza **PROJETO SIMPLIFICADO** e salva o PDF na pasta configurada.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `siim_download_projetos.py` | Código principal da automação |
| `diagnostic_dom.py` | Script auxiliar para diagnóstico do DOM da página |
| `.env.example` | Modelo das variáveis de ambiente |
| `.env` | Credenciais reais (não versionado) |
| `requirements.txt` | Dependências Python do projeto |
| `.gitignore` | Arquivos ignorados pelo Git |

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/marcocslima/coletor_SAEPRO.git
cd coletor_SAEPRO/siim_automation

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar navegador Chromium do Playwright
playwright install chromium
```

## Configuração

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Edite o `.env` e preencha:

```env
SIIM_URL=https://siim21.cijun.sp.gov.br/CA
SIIM_ORGAO=PREFEITURA DO MUNICÍPIO DE JUNDIAÍ
SIIM_USER=seu_usuario@jundiai.sp.gov.br
SIIM_PASSWORD=sua_senha_aqui
DOWNLOAD_DIR=/home/ubuntu/Downloads
HEADLESS=false
PROJECTS=SAEPRO2025/6485,SAEPRO2025/6865,SAEPRO2025/6884
# Opcional: caminho para o Chrome do sistema (se não quiser usar o bundled do Playwright)
# CHROME_PATH=/usr/bin/google-chrome
```

Por segurança, não coloque credenciais reais no `.env.example` e não envie o arquivo `.env` para repositórios.

## Execução

```bash
cd coletor_SAEPRO/siim_automation
source .venv/bin/activate
python siim_download_projetos.py
```

Os PDFs serão salvos em `DOWNLOAD_DIR` com o padrão `{projeto}_PROJETO_SIMPLIFICADO.pdf` (ex: `SAEPRO2025_6485_PROJETO_SIMPLIFICADO.pdf`).

## Logs e diagnóstico

O script imprime logs no terminal com o progresso de cada etapa. Em caso de erro, ele salva uma captura de tela na pasta de downloads com nome `erro_{projeto}.png` para facilitar a análise.

## Observações

A interface do SIIM pode mudar. Por isso, o script usa uma combinação de seletores por texto, URLs conhecidas, fallback por ícones/linhas de tabela e injeção de funções Angular. Se algum botão ou texto mudar, talvez seja necessário ajustar os seletores.

Se o sistema solicitar CAPTCHA, autenticação adicional, sessão expirada ou troca obrigatória de senha sem opção de continuar, a automação não conseguirá prosseguir sem intervenção manual.

# Automação SIIM — download de PDFs de projetos

Este projeto automatiza, com Playwright, o login no SIIM de Jundiaí/SP e o download do documento **PROJETO SIMPLIFICADO** para uma lista de projetos SAEPRO.

O script realiza login, trata o aviso de troca de senha, entra no módulo **SAEPRO - Aprovação de Projetos de Obras**, consulta cada projeto, abre a primeira linha dos resultados, navega até **ANÁLISE FISCALIZAÇÃO TRIBUTÁRIA > Documentos**, localiza **PROJETO SIMPLIFICADO** e salva o PDF na pasta configurada.

## Arquivos

`siim_download_projetos.py` contém o código principal da automação.

`.env.example` mostra as variáveis necessárias. Copie para `.env` e preencha com suas credenciais reais.

## Instalação

Dentro da pasta do projeto, instale as dependências:

```bash
cd /home/ubuntu/siim_automation
python3 -m venv .venv
source .venv/bin/activate
pip install playwright python-dotenv
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
```

Por segurança, não coloque credenciais reais no `.env.example` e não envie o arquivo `.env` para repositórios.

## Execução

```bash
cd /home/ubuntu/siim_automation
source .venv/bin/activate
python siim_download_projetos.py
```

Os PDFs serão salvos em `DOWNLOAD_DIR`. Quando possível, o script renomeia os arquivos para um padrão como `SAEPRO2025_6485_PROJETO_SIMPLIFICADO.pdf`.

## Logs e diagnóstico

O script imprime logs no terminal com o progresso de cada etapa. Em caso de erro, ele salva uma captura de tela na pasta de downloads com nome parecido com `erro_SAEPRO2025_6485.png`, para facilitar a análise.

## Observações

A interface do SIIM pode mudar. Por isso, o script usa uma combinação de seletores por texto, URLs conhecidas e fallback por ícones/linhas de tabela. Se algum botão ou texto mudar, talvez seja necessário ajustar os seletores.

Se o sistema solicitar CAPTCHA, autenticação adicional, sessão expirada ou troca obrigatória de senha sem opção de continuar, a automação não conseguirá prosseguir sem intervenção manual.

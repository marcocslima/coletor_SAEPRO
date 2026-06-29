# Guia Completo: Automacao SIIM no Windows 11

Este guia fornece instrucoes passo a passo para executar o script de automacao SIIM no Windows 11. O script baixa automaticamente PDFs de projetos SAEPRO do sistema SIIM.

---

## Indice

1. [Pre-requisitos](#pre-requisitos)
2. [Instalacao do Python](#instalacao-do-python)
3. [Download do Projeto](#download-do-projeto)
4. [Abrir Terminal](#abrir-terminal)
5. [Criar Ambiente Virtual](#criar-ambiente-virtual)
6. [Instalar Dependencias](#instalar-dependencias)
7. [Instalar Navegadores Playwright](#instalar-navegadores-playwright)
8. [Configurar Arquivo .env](#configurar-arquivo-env)
9. [Executar o Script](#executar-o-script)
10. [Localizar PDFs Baixados](#localizar-pdfs-baixados)
11. [Solucao de Problemas](#solucao-de-problemas)

---

## Pre-requisitos

Antes de comecar, voce precisa de:

- **Windows 11** instalado
- **Conexao com a internet** ativa
- **Credenciais SIIM** validas (usuario e senha)
- ~500 MB de espaco livre em disco

---

## Instalacao do Python

### Passo 1: Verificar se Python ja esta instalado

Abra o **Prompt de Comando** (CMD) ou **PowerShell**:

1. Pressione `Windows + R`
2. Digite `cmd` e pressione Enter

Na janela que abrir, digite:

```bash
python --version
```

Se voce ver uma versao como `Python 3.9.x` ou superior, **pule para a proxima secao**. Caso contrario, continue abaixo.

### Passo 2: Baixar Python

1. Acesse [python.org](https://www.python.org/downloads/windows/)
2. Clique em **"Download Python 3.13"** (ou versao mais recente)
3. Escolha o instalador **"Windows installer (64-bit)"**

### Passo 3: Instalar Python

1. Abra o arquivo `python-3.13.x-amd64.exe` que voce baixou
2. **IMPORTANTE**: Marque a caixa "Add Python to PATH"
3. Clique em "Install Now"
4. Ate a instalacao ser concluida
5. Clique em "Close"

### Passo 4: Verificar instalacao

Abra um novo Prompt de Comando e execute:

```bash
python --version
pip --version
```

Se vir numeros de versao para ambos, esta pronto!

---

## Download do Projeto

### Via Git (recomendado)

Se tiver Git instalado:

```bash
git clone https://github.com/marcocslima/coletor_SAEPRO.git
cd coletor_SAEPRO/siim_automation
```

### Via download ZIP

1. Acesse https://github.com/marcocslima/coletor_SAEPRO
2. Clique em "Code" > "Download ZIP"
3. Extraia o conteudo em uma pasta, ex:

```
C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation\
```

---

## Abrir Terminal

Para executar os comandos seguintes, voce precisa abrir um terminal na pasta do projeto.

### Opcao 1: Prompt de Comando (CMD)

```bash
cd C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation
```

### Opcao 2: PowerShell (Recomendado)

Clique com botao direito na pasta `siim_automation` e selecione "Abrir no PowerShell", ou navegue manualmente:

```powershell
cd C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation
```

---

## Criar Ambiente Virtual

O ambiente virtual (`.venv`) isola as dependencias do projeto.

### Passo 1: Criar

```bash
python -m venv .venv
```

### Passo 2: Ativar

**No Prompt de Comando (CMD):**
```bash
.venv\Scripts\activate
```

**No PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

Se receber erro de "execution policy" no PowerShell, execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente.

### Como saber se esta ativado?

Se vir `(.venv)` no inicio da linha do terminal:

```
(.venv) C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation>
```

---

## Instalar Dependencias

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt
```

Este comando instalara:
- **playwright**: Automacao de navegador web
- **python-dotenv**: Carregamento de variaveis de ambiente

---

## Instalar Navegadores Playwright

O Playwright precisa dos navegadores para funcionar. Execute:

```bash
playwright install chromium
```

Isto baixara os navegadores necessarios (~200-300 MB). **Este passo e obrigatorio!**

---

## Configurar Arquivo .env

O arquivo `.env` contem suas credenciais SIIM e configuracoes.

### Passo 1: Copiar arquivo de exemplo

```bash
copy .env.example .env
```

### Passo 2: Preencher credenciais

Abra o arquivo `.env` com um editor de texto (Bloco de Notas ou VS Code):

```env
SIIM_URL=https://siim21.cijun.sp.gov.br/CA
SIIM_ORGAO=PREFEITURA DO MUNICIPIO DE JUNDIAI
SIIM_USER=seu_usuario@jundiai.sp.gov.br
SIIM_PASSWORD=sua_senha_aqui
DOWNLOAD_DIR=C:\Users\SeuUsuario\Downloads
HEADLESS=false
PROJECTS=SAEPRO2025/6485,SAEPRO2025/6865,SAEPRO2025/6884
# Opcional: caminho para o Chrome do sistema
# CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
```

**Substitua pelos seus valores:**

| Campo | Descricao | Exemplo |
|-------|-----------|---------|
| `SIIM_URL` | URL do SIIM | Geralmente nao muda |
| `SIIM_ORGAO` | Seu orgao | PREFEITURA DO MUNICIPIO DE JUNDIAI |
| `SIIM_USER` | Seu email/usuario | seu_usuario@jundiai.sp.gov.br |
| `SIIM_PASSWORD` | Sua senha SIIM | Sua_Senha_123! |
| `DOWNLOAD_DIR` | Onde salvar PDFs | C:\Users\SeuUsuario\Downloads |
| `HEADLESS` | Mostrar navegador? | false (true para rodar silenciosamente) |
| `PROJECTS` | Projetos a baixar | SAEPRO2025/6485,SAEPRO2025/6865 |
| `CHROME_PATH` | Chrome do sistema (opcional) | Caminho do chrome.exe |
| `GOOGLE_SHEET_ID` | ID da planilha (opcional) | 1abc123xxx... |
| `GOOGLE_SHEET_CREDENTIALS` | Caminho do JSON da service account (opcional) | credentials/google-sheets.json |

### Passo 3: Salvar o arquivo

Apos editar, salve o arquivo (Ctrl + S).

**SEGURANCA**: O arquivo `.env` contem suas credenciais. **Nunca o compartilhe ou envie para repositorios publicos!**

---

## Integracao com Google Sheets (opcional)

Ao inves de editar `PROJECTS` manualmente, voce pode buscar a lista de projetos de uma planilha do Google Sheets.

### Passo a passo

1. **Crie uma Service Account** no [Google Cloud Console](https://console.cloud.google.com):
   - Crie um projeto e ative a **Google Sheets API**
   - Vá em "APIs e Servicos" > "Credenciais" > "Criar credenciais" > "Conta de servico"
   - Apos criar, clique em "Gerenciar chaves" > "Adicionar chave" > "JSON"
   - Salve o arquivo baixado em `siim_automation\credentials\google-sheets.json`

2. **Compartilhe a planilha** com o e-mail da service account (funcao "Leitor")

3. **Configure o `.env`**:

   ```env
   GOOGLE_SHEET_CREDENTIALS=credentials\google-sheets.json
   GOOGLE_SHEET_ID=1abc123xxx...
   ```

4. **Estrutura da planilha**: os projetos devem estar na **coluna A**, um por linha, a partir da **linha 2**:

   ```
   A1: Projetos (cabecalho, ignorado)
   A2: SAEPRO2025/6485
   A3: SAEPRO2025/6865
   ```

Quando `GOOGLE_SHEET_ID` estiver configurado, o script ignora `PROJECTS` do `.env` e usa a lista da planilha.

---

## Executar o Script

Com o ambiente virtual ativado e o arquivo `.env` configurado, execute:

```bash
python siim_download_projetos.py
```

### O que esperar:

1. **Janela do navegador abrira** (a menos que `HEADLESS=true`)
2. **Faca login automaticamente** no SIIM
3. **Navega para os projetos** configurados
4. **Downloads comecam** dos PDFs

### Indicadores de sucesso:

```
Login realizado com sucesso!
Navegando para projetos...
Baixando projeto SAEPRO2025/6485...
Arquivo salvo: C:\Users\SeuUsuario\Downloads\SAEPRO2025_6485_PROJETO_SIMPLIFICADO.pdf
```

---

## Localizar PDFs Baixados

Os PDFs sao salvos na pasta configurada em `DOWNLOAD_DIR` no arquivo `.env`.

### Exemplo de estrutura:

```
C:\Users\SeuUsuario\Downloads\
  SAEPRO2025_6485_PROJETO_SIMPLIFICADO.pdf
  SAEPRO2025_6865_PROJETO_SIMPLIFICADO.pdf
  SAEPRO2025_6884_PROJETO_SIMPLIFICADO.pdf
```

---

## Solucao de Problemas

### "Python nao e reconhecido como comando"

**Causa**: Python nao foi adicionado ao PATH durante a instalacao.

**Solucao**:
1. Desinstale Python
2. Reinstale marcando **Add Python to PATH**
3. Reinicie o computador

### "ModuleNotFoundError: No module named 'playwright'"

**Causa**: Dependencias nao foram instaladas corretamente.

**Solucao**:
1. Ative o ambiente virtual: `.venv\Scripts\activate`
2. Reinstale: `pip install -r requirements.txt`
3. Verifique: `pip list`

### "Erro ao instalar Playwright browsers"

**Causa**: Problemas de permissao ou espaco em disco.

**Solucao**:
1. Execute como Administrador o terminal
2. Ative o `.venv` e tente novamente: `playwright install chromium`
3. Libere espaco em disco e tente novamente

### "SIIM_USER ou SIIM_PASSWORD nao fornecidos"

**Causa**: O arquivo `.env` nao foi configurado corretamente.

**Solucao**:
1. Verifique se o arquivo `.env` existe (nao e `.env.example`)
2. Abra e verifique se todas as variaveis foram preenchidas
3. Nao use aspas:
   ```
   SIIM_USER=usuario@email.com
   ```

### "Timeout: navegacao levou muito tempo"

**Causa**: Conexao de internet lenta ou servidor SIIM lento.

**Solucao**:
1. Verifique sua conexao com a internet
2. Tente novamente em outro momento

### "Erro de login: credenciais invalidas"

**Causa**: Usuario ou senha incorretos, ou conta bloqueada.

**Solucao**:
1. Verifique suas credenciais no arquivo `.env`
2. Tente fazer login manualmente no site SIIM
3. Se a conta estiver bloqueada, entre em contato com o suporte SIIM

### "Arquivo .env nao encontrado"

**Causa**: O arquivo foi salvo com extensao diferente.

**Solucao**:
1. Abra Explorador de Arquivos
2. Clique em "Exibir" > "Extensoes de nomes de arquivo"
3. Verifique se o arquivo e `.env` (nao `.env.txt`)
4. Renomeie se necessario

### "PowerShell nao executa scripts"

**Causa**: "execution policy" bloqueia scripts.

**Solucao**:
1. Abra PowerShell como Administrador
2. Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Digite `Y` e pressione Enter
4. Tente novamente

### "Pasta .venv nao encontrada"

**Causa**: O ambiente virtual nao foi criado.

**Solucao**:
1. Verifique se esta na pasta `siim_automation`
2. Crie novamente: `python -m venv .venv`

---

## Dicas e Truques

### Executar novamente

```bash
cd C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation
.venv\Scripts\activate
python siim_download_projetos.py
```

### Ver navegador em acao

Para ver o navegador funcionando em tempo real, configure no `.env`:

```env
HEADLESS=false
```

Para rodar sem janela do navegador:

```env
HEADLESS=true
```

### Modificar projetos a baixar

Edite a lista de projetos no `.env`:

```env
PROJECTS=SAEPRO2025/6485,SAEPRO2025/6900,SAEPRO2025/7000
```

Separe os projetos com virgulas, sem espacos.

### Desativar ambiente virtual

```bash
deactivate
```

---

## Suporte Adicional

Se encontrar problemas nao cobertos aqui:

1. **Verifique o arquivo de log** da execucao do script
2. **Consulte a documentacao original**: Leia o arquivo `README.md`
3. **Entre em contato com suporte SIIM** se o problema for com credenciais ou acesso
4. **Verifique sua conexao de internet** e tente novamente

---

## Resumo Rapido (Cheat Sheet)

### Primeira vez:

```bash
# 1. Clonar
git clone https://github.com/marcocslima/coletor_SAEPRO.git
cd coletor_SAEPRO/siim_automation

# 2. Criar ambiente virtual
python -m venv .venv

# 3. Ativar (CMD)
.venv\Scripts\activate

# 3. Ativar (PowerShell)
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Instalar navegadores
playwright install chromium

# 6. Copiar e editar .env
copy .env.example .env
# Edite com suas credenciais

# 7. Executar
python siim_download_projetos.py
```

### Proximas vezes:

```bash
cd C:\Users\SeuUsuario\coletor_SAEPRO\siim_automation
.venv\Scripts\activate
python siim_download_projetos.py
```

---

## Historico de Versoes

- **v1.2** (Junho 2026): Adicionada integracao com Google Sheets (`sheet_reader.py`)
- **v1.1** (Junho 2026): Guia atualizado para GitHub, requirements.txt, nome do venv padrao `.venv`
- **v1.0** (Junho 2026): Guia inicial para Windows 11

---

**Ultima atualizacao**: Junho 2026
**Sistema**: Windows 11
**Python**: 3.9 ou superior

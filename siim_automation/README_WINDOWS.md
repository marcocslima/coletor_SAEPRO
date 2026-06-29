# 📘 Guia Completo: Automação SIIM no Windows 11

Este guia fornece instruções passo a passo para executar o script de automação SIIM no Windows 11. O script baixa automaticamente PDFs de projetos SAEPRO do sistema SIIM.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação do Python](#instalação-do-python)
3. [Download do Projeto](#download-do-projeto)
4. [Abrir Terminal](#abrir-terminal)
5. [Criar Ambiente Virtual](#criar-ambiente-virtual)
6. [Instalar Dependências](#instalar-dependências)
7. [Instalar Navegadores Playwright](#instalar-navegadores-playwright)
8. [Configurar Arquivo .env](#configurar-arquivo-env)
9. [Executar o Script](#executar-o-script)
10. [Localizar PDFs Baixados](#localizar-pdfs-baixados)
11. [Solução de Problemas](#solução-de-problemas)

---

## ✅ Pré-requisitos

Antes de começar, você precisa de:

- **Windows 11** instalado
- **Conexão com a internet** ativa
- **Credenciais SIIM** válidas (usuário e senha)
- ~500 MB de espaço livre em disco

---

## 🐍 Instalação do Python

### Passo 1: Verificar se Python já está instalado

Abra o **Prompt de Comando** (CMD) ou **PowerShell**:

1. Pressione `Windows + R`
2. Digite `cmd` e pressione Enter

Na janela que abrir, digite:

```bash
python --version
```

Se você ver uma versão como `Python 3.9.x` ou superior, **pule para a próxima seção**. Caso contrário, continue abaixo.

### Passo 2: Baixar Python

1. Acesse [python.org](https://www.python.org/downloads/windows/)
2. Clique em **"Download Python 3.11"** (ou versão mais recente)
3. Escolha o instalador **"Windows installer (64-bit)"** para Windows 11

### Passo 3: Instalar Python

1. Abra o arquivo `python-3.11.x-amd64.exe` que você baixou
2. **IMPORTANTE**: Marque a caixa "✓ Add Python to PATH"
3. Clique em "Install Now"
4. Aguarde até que a instalação seja concluída
5. Clique em "Disable path length limit" (opcional, mas recomendado)
6. Clique em "Close"

### Passo 4: Verificar instalação

Abra um novo Prompt de Comando e execute:

```bash
python --version
pip --version
```

Se você vir números de versão para ambos, está pronto! ✅

---

## 📥 Download do Projeto

### Opção A: Usando a interface Abacus.AI (Recomendado)

1. Clique no botão **"Files"** no canto superior direito da interface
2. Procure pela pasta `siim_automation`
3. Selecione todos os arquivos:
   - `siim_download_projetos.py`
   - `.env.example`
   - `README.md`
   - `README_WINDOWS.md`
4. Clique em "Download" ou selecione os arquivos e compacte em ZIP
5. Extraia os arquivos em uma pasta no seu computador, por exemplo:
   ```
   C:\Users\SeuUsuario\siim_automation\
   ```

### Opção B: Download Manual

Se precisar baixar manualmente:

1. Crie uma pasta em seu computador:
   ```
   C:\Users\SeuUsuario\siim_automation
   ```
2. Copie os arquivos nesta pasta

---

## 🖥️ Abrir Terminal

Para executar os comandos seguintes, você precisa abrir um terminal. Existem duas opções:

### Opção 1: Prompt de Comando (CMD)

1. Pressione `Windows + R`
2. Digite `cmd` e pressione Enter
3. Navegue até a pasta do projeto:
   ```bash
   cd C:\Users\SeuUsuario\siim_automation
   ```

### Opção 2: PowerShell (Recomendado)

1. Clique com botão direito na pasta `siim_automation`
2. Selecione "Abrir no PowerShell"
3. Se não vir esta opção, use:
   - Pressione `Windows + X`
   - Selecione "Terminal do Windows" ou "PowerShell"
   - Navegue com: `cd C:\Users\SeuUsuario\siim_automation`

### Opção 3: Windows Terminal (Moderno)

1. Abra a Microsoft Store
2. Procure por "Windows Terminal"
3. Clique em "Instalar"
4. Após instalar, abra-o e navegue até a pasta

---

## 🔧 Criar Ambiente Virtual

O ambiente virtual (venv) isola as dependências do projeto. Isso evita conflitos com outras instalações Python.

### Passo 1: Criar o ambiente virtual

No terminal (já na pasta `siim_automation`), execute:

```bash
python -m venv venv
```

Aguarde alguns segundos. Uma nova pasta chamada `venv` será criada.

### Passo 2: Ativar o ambiente virtual

**No Prompt de Comando (CMD):**
```bash
venv\Scripts\activate
```

**No PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

Se receber erro de "execution policy" no PowerShell, execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente:
```powershell
venv\Scripts\Activate.ps1
```

### Como saber se está ativado?

Se vir `(venv)` no início da linha do terminal, está ativado:

```
(venv) C:\Users\SeuUsuario\siim_automation>
```

✅ Perfeito! Agora você está pronto para instalar as dependências.

---

## 📦 Instalar Dependências

Com o ambiente virtual ativado, execute:

```bash
pip install playwright python-dotenv
```

Este comando instalará:
- **playwright**: Automação de navegador web
- **python-dotenv**: Carregamento de variáveis de ambiente

O processo pode levar alguns minutos. Aguarde até ver a mensagem de sucesso:

```
Successfully installed playwright python-dotenv
```

---

## 🌐 Instalar Navegadores Playwright

O Playwright precisa dos navegadores para funcionar. Execute:

```bash
playwright install chromium
```

Ou, se preferir instalar múltiplos navegadores:

```bash
playwright install
```

Isto baixará os navegadores necessários (~200-300 MB). **Este passo é obrigatório!**

---

## ⚙️ Configurar Arquivo .env

O arquivo `.env` contém suas credenciais SIIM e configurações.

### Passo 1: Copiar arquivo de exemplo

Na pasta `siim_automation`, copie o arquivo `.env.example`:

1. **Opção CMD/PowerShell:**
   ```bash
   copy .env.example .env
   ```

2. **Opção Manual:**
   - Clique com botão direito em `.env.example`
   - Selecione "Copiar"
   - Clique com botão direito na pasta vazia
   - Selecione "Colar"
   - Renomeie para `.env`

### Passo 2: Preencher credenciais

Abra o arquivo `.env` com um editor de texto (Bloco de Notas ou VS Code):

```env
SIIM_URL=https://siim21.cijun.sp.gov.br/CA
SIIM_ORGAO=PREFEITURA DO MUNICÍPIO DE JUNDIAÍ
SIIM_USER=seu_usuario@jundiai.sp.gov.br
SIIM_PASSWORD=sua_senha_aqui
DOWNLOAD_DIR=C:\Users\SeuUsuario\Downloads
HEADLESS=false
PROJECTS=SAEPRO2025/6485,SAEPRO2025/6865,SAEPRO2025/6884
```

**Substitua pelos seus valores:**

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `SIIM_URL` | URL do SIIM | Geralmente não muda |
| `SIIM_ORGAO` | Seu órgão | PREFEITURA DO MUNICÍPIO DE JUNDIAÍ |
| `SIIM_USER` | Seu email/usuário | seu_usuario@jundiai.sp.gov.br |
| `SIIM_PASSWORD` | Sua senha SIIM | Sua_Senha_123! |
| `DOWNLOAD_DIR` | Onde salvar PDFs | C:\Users\SeuUsuario\Downloads |
| `HEADLESS` | Mostrar navegador? | false (true para rodar silenciosamente) |
| `PROJECTS` | Projetos a baixar | SAEPRO2025/6485,SAEPRO2025/6865 |

### Passo 3: Salvar o arquivo

Após editar, salve o arquivo (Ctrl + S).

⚠️ **SEGURANÇA**: O arquivo `.env` contém suas credenciais. **Nunca o compartilhe ou envie para repositórios públicos!**

---

## ▶️ Executar o Script

Com o ambiente virtual ativado e o arquivo `.env` configurado, execute:

```bash
python siim_download_projetos.py
```

### O que esperar:

1. **Janela do navegador abrirá** (a menos que `HEADLESS=true`)
2. **Faça login automaticamente** no SIIM
3. **Navega para os projetos** configurados
4. **Downloads começam** dos PDFs

### Indicadores de sucesso:

```
✅ Login realizado com sucesso!
✅ Navegando para projetos...
✅ Baixando projeto SAEPRO2025/6485...
✅ PDF salvo em: C:\Users\SeuUsuario\Downloads\projeto_6485.pdf
```

---

## 📁 Localizar PDFs Baixados

Os PDFs são salvos na pasta configurada em `DOWNLOAD_DIR` no arquivo `.env`.

### Padrão padrão:

Se você usou a configuração padrão:

```
C:\Users\SeuUsuario\Downloads\
```

### Como abrir:

1. Abra o **Explorador de Arquivos** (Windows + E)
2. Navegue até a pasta `Downloads`
3. Procure por arquivos `.pdf` com nomes de projetos

### Exemplo de estrutura:

```
C:\Users\SeuUsuario\Downloads\
├── SAEPRO2025_6485.pdf
├── SAEPRO2025_6865.pdf
└── SAEPRO2025_6884.pdf
```

---

## 🔧 Solução de Problemas

### ❌ "Python não é reconhecido como comando"

**Causa**: Python não foi adicionado ao PATH durante a instalação.

**Solução**:
1. Desinstale Python
2. Reinstale marcando **✓ Add Python to PATH**
3. Reinicie o computador

### ❌ "ModuleNotFoundError: No module named 'playwright'"

**Causa**: Dependências não foram instaladas corretamente.

**Solução**:
1. Ative o ambiente virtual: `venv\Scripts\activate`
2. Reinstale: `pip install --upgrade playwright python-dotenv`
3. Verifique: `pip list` (deve mostrar ambos os pacotes)

### ❌ "Erro ao instalar Playwright browsers"

**Causa**: Problemas de permissão ou espaço em disco.

**Solução**:
1. Execute como Administrador:
   - Clique com botão direito no Prompt de Comando
   - Selecione "Executar como administrador"
   - Ative o venv e tente novamente:
     ```bash
     playwright install chromium
     ```

2. Libere espaço em disco e tente novamente

### ❌ "SIIM_USER ou SIIM_PASSWORD não fornecidos"

**Causa**: O arquivo `.env` não foi configurado corretamente.

**Solução**:
1. Verifique se o arquivo `.env` existe (não é `.env.example`)
2. Abra e verifique se todas as variáveis foram preenchidas
3. Não use aspas desnecessárias:
   ```
   ✅ SIIM_USER=usuario@email.com
   ❌ SIIM_USER="usuario@email.com"
   ```

### ❌ "Timeout: navegação levou muito tempo"

**Causa**: Conexão de internet lenta ou servidor SIIM lento.

**Solução**:
1. Verifique sua conexão com a internet
2. Tente novamente em outro momento
3. Aumente o timeout modificando o script (requer conhecimento Python)

### ❌ "Erro de login: credenciais inválidas"

**Causa**: Usuário ou senha incorretos, ou conta bloqueada.

**Solução**:
1. Verifique suas credenciais no arquivo `.env`
2. Tente fazer login manualmente no site SIIM: [siim21.cijun.sp.gov.br](https://siim21.cijun.sp.gov.br)
3. Se a conta estiver bloqueada, entre em contato com o suporte SIIM

### ❌ "Arquivo .env não encontrado"

**Causa**: O arquivo foi salvo com extensão diferente.

**Solução**:
1. Abra Explorador de Arquivos
2. Clique em "Exibir" → "Extensões de nomes de arquivo"
3. Verifique se o arquivo é `.env` (não `.env.txt`)
4. Renomeie se necessário: clique direito → Renomear

### ❌ "PowerShell não executa scripts"

**Erro típico**: "não pode ser carregado porque a execução de scripts está desabilitada"

**Solução**:
1. Abra PowerShell como Administrador
2. Execute:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Digite `Y` e pressione Enter
4. Tente novamente

### ❌ "Pasta venv não encontrada"

**Causa**: O ambiente virtual não foi criado.

**Solução**:
1. Verifique se está na pasta `siim_automation`:
   ```bash
   cd C:\Users\SeuUsuario\siim_automation
   ```
2. Crie novamente:
   ```bash
   python -m venv venv
   ```

---

## 💡 Dicas e Truques

### Executar novamente

Para rodar o script novamente:

1. Abra terminal na pasta do projeto
2. Ative o venv:
   ```bash
   venv\Scripts\activate
   ```
3. Execute:
   ```bash
   python siim_download_projetos.py
   ```

### Ver navegador em ação

Para ver o navegador funcionando em tempo real, configure no `.env`:

```env
HEADLESS=false
```

Se quiser que rode sem a janela do navegador:

```env
HEADLESS=true
```

### Modificar projetos a baixar

Edite a lista de projetos no `.env`:

```env
PROJECTS=SAEPRO2025/6485,SAEPRO2025/6900,SAEPRO2025/7000
```

Separe os projetos com vírgulas, sem espaços.

### Desativar ambiente virtual

Quando terminar, para sair do ambiente virtual:

```bash
deactivate
```

---

## 🆘 Suporte Adicional

Se encontrar problemas não cobertos aqui:

1. **Verifique o arquivo de log** da execução do script
2. **Consulte a documentação original**: Leia o arquivo `README.md`
3. **Entre em contato com suporte SIIM** se o problema for com credenciais ou acesso
4. **Verifique sua conexão de internet** e tente novamente

---

## ✨ Resumo Rápido (Cheat Sheet)

### Primeira vez:

```bash
# 1. Navegar até a pasta
cd C:\Users\SeuUsuario\siim_automation

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar (CMD)
venv\Scripts\activate

# 3. Ativar (PowerShell)
venv\Scripts\Activate.ps1

# 4. Instalar dependências
pip install playwright python-dotenv

# 5. Instalar navegadores
playwright install chromium

# 6. Copiar e editar .env
copy .env.example .env
# ← Edite com suas credenciais

# 7. Executar
python siim_download_projetos.py
```

### Próximas vezes:

```bash
# Apenas ativar e executar
cd C:\Users\SeuUsuario\siim_automation
venv\Scripts\activate
python siim_download_projetos.py
```

---

## 📝 Histórico de Versões

- **v1.0** (Junho 2026): Guia inicial para Windows 11
- Atualizado com instruções detalhadas para Python 3.11+
- Adicionadas soluções de problemas comuns

---

**Última atualização**: Junho 2026
**Sistema**: Windows 11
**Python**: 3.9 ou superior

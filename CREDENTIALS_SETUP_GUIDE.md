# 🔐 Guia Completo de Configuração de Credenciais

**Última Atualização**: 2025-11-22
**Status**: Em migração para Namastex OAuth Server (Gatekeeper)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Namastex OAuth Server](#1-namastex-oauth-server-gatekeeper) ⭐ Nova Arquitetura
3. [Google Workspace Tools](#2-google-workspace-tools) (9 ferramentas individuais + 1 unificada)
4. [Genie Omni](#3-genie-omni-22) - WhatsApp Agent-First
5. [Omni](#4-omni-23) - Multi-tenant Messaging
6. [Wait](#5-wait-24) - Utilidade
7. [Gemini Assistant](#6-gemini-assistant-25) - AI Consultation

---

## Visão Geral

### 🏗️ Arquitetura OAuth em Migração

Estamos migrando de autenticação individual por ferramenta para um **OAuth Server centralizado (Gatekeeper)**:

```
┌─────────────────────────────────────────────────────────────┐
│          NAMASTEX OAUTH SERVER (Gatekeeper)                  │
│              Port 11000 - OAuth Centralized                  │
├─────────────────────────────────────────────────────────────┤
│  • Gerencia TODAS as autenticações OAuth                    │
│  • Curadoria de credenciais                                 │
│  • Single Sign-On para todas as tools                       │
│  • Comportamento padrão das ferramentas Namastex            │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌─────────────────┐      ┌──────────────────┐
    │ Google Tools    │      │  Future Tools    │
    │ (10 ferramentas)│      │  (WhatsApp, etc) │
    └─────────────────┘      └──────────────────┘
```

### Status da Migração

- ✅ **Namastex OAuth Server**: Em desenvolvimento (port 11000)
- ⚙️ **Google Calendar Test**: Ferramenta de teste da nova arquitetura (port 11001)
- 📋 **Google Workspace Tools**: Ainda usando autenticação individual (migração planejada)
- 🎯 **Objetivo**: Todas as ferramentas passarão pelo Gatekeeper

---

## 1. Namastex OAuth Server (Gatekeeper)

**Port**: 11000
**Status**: 🆕 Em desenvolvimento (untracked no git)
**Propósito**: Centralizador OAuth para TODAS as ferramentas Namastex

### Como Funciona

O Namastex OAuth Server será o **ponto único de autenticação** para:
1. Google Workspace (Calendar, Gmail, Drive, Docs, Sheets, Slides, Forms, Tasks, Chat)
2. Futuras integrações WhatsApp
3. Qualquer serviço que precise de OAuth

### Configuração

```bash
# .env
OAUTH_SERVER_PORT=11000
OAUTH_CREDENTIALS_DIR=~/.credentials  # Ou caminho personalizado
```

### PM2 Configuration

```javascript
{
  name: 'oauth',
  script: 'uv',
  args: 'run python -m automagik_tools.tools.namastex_oauth_server --transport sse --host 0.0.0.0 --port 11000',
  env: {
    OAUTH_SERVER_PORT: '11000',
    OAUTH_CREDENTIALS_DIR: process.env.OAUTH_CREDENTIALS_DIR || '~/.credentials',
  }
}
```

### Fluxo de Autenticação Planejado

1. **Tool solicita autenticação** → Redireciona para OAuth Server
2. **OAuth Server valida** → Curadoria de credenciais
3. **Credenciais aprovadas** → Token retornado para a tool
4. **Tool opera** → Com credenciais gerenciadas pelo Gatekeeper

### Status Atual

- 🔴 **Código não acessível** (untracked no git)
- ⚙️ **Em desenvolvimento ativo**
- 🎯 **Próximo passo**: Finalizar implementação e fazer login test

---

## 2. Google Workspace Tools

### 2.1 Google Calendar Test (Port 11001)

**Status**: 🆕 Ferramenta de teste da migração OAuth
**Propósito**: Validar a nova arquitetura OAuth com Namastex OAuth Server

```bash
# .env (em migração para OAuth Server)
# Configuração atual (será migrada)
GOOGLE_MCP_CREDENTIALS_DIR=~/.credentials
```

### 2.2 Google Workspace Individual Tools (Ports 11002-11010)

Todas as 9 ferramentas Google usam a MESMA configuração:

| Tool | Port | Função |
|------|------|--------|
| google-calendar | 11002 | Gerenciar calendários e eventos |
| google-gmail | 11003 | Ler/enviar emails, labels, threads |
| google-drive | 11004 | Upload/download arquivos, pastas |
| google-docs | 11005 | Criar/editar documentos Google Docs |
| google-sheets | 11006 | Planilhas e fórmulas |
| google-slides | 11007 | Apresentações |
| google-forms | 11008 | Formulários e respostas |
| google-tasks | 11009 | Listas de tarefas |
| google-chat | 11010 | Mensagens Google Chat |

#### Configuração Compartilhada

```bash
# .env
GOOGLE_MCP_CREDENTIALS_DIR=~/.credentials

# Opcional: OAuth direto (método antigo, será deprecado)
GOOGLE_WORKSPACE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_WORKSPACE_CLIENT_SECRET=your-client-secret
```

### 2.3 Google Workspace Unified (Port 11011)

**Ferramenta COMPLETA** - Todas as funcionalidades Google em uma única tool.

```bash
# .env
GOOGLE_WORKSPACE_CREDENTIALS_DIR=~/.google_workspace_mcp/credentials  # Default
GOOGLE_WORKSPACE_TOOL_TIER=complete  # Opções: core, extended, complete
GOOGLE_WORKSPACE_USER_EMAIL=seu-email@gmail.com  # Modo single-user

# OAuth 2.1 (modo avançado)
GOOGLE_WORKSPACE_ENABLE_OAUTH21=false
GOOGLE_WORKSPACE_SINGLE_USER_MODE=true
GOOGLE_WORKSPACE_STATELESS_MODE=false

# Servidor (se usar HTTP transport)
GOOGLE_WORKSPACE_BASE_URI=http://localhost
GOOGLE_WORKSPACE_PORT=11011
GOOGLE_WORKSPACE_LOG_LEVEL=INFO
```

### Como Fazer Login - Google Tools

#### Método Atual (Antes do OAuth Server)

1. **Criar projeto Google Cloud**:
   - Vá em https://console.cloud.google.com
   - Crie novo projeto ou use existente
   - Ative as APIs necessárias

2. **Ativar APIs Google** (para cada ferramenta):
   ```
   Gmail Tool         → Gmail API
   Calendar Tool      → Google Calendar API
   Drive Tool         → Google Drive API
   Docs Tool          → Google Docs API
   Sheets Tool        → Google Sheets API
   Slides Tool        → Google Slides API
   Forms Tool         → Google Forms API
   Tasks Tool         → Google Tasks API
   Chat Tool          → Google Chat API
   ```

3. **Criar OAuth 2.0 Credentials**:
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Application type: **Desktop app**
   - Download JSON (client_secret.json)

4. **Configurar .env**:
   ```bash
   GOOGLE_MCP_CREDENTIALS_DIR=~/.credentials
   ```

5. **Primeiro uso** (cada ferramenta):
   ```bash
   # A ferramenta vai abrir o navegador automaticamente
   # Login com sua conta Google
   # Aceitar permissões
   # Token salvo em ~/.credentials/
   ```

#### Método Futuro (Com OAuth Server)

1. **OAuth Server centraliza tudo**
2. **Login único** para todas as ferramentas Google
3. **Curadoria automática** de credenciais
4. **Renovação automática** de tokens

---

## 3. Genie Omni (#22)

**Port**: 11012
**Tipo**: WhatsApp Agent-First Communication
**Framework**: Agent-owned ou Act-on-behalf

### Como Funciona

Genie Omni é uma interface **human-like** para WhatsApp com **context isolation** (modo seguro).

**Modos de Operação**:

1. **Agent Owned** (recomendado):
   - Agent tem seu próprio número WhatsApp
   - Comunicação natural com humanos
   - Contexto isolado para segurança

2. **Act On Behalf**:
   - Agent usa número do dono
   - Requer permissão explícita
   - Contexto isolado OBRIGATÓRIO

### Configuração Completa

```bash
# .env

# === CREDENCIAIS OBRIGATÓRIAS ===
OMNI_API_KEY=sua-api-key-aqui              # API key do Omni Hub
OMNI_BASE_URL=http://localhost:8882        # URL do servidor Omni

# === CONTEXT ISOLATION (SEGURANÇA) ===
# ESCOLHA UMA OPÇÃO (altamente recomendado):

# Opção 1: Isolar para um número específico
OMNI_MASTER_PHONE=5511999999999            # Seu número (contexto isolado)

# OU

# Opção 2: Isolar para um grupo específico
OMNI_MASTER_GROUP=120363xxx@g.us           # ID do grupo (contexto isolado)

# ⚠️ SEM MASTER CONTEXT = MODO PERIGOSO
# Agent pode enviar mensagens para QUALQUER PESSOA
# Configure master_phone OU master_group para segurança

# === MODO DE OPERAÇÃO ===
OMNI_MODE=agent_owned                      # Opções: agent_owned, act_on_behalf

# === CONFIGURAÇÕES OPCIONAIS ===
OMNI_DEFAULT_INSTANCE=genie                # Nome da instância padrão
OMNI_TIMEOUT=30                            # Timeout em segundos
OMNI_MAX_RETRIES=3                         # Máximo de tentativas
OMNI_MEDIA_DOWNLOAD_FOLDER=/tmp/genie-omni-media  # Pasta para mídia
```

### Context Isolation - Como Funciona

```python
# SEM master context (PERIGOSO):
✅ Agent pode enviar para: QUALQUER NÚMERO
⚠️ RISCO: Agent autônomo sem restrições

# COM master_phone (SEGURO):
✅ Agent pode enviar para: 5511999999999
❌ Agent BLOQUEADO para: Qualquer outro número

# COM master_group (SEGURO):
✅ Agent pode enviar para: 120363xxx@g.us
❌ Agent BLOQUEADO para: Qualquer outro destino
```

### Como Obter as Credenciais

1. **Omni Hub API Key**:
   - Configure seu servidor Omni Hub
   - Gere API key no painel admin
   - URL padrão: `http://localhost:8882`

2. **Master Phone/Group** (para segurança):
   ```bash
   # Seu número WhatsApp (com DDI)
   OMNI_MASTER_PHONE=5511999999999

   # OU ID do grupo WhatsApp
   # Pegar do Evolution API ou Omni Hub
   OMNI_MASTER_GROUP=120363xxx@g.us
   ```

3. **Configurar instância WhatsApp**:
   - Usar Evolution API ou similar
   - Conectar número WhatsApp
   - Configurar webhook para Omni Hub

### PM2 Configuration

```javascript
{
  name: 'genie-omni',
  script: 'uv',
  args: 'run python -m automagik_tools.tools.genie_omni --transport sse --host 0.0.0.0 --port 11012',
  env: {
    OMNI_API_KEY: process.env.OMNI_API_KEY || '',
    OMNI_BASE_URL: process.env.OMNI_BASE_URL || 'http://localhost:8882',
    OMNI_MASTER_PHONE: process.env.OMNI_MASTER_PHONE || '',  // SEGURANÇA
    OMNI_MODE: 'agent_owned',
  }
}
```

### Features

- ✅ Leitura de mensagens WhatsApp
- ✅ Envio de mensagens (texto, mídia, áudio)
- ✅ Gestão de contatos
- ✅ Listagem de conversas
- ✅ Download de mídia
- ✅ Context isolation (segurança)
- ✅ Agent-first communication

---

## 4. Omni (#23)

**Port**: 11014
**Tipo**: Multi-tenant Messaging Platform
**Propósito**: Plataforma unificada para WhatsApp, Slack, Discord

### Como Funciona

Omni é uma plataforma **multi-tenant** que gerencia múltiplos canais de comunicação.

### Configuração

```bash
# .env

# === CREDENCIAIS OBRIGATÓRIAS ===
OMNI_API_KEY=sua-api-key-aqui              # API key do Omni
OMNI_BASE_URL=http://localhost:8882        # URL do servidor Omni

# === CONFIGURAÇÕES OPCIONAIS ===
OMNI_DEFAULT_INSTANCE=default              # Instância padrão
OMNI_TIMEOUT=30                            # Timeout em segundos
OMNI_MAX_RETRIES=3                         # Máximo de tentativas
```

### Diferença entre Omni e Genie-Omni

| Aspecto | Omni (#23) | Genie-Omni (#22) |
|---------|-----------|------------------|
| **Foco** | Multi-tenant platform | Agent-first WhatsApp |
| **Uso** | Múltiplas instâncias | Single agent communication |
| **Segurança** | Multi-tenant isolation | Context isolation |
| **Features** | Gestão completa | Communication natural |

### PM2 Configuration

```javascript
{
  name: 'omni',
  script: 'uv',
  args: 'run python -m automagik_tools.tools.omni --transport sse --host 0.0.0.0 --port 11014',
  env: {
    OMNI_BASE_URL: process.env.OMNI_BASE_URL || 'http://localhost:8080',
    OMNI_API_KEY: process.env.OMNI_API_KEY || '',
  }
}
```

---

## 5. Wait (#24)

**Port**: 11022
**Tipo**: Utility Tool
**Propósito**: Adicionar delays/waits em workflows

### Como Funciona

Ferramenta simples para adicionar delays em automações:
- Esperar X minutos/segundos
- Throttling de operações
- Rate limiting manual

### Configuração

```bash
# .env
# Nenhuma credencial necessária - ferramenta standalone
```

### PM2 Configuration

```javascript
{
  name: 'wait',
  script: 'uv',
  args: 'run python -m automagik_tools.tools.wait --transport sse --host 0.0.0.0 --port 11022',
  env: {},  // Sem credenciais
  max_memory_restart: '200M',  // Leve
}
```

### Uso

```javascript
// Exemplo de uso no MCP
{
  "tool": "wait",
  "duration": 300  // segundos
}
```

---

## 6. Gemini Assistant (#25)

**Port**: 11032
**Tipo**: AI Consultation Tool
**Propósito**: Consultas avançadas ao Google Gemini com sessões e anexos

### Como Funciona

**Features**:
1. ✅ **Session Management**: Múltiplas sessões simultâneas (max 10)
2. ✅ **File Attachments**: Upload de arquivos para contexto
3. ✅ **Multiple Models**: Suporte a vários modelos Gemini
4. ✅ **Configurável**: Temperature, tokens, timeout por sessão

**Tools Disponíveis**:
- `consult_gemini`: Fazer consulta ao Gemini
- `list_sessions`: Listar sessões ativas
- `end_session`: Encerrar sessão
- `get_gemini_requests`: Histórico de requests

### Configuração Completa

```bash
# .env

# === CREDENCIAL OBRIGATÓRIA ===
GEMINI_API_KEY=sua-gemini-api-key-aqui     # Google AI Studio

# === MODELO (OPCIONAL) ===
GEMINI_MODEL=gemini-2.0-flash-exp          # Default

# Modelos disponíveis:
# - gemini-2.5-pro                   (mais poderoso, mais lento)
# - gemini-2.0-flash-exp             (recomendado, balanceado)
# - gemini-2.0-flash-thinking-exp-1219  (reasoning)
# - gemini-1.5-flash                 (rápido)
# - gemini-1.5-flash-8b              (ultra rápido, mais leve)
# - gemini-1.5-pro                   (estável)
# - gemini-1.0-pro                   (legado)

# === CONFIGURAÇÕES DE SESSÃO (OPCIONAL) ===
GEMINI_SESSION_TIMEOUT=3600                # 1 hora (60-86400 segundos)
GEMINI_MAX_SESSIONS=10                     # Máximo de sessões simultâneas (1-100)

# === CONFIGURAÇÕES DE GERAÇÃO (OPCIONAL) ===
GEMINI_MAX_TOKENS=8192                     # Máximo de tokens por resposta (1-32768)
GEMINI_TEMPERATURE=0.7                     # Criatividade (0.0-2.0)
```

### Como Obter API Key

1. **Google AI Studio**:
   - Acesse: https://makersuite.google.com/app/apikey
   - Login com conta Google
   - "Create API Key"
   - Copie a chave gerada

2. **Configure .env**:
   ```bash
   GEMINI_API_KEY=AIzaSy...sua-chave-aqui
   ```

### PM2 Configuration

```javascript
{
  name: 'gemini-assistant',
  script: 'uv',
  args: 'run python -m automagik_tools.tools.gemini_assistant --transport sse --host 0.0.0.0 --port 11032',
  env: {
    GEMINI_API_KEY: process.env.GEMINI_API_KEY || '',
    GEMINI_MODEL: 'gemini-2.0-flash-exp',
    GEMINI_SESSION_TIMEOUT: '3600',
    GEMINI_MAX_SESSIONS: '10',
  }
}
```

### Limites e Quotas

**Free Tier (Google AI Studio)**:
- 15 requests/minuto
- 1,500 requests/dia
- Rate limit pode variar por modelo

**Paid Tier (Google Cloud)**:
- Quotas maiores
- Billing via Google Cloud Console
- Mais modelos disponíveis

---

## 🚀 Próximos Passos - Configuração Completa

### 1. Namastex OAuth Server (PRIORITÁRIO)

```bash
# 1. Finalizar implementação do OAuth Server
# 2. Testar com Google Calendar Test
cd /home/namastex/workspace/automagik-tools

# 3. Iniciar OAuth Server
pm2 start ecosystem.config.cjs --only oauth

# 4. Verificar logs
pm2 logs oauth

# 5. Fazer primeiro login (quando pronto)
# OAuth Server vai abrir navegador para autenticação
```

### 2. Google Tools - Login Individual (Temporário)

Até migração para OAuth Server estar completa:

```bash
# Para cada ferramenta Google:

# 1. Ativar API no Google Cloud Console
# 2. Criar OAuth 2.0 credentials (Desktop app)
# 3. Download client_secret.json
# 4. Configurar GOOGLE_MCP_CREDENTIALS_DIR
# 5. Iniciar ferramenta (primeira vez abre navegador)
# 6. Fazer login e aceitar permissões
# 7. Token salvo automaticamente

# Exemplo: Google Calendar
pm2 start ecosystem.config.cjs --only google-calendar
pm2 logs google-calendar  # Ver URL de autenticação
```

### 3. Genie Omni - Setup WhatsApp

```bash
# 1. Configurar Omni Hub
# 2. Conectar instância WhatsApp
# 3. Obter API key
# 4. Configurar master_phone/master_group (SEGURANÇA)

# .env
OMNI_API_KEY=sua-chave
OMNI_MASTER_PHONE=5511999999999  # SEU NÚMERO

# Iniciar
pm2 start ecosystem.config.cjs --only genie-omni
pm2 logs genie-omni
```

### 4. Gemini Assistant - Google AI

```bash
# 1. Obter API key do Google AI Studio
# https://makersuite.google.com/app/apikey

# .env
GEMINI_API_KEY=AIzaSy...

# Iniciar
pm2 start ecosystem.config.cjs --only gemini-assistant
pm2 logs gemini-assistant
```

### 5. Validação Completa

```bash
# Iniciar TODAS as ferramentas
pm2 start ecosystem.config.cjs

# Verificar status
pm2 status

# Verificar logs
pm2 logs

# Monitor em tempo real
pm2 monit
```

---

## 🔒 Segurança e Best Practices

### Variáveis de Ambiente

```bash
# NUNCA commitar .env
# SEMPRE usar .env.example como template
# SEMPRE usar environment variables em produção

# Exemplo .env.example:
GEMINI_API_KEY=your-key-here
GOOGLE_MCP_CREDENTIALS_DIR=~/.credentials
OMNI_API_KEY=your-key-here
OMNI_MASTER_PHONE=5511999999999  # IMPORTANTE: Context isolation
```

### Credentials Storage

```bash
# Google Tools
~/.credentials/
  ├── token_user@gmail.com.json
  ├── client_secret.json
  └── ...

# OAuth Server (futuro)
~/.credentials/
  ├── oauth_server_tokens/
  │   ├── user1@gmail.com/
  │   └── user2@gmail.com/
  └── ...
```

### Context Isolation (Genie Omni)

```bash
# SEMPRE configurar master context em produção
# NUNCA rodar sem master_phone/master_group em produção
# TESTAR primeiro com master_phone configurado

# Produção (SEGURO):
OMNI_MASTER_PHONE=5511999999999

# Development (PERIGOSO - apenas local):
# Sem master context
```

---

## 📊 Checklist de Configuração

### Google Tools ✅

- [ ] Projeto Google Cloud criado
- [ ] APIs ativadas (Calendar, Gmail, Drive, Docs, Sheets, Slides, Forms, Tasks, Chat)
- [ ] OAuth 2.0 credentials criadas (Desktop app)
- [ ] client_secret.json baixado
- [ ] `GOOGLE_MCP_CREDENTIALS_DIR` configurado
- [ ] Primeiro login feito (token salvo)
- [ ] Testar cada ferramenta individualmente

### Genie Omni ✅

- [ ] Omni Hub rodando
- [ ] Instância WhatsApp conectada
- [ ] `OMNI_API_KEY` obtida
- [ ] `OMNI_BASE_URL` configurado
- [ ] `OMNI_MASTER_PHONE` ou `OMNI_MASTER_GROUP` configurado (SEGURANÇA)
- [ ] Testar envio de mensagem
- [ ] Verificar context isolation funcionando

### Gemini Assistant ✅

- [ ] Google AI Studio account criado
- [ ] `GEMINI_API_KEY` obtida
- [ ] Modelo configurado (default OK)
- [ ] Testar consulta simples
- [ ] Testar session management
- [ ] Verificar quotas/limites

### Namastex OAuth Server ✅

- [ ] Código finalizado (untracked → tracked)
- [ ] Configuração de credenciais definida
- [ ] Testar com Google Calendar Test
- [ ] Migração das Google Tools planejada
- [ ] Documentação de integração criada

---

## 🆘 Troubleshooting

### Google Tools - "Credenciais inválidas"

```bash
# 1. Verificar se APIs estão ativadas
# 2. Recriar OAuth credentials
# 3. Deletar tokens antigos
rm -rf ~/.credentials/*
# 4. Refazer login
```

### Genie Omni - "Context isolation bloqueando"

```bash
# Verificar configuração
echo $OMNI_MASTER_PHONE

# Se vazio, configurar:
export OMNI_MASTER_PHONE=5511999999999

# Ou desabilitar temporariamente (APENAS DEV):
unset OMNI_MASTER_PHONE
unset OMNI_MASTER_GROUP
```

### Gemini - "Rate limit exceeded"

```bash
# Free tier: 15 req/min
# Esperar 1 minuto
# Ou upgrade para paid tier
```

---

**Dúvidas?** Consulte a documentação individual de cada ferramenta ou peça ajuda!

**Status**: ✅ Guia completo criado
**Próximo**: Testar login em cada ferramenta e documentar issues

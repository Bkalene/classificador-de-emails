# 📧 Email Agent — Guia de Configuração

Agente local que lê seu Gmail, classifica e-mails com Gemini e age somente após sua aprovação.

---

## Pré-requisitos

- Python 3.11+
- Conta Gmail
- [Gemini API Key](https://aistudio.google.com) (já configurada no `.env`)

---

## Passo 1 — Instalar dependências

```powershell
cd D:\Organizador\email-agent
pip install -r requirements.txt
```

---

## Passo 2 — Configurar Gmail API (faça 1 vez)

### 2.1 — Criar projeto no Google Cloud Console

1. Acesse: https://console.cloud.google.com
2. Clique em **"Novo Projeto"** → dê o nome `email-agent`
3. No menu lateral → **APIs e Serviços** → **Biblioteca**
4. Pesquise **"Gmail API"** → clique → **Ativar**

### 2.2 — Criar credenciais OAuth2

1. Vá em **APIs e Serviços** → **Credenciais**
2. Clique em **+ Criar Credenciais** → **ID do cliente OAuth**
3. Tipo de aplicativo: **Aplicativo para computador**
4. Nome: `email-agent-local`
5. Clique em **Criar** → **Baixar JSON**
6. Renomeie o arquivo para `credentials.json`
7. Coloque em: `D:\Organizador\email-agent\credentials.json`

### 2.3 — Configurar Tela de Consentimento (se necessário)

1. Vá em **APIs e Serviços** → **Tela de consentimento OAuth**
2. Tipo de usuário: **Externo** → **Criar**
3. Preencha nome do app e e-mail
4. Em **Escopos**, adicione: `gmail.readonly` e `gmail.modify`
5. Em **Usuários de teste**, adicione seu e-mail Gmail

### 2.4 — Autenticar (abre o browser uma vez)

```powershell
python auth.py
```

> Isso abre o browser, você faz login no Gmail e autoriza. O arquivo `token.json` é gerado automaticamente.

---

## Passo 3 — Testar componentes

```powershell
# Testar classificador Gemini
python classifier.py

# Testar busca de e-mails
python fetcher.py

# Testar geração de relatório
python summarizer.py
```

---

## Passo 4 — Executar o agente

```powershell
python main.py
```

### O que acontece:
1. 📬 Busca e-mails das últimas 24h
2. 🤖 Classifica cada um com Gemini
3. 📄 Gera `daily_report.md`
4. ✋ Exibe tabela e aguarda sua aprovação
5. ✅ Após `s` + Enter → move e-mails no Gmail

### Comandos na tela de aprovação:
| Comando            | Ação                               |
|--------------------|------------------------------------|
| `s`                | Aprovar tudo e executar            |
| `n`                | Cancelar (nada é feito)            |
| `e 3 IMPORTANTE`   | Muda e-mail #3 para IMPORTANTE     |
| `v 2`              | Ver detalhes do e-mail #2          |
| `?`                | Ajuda                              |

---

## Passo 5 — Agendar execução diária (Windows)

Executar o script de agendamento:

```powershell
python schedule_task.py
```

> Isso cria uma tarefa no Windows Task Scheduler para rodar às **8h todo dia**.

---

## Labels criadas no Gmail

O agente cria automaticamente:
- `AgentEmail/Urgente`
- `AgentEmail/Importante`
- `AgentEmail/Informativo`
- E-mails LIXO → Lixeira do Gmail

---

## Arquivos do projeto

| Arquivo | Função |
|---------|--------|
| `main.py` | Ponto de entrada |
| `auth.py` | Autenticação Gmail |
| `fetcher.py` | Busca e-mails |
| `classifier.py` | Classifica com Gemini |
| `summarizer.py` | Gera relatório |
| `approval.py` | Interface de aprovação |
| `executor.py` | Aplica ações no Gmail |
| `memory.py` | Aprende com feedback |
| `.env` | Sua Gemini API Key |
| `credentials.json` | Credenciais Gmail (você baixa) |
| `token.json` | Token OAuth (gerado automaticamente) |
| `daily_report.md` | Relatório do dia |
| `memory.jsonl` | Histórico de preferências |

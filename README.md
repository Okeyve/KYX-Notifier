# 🎵 TikTok → Discord Bot (GitHub Actions)

Notifica automaticamente novos vídeos de perfis do TikTok em um canal do Discord, rodando de graça via GitHub Actions a cada 30 minutos.

---

## 📁 Estrutura

```
.
├── bot.py                          # Script principal
├── requirements.txt                # Dependências Python
├── seen_videos.json                # Estado (criado automaticamente)
└── .github/
    └── workflows/
        └── tiktok_notify.yml       # Workflow do GitHub Actions
```

---

## 🚀 Setup passo a passo

### 1. Criar o repositório

Crie um repositório **privado** no GitHub e suba todos os arquivos.

### 2. Criar o Webhook no Discord

1. Vá ao canal do Discord onde quer receber as notificações
2. **Configurações do canal → Integrações → Webhooks → Novo Webhook**
3. Dê um nome (ex: `TikTok Bot`) e copie a URL do webhook

### 3. Configurar os Secrets no GitHub

Vá em **Settings → Secrets and variables → Actions → New repository secret** e adicione:

| Secret | Valor |
|---|---|
| `DISCORD_WEBHOOK_URL` | A URL do webhook copiada acima |
| `TIKTOK_USERNAMES` | Usuários separados por vírgula, ex: `khaby.lame,charlidamelio` |

> ⚠️ **Não coloque `@` nos nomes de usuário**, apenas o handle puro.

### 4. Dar permissão de escrita ao Actions

Vá em **Settings → Actions → General → Workflow permissions** e selecione **Read and write permissions**.

### 5. Ativar o workflow

Vá na aba **Actions** do repositório e ative os workflows se solicitado.  
Para testar imediatamente, clique em **Run workflow** no workflow `TikTok → Discord Notifier`.

---

## ⚙️ Personalização

| O que mudar | Onde |
|---|---|
| Frequência de verificação | `cron` no arquivo `.github/workflows/tiktok_notify.yml` |
| Cor do embed no Discord | Variável `color` em `bot.py` (formato hexadecimal) |
| Quantidade de vídeos verificados | Parâmetro `[:10]` em `fetch_latest_videos` em `bot.py` |

### Exemplos de cron

```
*/15 * * * *   → a cada 15 minutos
*/30 * * * *   → a cada 30 minutos (padrão)
0 * * * *      → a cada hora
```

---

## 🔧 Como funciona

1. O GitHub Actions roda o `bot.py` a cada 30 minutos
2. O script acessa a página pública de cada perfil do TikTok
3. Extrai os vídeos mais recentes do JSON de hidratação embutido na página
4. Compara com o arquivo `seen_videos.json` (estado persistido via cache + commit)
5. Para cada vídeo novo, envia um embed formatado para o Discord via webhook
6. Salva o novo estado para a próxima execução

---

## ⚠️ Avisos

- O TikTok pode mudar a estrutura HTML/JSON a qualquer momento, o que pode quebrar o scraping.
- Perfis privados **não** funcionam.
- O GitHub Actions tem um limite de ~2.000 minutos/mês gratuitos — com execuções a cada 30 min isso dá ~1.440 min/mês, dentro do limite.

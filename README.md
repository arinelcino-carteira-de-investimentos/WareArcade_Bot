# 🎮 WareArcadeBot - Ware Arcade Game
## Com SQLite + PIX Automático (Mercado Pago)

### Arquivos do projeto
- `bot.py`              — Bot principal (Telegram)
- `catalog.py`          — **Catálogo mestre consolidado com 112 produtos**
- `database.py`         — Camada SQLite (cadastros, carrinho, pedidos)
- `payments.py`         — Integração PIX (Mercado Pago / Webhook genérico / Manual)
- `qrcode_pix.py`       — Gerador de QR Code PIX
- `.env`                — Configurações (token, admin, pagamento, webhook)
- `warearcade.db`       — Banco SQLite (criado automaticamente no 1º run)
- `restaurar_bot.ps1`   — Script PowerShell de instalação/reparo
- `README.md`           — Este guia

### Catálogo final (CATÁLOGO MESTRE)
**325 produtos no total** — mesclando o catálogo antigo original (92 jogos + software/cursos = 126 itens) com todos os produtos novos dos PRDs anexados + softwares/jogos adicionais completando as categorias.

Todos os **IDs e preços originais do seu catálogo antigo foram preservados** (IDs 1-92 jogos, 100-104 Windows, 110-114 Office, 120-125 Adobe/Design, 130-134 Engenharia, 140-142 Antivírus, 150-152 Ferramentas, 160-161 Streaming, 165 Música, 168 Gift Card, 172 Cloud, 175 Curso Excel, 999 produto de teste).

| Categoria (tipo) | Qtd |
|-----------|-----|
| 🎮 Jogos PC | 161 |
| 🎓 Cursos | 36 |
| 🎨 Design/Adobe | 11 |
| 🤖 IA - Ferramenta (spy/análise) | 11 |
| 🛠️ Ferramentas/Utilitários | 9 |
| 🖥️ Sistemas Operacionais | 8 |
| 🎬 Vídeo/Edição | 8 |
| 🔒 Segurança/Antivírus | 8 |
| 🤖 IA - Texto | 8 |
| 📄 Office | 7 |
| 🎬 Streaming | 7 |
| 🤖 IA - Vídeo | 7 |
| 🏗️ Engenharia/3D | 6 |
| 🎁 Gift Cards | 6 |
| 🤖 IA - Imagem | 5 |
| 🤖 IA - Plano | 5 |
| 🤖 IA - Áudio | 4 |
| 🤖 IA - Produtividade | 4 |
| ☁️ Cloud | 3 |
| 🎵 Música | 3 |
| 🤖 IA - Pesquisa | 2 |
| 🤖 IA - Marketing | 2 |
| 🤖 IA - Código | 2 |
| 💼 Produtividade (combos) | 1 |
| 🧪 Teste | 1 |
| **Total** | **325** |

#### Produtos adicionados via documentos anexados:
- ✅ 12 Cursos de Importação (IMP001–IMP012) com preços do PRD (80% OFF)
- ✅ Curso Facebook Zero (FB001) com descrição longa
- ✅ 8 aulas F39–F46 (DECEA Aviação, Photoshop CS6, Adobe Premiere)
- ✅ 3 packs (DECEA, Photoshop, Premiere)
- ✅ 34 ferramentas de IA (IA Knights) cobrindo texto/vídeo/imagem/áudio/produtividade/marketing/código
- ✅ 11 ferramentas de análise/espiã (AdSpy, SimilarWeb, Ahrefs, SEMrush, etc.)
- ✅ 3 planos IA Knights (Mensal/Trimestral/Vitalício) com os preços do relatório (R$47, R$97, R$197)
- ✅ 2 packs IA (Premium e Criador)
- ✅ Jogos, softwares e cursos extras para completar as categorias
- ✅ SKU único em todos os produtos (facilita integração futura com e-commerce)
- Todos os IDs antigos preservados; itens novos receberam IDs sequenciais a partir de 1000.

---

## 🚀 Como instalar do zero
1. Coloque **todos os arquivos** numa pasta, ex: `C:\Users\AriGsena\Desktop\WareArcadeBot`
2. Edite o `.env`:
   - `TELEGRAM_BOT_TOKEN` = token do @BotFather
   - `ADMIN_CHAT_IDS` = seu ID do Telegram (use @userinfobot)
3. Execute no PowerShell:
   ```powershell
   cd C:\Users\AriGsena\Desktop\WareArcadeBot
   Set-ExecutionPolicy -Scope Process Bypass -Force
   .\restaurar_bot.ps1
   ```

---

## 💳 Modos de pagamento
Configure no `.env` a variável `PAYMENT_PROVIDER`:

| Modo | Funcionamento |
|------|---------------|
| `manual` (padrão) | Gera QR PIX estático da chave da empresa. Cliente clica em "Já Paguei", admin recebe aviso e aprova manualmente. |
| `mercadopago` | Cria cobrança PIX no Mercado Pago, gera QR dinâmico. Webhook recebe confirmação em segundos e **aprova o pedido automaticamente** (se `AUTO_APPROVE_ON_PAID=1`). |
| `generic` | Qualquer gateway que faça POST JSON no webhook. Espera campos `codigo`/`external_reference`/`order_id` e `status=approved/paid`. |

---

## ⚙️ Configurar PIX AUTOMÁTICO com Mercado Pago

### 1. Pegar o Access Token
- Acesse: https://www.mercadopago.com.br/developers/panel/credentials
- Entre com a conta da Mary (a mesma da chave PIX CNPJ)
- Copie o **Access Token de Produção** (não use o de teste)
- Coloque no `.env`:
  ```
  PAYMENT_PROVIDER=mercadopago
  MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxx-xxxxxx
  AUTO_APPROVE_ON_PAID=1
  ```

### 2. Expor o webhook publicamente
O Mercado Pago precisa mandar um POST pra sua máquina. Você tem 3 opções:

**Opção A — Teste rápido com ngrok (recomendado pra começar):**
```powershell
# Baixe ngrok.exe e rode:
ngrok http 8000
```
Ele vai te dar uma URL tipo `https://abc123.ngrok.io`. Coloque no `.env`:
```
PUBLIC_WEBHOOK_URL=https://abc123.ngrok.io/webhook/pix
WEBHOOK_PORT=8000
```

**Opção B — VPS/servidor com domínio:**
Configure Nginx/Cloudflare apontando pro bot na porta 8000 (HTTPS obrigatório pro MP). Exemplo de URL:
```
PUBLIC_WEBHOOK_URL=https://bot.seudominio.com.br/webhook/pix
```

**Opção C — Cloudflare Tunnel (sem VPS):**
Use `cloudflared tunnel --url http://localhost:8000`, funciona parecido com ngrok.

### 3. Configurar webhook no painel do MP
- Vá em https://www.mercadopago.com.br/developers/panel/webhooks
- Adicione a URL do webhook (mesma do PUBLIC_WEBHOOK_URL)
- Marque o evento **Payments** (`payment.updated`)

### 4. Reinicie o bot
O servidor webhook roda em segundo plano. Ao iniciar, você verá no console:
```
🌐 Webhook PIX rodando em 0.0.0.0:8000/webhook/pix (provider=mercadopago)
🚀 Bot rodando!
```

Pronto: quando o cliente escanear e pagar o PIX, o pedido é aprovado automaticamente sem precisar de nenhum `/aprovar` manual.

---

## 🗄️ O que é salvo no banco (warearcade.db)
- **cadastros**: nome, email, whatsapp (por user_id)
- **carrinhos**: itens pendentes por usuário (não some ao reiniciar!)
- **pedidos**: código, itens, total, status, payment_id, link_download, timestamps
- **ordem_counter**: contador para gerar WA-000001, WA-000002…

Se reiniciar o bot, tudo volta do jeito que estava.

---

## 🛠️ Comandos administrativos
| Comando | Ação |
|---------|------|
| `/admin` | Verifica status, mostra modo de pagamento |
| `/pendentes` | Lista pedidos pendentes/aguardando aprovação |
| `/aprovar WA-XXXXXX` | Aprova manualmente e envia link de download |
| `/rejeitar WA-XXXXXX` | Rejeita o pedido e avisa o cliente |
| `/info WA-XXXXXX` | Mostra detalhes completos do pedido (inclusive payment_id) |

---

## 🔐 Segurança
- Dados locais em SQLite (não ficam na nuvem)
- Webhook com assinatura HMAC configurável (`WEBHOOK_SECRET`)
- LGPD: dados cadastrais são só nome/email/whatsapp, sem dados de cartão
- Pagamentos 100% processados pelo Mercado Pago, o bot nunca vê senhas

---

## 📞 Suporte
Se der erro, olhe o console do PowerShell — ele agora imprime logs de pagamento
(`💰 PIX RECEBIDO!`, `✅ PIX confirmado`, etc.) facilitando diagnóstico.

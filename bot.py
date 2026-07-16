# -*- coding: utf-8 -*-
"""
WareArcadeBot - Ware Arcade Game
Versão com persistência SQLite + pagamento PIX automático (Mercado Pago / Webhook genérico).
"""
import logging
import math
import asyncio
import os
import re
import random
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from telegram.request import HTTPXRequest

from qrcode_pix import enviar_qrcode_pix_texto, EMPRESA
import database as db
import payments as pay

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

# ===================== CONFIG =====================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
ITEMS_PER_PAGE = 6
AUTO_APPROVE_ON_PAID = os.getenv("AUTO_APPROVE_ON_PAID", "1") == "1"

ADMIN_IDS = []
_admin_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
if _admin_ids_str:
    for _aid in _admin_ids_str.split(","):
        try:
            _aid = _aid.strip()
            if _aid:
                ADMIN_IDS.append(int(_aid))
        except ValueError:
            print(f"⚠️ Admin ID inválido: {_aid}")

if not TOKEN:
    print("❌ Token não encontrado! Configure TELEGRAM_BOT_TOKEN no .env")
    raise SystemExit(1)

# ===================== CATÁLOGO =====================
try:
    from catalog import (
        GAMES_CATALOG, TIPOS, CATEGORIAS,
        get_game_by_id, search_games, get_offers, games_by_categoria,
    )
    print(f"✅ Catálogo carregado: {len(GAMES_CATALOG)} produtos")
    print(f"📂 Tipos: {len(TIPOS)} | Categorias: {len(CATEGORIAS)}")
except Exception as e:
    print(f"❌ Erro ao carregar catálogo: {e}")
    GAMES_CATALOG = []
    TIPOS = {}
    CATEGORIAS = {}
    def get_game_by_id(_id): return None
    def search_games(_q): return []
    def get_offers(): return []
    def games_by_categoria(_c): return []

# ===================== INICIALIZA BANCO =====================
db.init_db()
db.carregar_tudo_para_memoria()

# Estado em memória (agora espelha o SQLite)
carrinhos = db.carrinhos_mem
pedidos = db.pedidos_mem
pedidos_pendentes = db.pedidos_pendentes_mem
cadastros = db.cadastros_mem
ordens = [0]  # mutável para manter contagem por sessão

def gerar_codigo_pedido():
    cod = db.next_codigo()
    return cod

# ===================== FUNÇÕES AUXILIARES =====================
def validar_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None

def formatar_whatsapp(numero):
    numero = re.sub(r"\D", "", numero)
    if len(numero) == 11:
        return f"+{numero}"
    if len(numero) == 10:
        return f"+55{numero}"
    if numero.startswith("55") and len(numero) >= 12:
        return f"+{numero}"
    return f"+{numero}" if not numero.startswith("+") else numero

async def safe_edit(update, text, reply_markup=None, parse_mode=ParseMode.MARKDOWN):
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, parse_mode=parse_mode, reply_markup=reply_markup,
            )
        return True
    except BadRequest as e:
        if "message is not modified" in str(e):
            return True
        try:
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    text, parse_mode=parse_mode, reply_markup=reply_markup)
                return True
        except Exception:
            pass
        try:
            chat_id = (update.callback_query.message.chat_id
                       if update.callback_query and update.callback_query.message
                       else update.effective_chat.id)
            await update._bot.send_message(
                chat_id=chat_id, text=text,
                parse_mode=parse_mode, reply_markup=reply_markup,
            )
            return True
        except Exception:
            return False

async def notificar_admin(context, mensagem):
    if not ADMIN_IDS:
        return False
    ok = False
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=mensagem, parse_mode=ParseMode.MARKDOWN)
            ok = True
        except Exception:
            pass
    return ok

# ===================== KEYBOARDS =====================
def menu_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Ver Catálogo Completo", callback_data="catalog_0")],
        [InlineKeyboardButton("🔥 Ofertas Imperdíveis", callback_data="offers_0"),
         InlineKeyboardButton("🔍 Buscar Produto",    callback_data="search")],
        [InlineKeyboardButton("📂 Categorias",        callback_data="categories"),
         InlineKeyboardButton("🛒 Meu Carrinho",      callback_data="cart")],
        [InlineKeyboardButton("📦 Meus Pedidos",      callback_data="my_orders"),
         InlineKeyboardButton("👤 Meu Cadastro",      callback_data="my_profile")],
        [InlineKeyboardButton("❓ Suporte / Ajuda",   callback_data="support")],
    ])

def catalog_keyboard(page, games, prefix="catalog"):
    if not games:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("📭 Nenhum produto", callback_data="noop")],
             [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]]
        )
    total_pages = max(1, math.ceil(len(games) / ITEMS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_games = games[start_idx:end_idx]

    keyboard = []
    for g in page_games:
        tag = " 🔥" if g.get("oferta", False) else ""
        nome_curto = (g["nome"][:28] + "...") if len(g["nome"]) > 28 else g["nome"]
        emoji_tipo = g.get("tipo", "🎮").split()[0] if g.get("tipo") else "🎮"
        keyboard.append([
            InlineKeyboardButton(
                f"{emoji_tipo} {nome_curto} - R$ {g['preco_oferta']:.2f}{tag}",
                callback_data=f"game_{g['id']}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"{prefix}_{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️ Próximo", callback_data=f"{prefix}_{page+1}"))
    keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🔍 Buscar Produto", callback_data="search_product")])
    keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def game_detail_keyboard(game_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Adicionar ao Carrinho", callback_data=f"add_cart_{game_id}")],
        [InlineKeyboardButton("⚡ Comprar Agora",         callback_data=f"buy_now_{game_id}")],
        [InlineKeyboardButton("🔙 Voltar ao Catálogo",    callback_data="catalog_0")],
        [InlineKeyboardButton("🏠 Menu",                  callback_data="main_menu")],
    ])

def back_to_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]]
    )

def categorias_keyboard():
    keyboard = []
    for tipo, produtos in sorted(TIPOS.items(), key=lambda x: -len(x[1])):
        keyboard.append([
            InlineKeyboardButton(
                f"{tipo} ({len(produtos)})",
                callback_data=f"cat_{tipo}",
            )
        ])
    keyboard.append([
        InlineKeyboardButton("🔥 Ofertas", callback_data="offers_0"),
        InlineKeyboardButton("🔍 Buscar",  callback_data="search"),
    ])
    keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

# ===================== MENSAGENS =====================
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 6 banners diferentes, cada um com seu estilo de mensagem combinando
BANNER_VARIANTS = [
    {
        "file": "banner_01_cyberpunk.jpg",
        "emoji": "🎮",
        "caption": (
            "🎮 *WARE ARCADE GAME* 🎮\n"
            "_WareArcadeBot_\n\n"
            "✨ *A sua loja digital completa no Telegram!* ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos para PC\n"
            "🤖 Inteligência Artificial\n"
            "🎓 Cursos online\n"
            "🖥️ Softwares e Windows\n"
            "🎬 Streaming\n"
            "🎁 Gift Cards e muito mais!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ *Entrega imediata* após pagamento\n"
            "🔒 *100% seguro* com PIX automático\n"
            "💚 *Atendimento* humanizado rápido\n\n"
            "Toque em um botão abaixo 👇"
        ),
    },
    {
        "file": "banner_02_gold.jpg",
        "emoji": "👑",
        "caption": (
            "👑 *WARE ARCADE GAME* 👑\n"
            "_Premium Edition_\n\n"
            "💎 *A melhor seleção de jogos, softwares e IA* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏆 Produtos premium selecionados\n"
            "🎮 Jogos de qualidade garantida\n"
            "🤖 Ferramentas de IA exclusivas\n"
            "🎓 Cursos completos e atualizados\n"
            "🖥️ Softwares originais\n"
            "🎁 Gift Cards com os melhores preços\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚚 *Entrega rápida* em até 4 horas\n"
            "✅ *Produtos originais* com garantia\n"
            "🎧 *Suporte 24h* para te ajudar\n\n"
            "Escolha sua opção abaixo 👇"
        ),
    },
    {
        "file": "banner_03_red.jpg",
        "emoji": "🔥",
        "caption": (
            "🔥 *WARE ARCADE GAME* 🔥\n"
            "_Prepare-se para a ação!_\n\n"
            "💥 *Sua gameplay começa aqui!* 💥\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 +150 jogos para PC\n"
            "🤖 IAs e bots exclusivos\n"
            "🎓 Cursos para dominar tudo\n"
            "🖥️ Programas e softwares\n"
            "▶️ Streaming e entretenimento\n"
            "🎁 Brindes e conteúdo grátis\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 *Download imediato* após pagar\n"
            "💰 *Os melhores preços* do mercado\n"
            "🎯 *Mais de 300 produtos* disponíveis\n\n"
            "Bora começar? Clica num botão! 👇"
        ),
    },
    {
        "file": "banner_04_green.jpg",
        "emoji": "🤖",
        "caption": (
            "🤖 *WARE ARCADE GAME* 🤖\n"
            "_Tecnologia, jogos e IA no Telegram_\n\n"
            "⚡ *Sua loja digital 100% automatizada!* ⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos para PC\n"
            "🧠 Ferramentas de Inteligência Artificial\n"
            "📱 Tecnologia e apps\n"
            "🛠️ Ferramentas profissionais\n"
            "🎁 Gift cards e conteúdos exclusivos\n"
            "⭐ Produtos verificados\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ *PIX automático* — sem espera\n"
            "🔒 *Compra 100% segura* e criptografada\n"
            "📲 *Tudo direto no Telegram* — sem sites\n\n"
            "Navegue pelas opções abaixo 👇"
        ),
    },
    {
        "file": "banner_05_pink.jpg",
        "emoji": "💜",
        "caption": (
            "💜 *BOAS VINDAS A WARE ARCADE GAME!* 💜\n"
            "_Tudo que você precisa em um só lugar!_\n\n"
            "✨ *Sua loja digital favorita no Telegram!* ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Games e acessórios\n"
            "🤖 IAs e ferramentas incríveis\n"
            "🎓 Cursos de todas as áreas\n"
            "🎬 Streaming e entretenimento\n"
            "🎁 Presentes e utilidades\n"
            "👕 E muito mais!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💜 *Mais de 300 produtos* no catálogo\n"
            "✨ *Ofertas diárias* com descontos\n"
            "💚 *PIX fácil* e aprovação rápida\n\n"
            "Vem conferir! Escolha abaixo 👇"
        ),
    },
    {
        "file": "banner_06_navy.jpg",
        "emoji": "🏢",
        "caption": (
            "✅ *BEM-VINDO A WARE ARCADE GAME* ✅\n"
            "_Sua loja digital confiável_\n\n"
            "🛡️ *Jogos, Softwares, IA e Cursos com garantia!* 🛡️\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Empresa cadastrada e legalizada\n"
            "🏆 Mais de 2.500 clientes satisfeitos\n"
            "🛡️ Garantia de 7 dias em todos os produtos\n"
            "🎮 Jogos, softwares, cursos, IA e mais\n"
            "🔒 Compra 100% segura\n"
            "🎧 Suporte especializado\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 *Produtos originais* com nota\n"
            "💬 *Atendimento* humanizado\n"
            "🔐 *Seus dados* protegidos pela LGPD\n\n"
            "Confira nossas opções abaixo 👇"
        ),
    },
    # === Coleção Luxury Gems (5 variações no estilo ouro premium) ===
    {
        "file": "banner_07_sapphire.jpg",
        "emoji": "💎",
        "caption": (
            "💎 *WARE ARCADE GAME* 💎\n"
            "_Sapphire Premium Edition_\n\n"
            "🔷 *Qualidade safira em todos os produtos* 🔷\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos selecionados a dedo\n"
            "🤖 IAs de última geração\n"
            "🎓 Cursos premium atualizados\n"
            "🖥️ Softwares originais\n"
            "🎬 Streaming liberado\n"
            "🎁 Gift cards com desconto\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚚 *Entrega expressa* após confirmação\n"
            "✅ *Produtos verificados* e testados\n"
            "🎧 *Suporte VIP* 24 horas por dia\n\n"
            "Escolha uma opção abaixo 👇"
        ),
    },
    {
        "file": "banner_08_ruby.jpg",
        "emoji": "❤️",
        "caption": (
            "❤️ *WARE ARCADE GAME* ❤️\n"
            "_Ruby Premium Edition_\n\n"
            "🔴 *A paixão por games e tecnologia* 🔴\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Os melhores jogos para PC\n"
            "🤖 Ferramentas de IA exclusivas\n"
            "🎓 Cursos de alta performance\n"
            "🖥️ Softwares e Windows ativados\n"
            "🎬 Entretenimento sem limites\n"
            "🎁 Promoções exclusivas\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚚 *Entrega super rápida* via PIX\n"
            "✅ *Produtos originais* com garantia\n"
            "💌 *Atendimento carismático* e rápido\n\n"
            "Vem conferir! Clica abaixo 👇"
        ),
    },
    {
        "file": "banner_09_emerald.jpg",
        "emoji": "💚",
        "caption": (
            "💚 *WARE ARCADE GAME* 💚\n"
            "_Emerald Premium Edition_\n\n"
            "🟢 *A experiência premium que você merece* 🟢\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos atualizados constantemente\n"
            "🤖 IAs verdes (eficientes e poderosas)\n"
            "🎓 Cursos de qualidade esmeralda\n"
            "🖥️ Softwares premium livres de vírus\n"
            "🎬 Streaming em alta definição\n"
            "🎁 Bônus exclusivos em compras\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ *PIX automático* na hora\n"
            "✅ *Garantia de satisfação* total\n"
            "🌿 *Atendimento* humano sem enrolação\n\n"
            "Explore o catálogo abaixo 👇"
        ),
    },
    {
        "file": "banner_10_amethyst.jpg",
        "emoji": "💜",
        "caption": (
            "💜 *WARE ARCADE GAME* 💜\n"
            "_Amethyst Premium Edition_\n\n"
            "🟣 *Elegância e poder em um só lugar* 🟣\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos raros e exclusivos\n"
            "🤖 IAs místicas e poderosas\n"
            "🎓 Cursos de conhecimento profundo\n"
            "🖥️ Softwares raros e especiais\n"
            "🎬 Streaming premium liberado\n"
            "🎁 Kits e combos com desconto\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 *Download imediato* após pagamento\n"
            "💎 *Produtos premium* selecionados\n"
            "🎧 *Suporte dedicado* sempre à disposição\n\n"
            "Escolha seu destino abaixo 👇"
        ),
    },
    {
        "file": "banner_11_platinum.jpg",
        "emoji": "⚪",
        "caption": (
            "⚪ *WARE ARCADE GAME* ⚪\n"
            "_Platinum Edition — A mais alta qualidade_\n\n"
            "⬜ *Nível Platina: o melhor do melhor* ⬜\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 Jogos AAA e indies selecionados\n"
            "🤖 IAs de ponta do mercado\n"
            "🎓 Cursos premium com certificado\n"
            "🖥️ Softwares profissionais completos\n"
            "🎬 Todos os streamings em um só lugar\n"
            "🎁 Tratamento VIP em todo pedido\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ *Aprovação em segundos* no PIX\n"
            "🏆 *Qualidade platina* garantida\n"
            "🛡️ *Garantia estendida* em todos os produtos\n\n"
            "Bem-vindo(a) ao nível premium! 👇"
        ),
    },
]

# Filtra apenas banners que existem no disco (evita erro se algum faltar)
BANNER_VARIANTS = [b for b in BANNER_VARIANTS
                   if os.path.exists(os.path.join(ASSETS_DIR, b["file"]))]

def pick_random_banner():
    """Retorna (caminho_completo, caption) de um banner aleatório."""
    variant = random.choice(BANNER_VARIANTS) if BANNER_VARIANTS else None
    if not variant:
        return None, WELCOME_CAPTION_FALLBACK
    return os.path.join(ASSETS_DIR, variant["file"]), variant["caption"]

WELCOME_CAPTION_FALLBACK = (
    "🎮 *WARE ARCADE GAME* 🎮\n"
    "_WareArcadeBot_\n\n"
    "✨ *A sua loja digital completa no Telegram!* ✨\n\n"
    "⚡ Entrega imediata | 🔒 PIX seguro | 💚 Atendimento rápido\n\n"
    "Toque em um botão abaixo 👇"
)

# Mensagens variadas para a saudação personalizada (também sorteadas)
SAUDACOES_VARIANTS = [
    "👋 Olá, *{nome}*!",
    "🔥 E aí, *{nome}*! Tudo bem?",
    "✨ Que bom te ver por aqui, *{nome}*!",
    "🎮 Bem-vindo(a), *{nome}*!",
    "💚 Olá, *{nome}*! É um prazer te receber!",
    "🚀 Prepare-se, *{nome}*! As ofertas estão imperdíveis hoje!",
]

DICAS_VARIANTS = [
    "💡 *Dica rápida:* comece por 🔥 Ofertas Imperdíveis para ver os descontos!",
    "🎯 *Novidade:* confira as novas IAs que acabamos de adicionar!",
    "⚡ *Lembre-se:* PIX aprova automaticamente em segundos!",
    "🎁 *Promoção:* vários produtos com desconto hoje só!",
    "🏆 *Mais pedido:* a seção de Jogos para PC está bombando!",
    "💎 *Dica premium:* nossa seção de IA tem ferramentas exclusivas!",
]

def mensagem_confirmacao_elegante(nome_cliente, codigo_pedido, total, itens):
    upsell = {"nome": "Antivírus Premium (1 ano)", "preco": 59.90, "id": 140}
    texto = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   🎉 *PEDIDO CONFIRMADO!* 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{nome_cliente}*! 👋\n\n"
        "✅ Seu pedido foi *confirmado com sucesso*!\n"
        f"📋 *Código:* `{codigo_pedido}`\n"
        f"💰 *Total:* R$ {total:.2f}\n"
        f"📦 *Itens:* {len(itens)} produto(s)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   ⏳ *ATENÇÃO - ENTREGA* ⏳\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Pagamento confirmado!*\n"
        "*Os downloads serão liberados em até 4 horas.* ⏰\n\n"
        "📱 Você receberá o link por:\n"
        "   📧 *Email*\n   📱 *WhatsApp*\n\n"
        "🔒 *100% SEGURO*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   💰 *APROVEITE A OFERTA!* 💰\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛡️ *Proteja seu PC com antivírus premium!*\n"
        f"✨ *{upsell['nome']}* - *R$ {upsell['preco']:.2f}*\n\n"
        "➡️ *Adicione agora e receba junto com seu pedido!*\n"
    )
    return texto, upsell

def mensagem_aprovacao_elegante(nome_cliente, codigo_pedido, link_download):
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   🎊 *PEDIDO APROVADO!* 🎊\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Olá, *{nome_cliente}*! 🚀\n\n"
        "✅ Seu pedido foi *aprovado com sucesso*!\n"
        f"📋 *Código:* `{codigo_pedido}`\n\n"
        f"⬇️ *Seu link de download:*\n`{link_download}`\n\n"
        "⏳ *Link válido por 48 horas*\n"
        "🔒 *Download seguro e garantido*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   💚 *APROVEITE SEU JOGO!* 💚\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⭐ *Avalie nosso atendimento:* /feedback"
    )

# ===================== COMANDOS ADMIN =====================
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    prov = pay.PROVIDER
    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            "👑 *ADMINISTRADOR VERIFICADO*\n\n"
            "✅ Você é administrador!\n\n"
            f"💳 Provedor PIX: `{prov}`\n"
            f"⚡ Auto-aprovar: `{AUTO_APPROVE_ON_PAID}`\n\n"
            "📋 *Comandos:*\n"
            "🔹 /admin - Verificar status\n"
            "🔹 /pendentes - Listar pedidos\n"
            "🔹 /aprovar COD - Aprovar pedido\n"
            "🔹 /rejeitar COD - Rejeitar pedido\n"
            "🔹 /info COD - Ver detalhes do pedido\n\n"
            f"👤 Seu ID: `{user_id}`",
            parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(
            "❌ *ACESSO NEGADO*\n\n"
            "Você não é administrador!\n\n"
            f"Para ser admin, coloque no .env:\n`ADMIN_CHAT_IDS={user_id}`",
            parse_mode=ParseMode.MARKDOWN)

async def cmd_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return
    pend = db.listar_pedidos_por_status("pendente", "aguardando_aprovacao")
    if not pend:
        await update.message.reply_text(
            "📋 *PEDIDOS PENDENTES*\n\n✅ Nenhum pedido pendente!",
            parse_mode=ParseMode.MARKDOWN)
        return
    text = "📋 *PEDIDOS PENDENTES*\n\n"
    for pedido in pend:
        cliente = pedido.get("cliente", {})
        text += (f"🔹 *{pedido['codigo']}* - R$ {pedido['total']:.2f}  ({pedido['status']})\n"
                 f"   👤 {cliente.get('nome', 'Não informado')}\n"
                 f"   📦 {len(pedido['itens'])} itens\n"
                 f"   ⏳ {pedido.get('data', '')}\n\n")
    text += "✅ Use: /aprovar COD   ❌ Use: /rejeitar COD"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def _aprovar_pedido(context, codigo, por_admin=False):
    pedido = db.carregar_pedido(codigo)
    if not pedido:
        return False, "não encontrado"
    if pedido["status"] == "aprovado":
        return False, "já aprovado"
    link_download = pay.get_download_link(codigo)
    db.update_pedido(codigo, "aprovado",
                     link_download=link_download,
                     approved_at=datetime.now().isoformat())
    pedido = db.carregar_pedido(codigo)
    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Suporte", callback_data="support")],
        [InlineKeyboardButton("🏠 Menu",   callback_data="main_menu")],
    ])
    try:
        await context.bot.send_message(
            pedido["user_id"],
            mensagem_aprovacao_elegante(nome_cliente, codigo, link_download),
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception as e:
        log.warning("Não consegui notificar cliente %s: %s", pedido["user_id"], e)

    if por_admin:
        await notificar_admin(context,
            f"✅ Pedido `{codigo}` aprovado manualmente.\n👤 {nome_cliente}\n💰 R$ {pedido['total']:.2f}")
    return True, link_download

async def cmd_aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return
    if not context.args:
        await update.message.reply_text(
            "📋 *APROVAR PEDIDO*\n\nUse: /aprovar COD\nEx: /aprovar WA-000001",
            parse_mode=ParseMode.MARKDOWN)
        return
    codigo = context.args[0].upper()
    ok, res = await _aprovar_pedido(context, codigo, por_admin=True)
    if not ok:
        await update.message.reply_text(f"❌ Pedido `{codigo}` {res}.")
        return
    await update.message.reply_text(
        f"✅ *Pedido aprovado!*\n📋 `{codigo}`\n🔗 {res}",
        parse_mode=ParseMode.MARKDOWN)

async def cmd_rejeitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return
    if not context.args:
        await update.message.reply_text(
            "📋 *REJEITAR PEDIDO*\n\nUse: /rejeitar COD",
            parse_mode=ParseMode.MARKDOWN)
        return
    codigo = context.args[0].upper()
    pedido = db.carregar_pedido(codigo)
    if not pedido:
        await update.message.reply_text(f"❌ Pedido `{codigo}` não encontrado!")
        return
    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")
    db.update_pedido(codigo, "rejeitado")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Suporte", callback_data="support")],
        [InlineKeyboardButton("🏠 Menu",   callback_data="main_menu")],
    ])
    try:
        await context.bot.send_message(
            pedido["user_id"],
            f"❌ *PEDIDO REJEITADO*\n\nOlá {nome_cliente}!\n\nSeu pedido `{codigo}` foi rejeitado.\n\n"
            "💬 Para mais informações, fale com nosso suporte.",
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception as e:
        log.warning(e)
    await update.message.reply_text(
        f"❌ *Pedido rejeitado!*\n📋 `{codigo}` 👤 {nome_cliente}",
        parse_mode=ParseMode.MARKDOWN)

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Uso: /info COD")
        return
    codigo = context.args[0].upper()
    p = db.carregar_pedido(codigo)
    if not p:
        await update.message.reply_text("❌ Pedido não encontrado.")
        return
    c = p.get("cliente", {})
    txt = (
        f"📋 *Pedido {codigo}*\n"
        f"Status: `{p['status']}`\n"
        f"Usuário: `{p['user_id']}`\n"
        f"Valor: R$ {p['total']:.2f}\n"
        f"Método: {p['metodo']} (prov {p.get('pay_provider', pay.PROVIDER)})\n"
        f"Pagamento ID: `{p.get('pagamento_id') or '-'}`\n"
        f"Data: {p.get('data')}\n\n"
        f"👤 Cliente:\n  {c.get('nome')}\n  {c.get('email')}\n  {c.get('whatsapp')}\n\n"
        f"Itens:\n"
    )
    for it in p.get("itens", []):
        txt += f"  - {it['nome']} R$ {it['preco']:.2f}\n"
    if p.get("link_download"):
        txt += f"\n🔗 {p['link_download']}"
    await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)

# ===================== CALLBACK DE PAGAMENTO AUTOMÁTICO =====================
@pay.on_payment_confirmed
async def pagamento_confirmado(codigo: str, payload: dict):
    """Chamado pelo servidor de webhook quando o PIX é pago."""
    pedido = db.carregar_pedido(codigo)
    if not pedido:
        log.warning("Webhook para pedido inexistente: %s", codigo)
        return
    if pedido["status"] in ("aprovado", "rejeitado"):
        return  # já tratado

    db.update_pedido(codigo, "pago", confirmed_at=datetime.now().isoformat())

    # Avisa ao cliente que o pagamento foi recebido
    bot_app = globals().get("_app")
    if bot_app:
        nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")
        try:
            await bot_app.bot.send_message(
                pedido["user_id"],
                f"💚 *Pagamento confirmado!*\n\n"
                f"Olá {nome_cliente}, recebemos seu PIX do pedido `{codigo}`.\n"
                "Seu pedido está sendo liberado...",
                parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            log.warning(e)

        if AUTO_APPROVE_ON_PAID:
            log.info(f"Aprovando pedido {codigo} automaticamente...")
            await _aprovar_pedido(bot_app, codigo, por_admin=False)
        else:
            # Notifica admins para aprovar
            total = pedido["total"]
            await notificar_admin(bot_app,
                f"💚 *PIX RECEBIDO!*\n\n"
                f"📋 Pedido `{codigo}` no valor de R$ {total:.2f}\n"
                f"👤 {nome_cliente}\n\n"
                f"Use: /aprovar {codigo}")

# ===================== HANDLERS PRINCIPAIS =====================
async def _enviar_banner_e_menu(chat_id, context, msg_boas_vindas):
    """Envia banner aleatório + menu com fallback seguro (nunca quebra)."""
    banner_path, caption = pick_random_banner()
    try:
        if banner_path and os.path.exists(banner_path):
            with open(banner_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=30,
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id, text=caption,
                parse_mode=ParseMode.MARKDOWN,
                read_timeout=30, write_timeout=30)
    except Exception as e:
        log.warning("Falha ao enviar banner, usando fallback texto: %s", e)
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=caption,
                parse_mode=ParseMode.MARKDOWN,
                read_timeout=30, write_timeout=30)
        except Exception as e2:
            log.error("Nem fallback funcionou: %s", e2)

    # Sempre envia o menu depois, mesmo se o banner falhar
    await context.bot.send_message(
        chat_id=chat_id, text=msg_boas_vindas,
        parse_mode=ParseMode.MARKDOWN, reply_markup=menu_principal(),
        read_timeout=30, write_timeout=30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    total = len(GAMES_CATALOG)
    ofertas = len([g for g in GAMES_CATALOG if g.get("oferta", False)])

    # Sorteia saudação e dica aleatoriamente
    saudacao = random.choice(SAUDACOES_VARIANTS).format(nome=user.first_name)
    dica = random.choice(DICAS_VARIANTS)

    # Texto de boas-vindas variado (aleatório em cada acesso)
    msg_boas_vindas = (
        f"{saudacao}\n\n"
        f"✨ Temos *{total} produtos* disponíveis, *{ofertas} em oferta*! 🎉\n\n"
        f"{dica}\n\n"
        "Escolha uma opção abaixo 👇"
    )

    # Se for comando /start ou /menu (mensagem direta), envia banner ALEATÓRIO + menu
    if update.message:
        await _enviar_banner_e_menu(update.effective_chat.id, context, msg_boas_vindas)
    else:
        # Callback query (volta ao menu): envia nova mensagem com banner sorteado
        query = update.callback_query
        chat_id = query.message.chat_id
        try:
            await _enviar_banner_e_menu(chat_id, context, msg_boas_vindas)
            # Tenta apagar a mensagem antiga para ficar limpo
            try:
                await query.message.delete()
            except Exception:
                pass
        except Exception as e:
            log.warning("Fallback para safe_edit: %s", e)
            await safe_edit(update, msg_boas_vindas, menu_principal())

async def show_game_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: int):
    query = update.callback_query
    game = get_game_by_id(game_id)
    if not game:
        await query.answer("❌ Produto não encontrado!")
        return
    nome = game["nome"]
    preco = game["preco_oferta"]
    preco_orig = game.get("preco_original", preco)
    if game.get("oferta", False) and preco_orig and preco_orig != preco:
        desconto = int((1 - preco / preco_orig) * 100)
        preco_text = f"De R$ {preco_orig:.2f} por R$ {preco:.2f} ({desconto}% OFF)"
    else:
        preco_text = f"R$ {preco:.2f}"
    categorias = ", ".join(game.get("categorias", []))
    emoji_tipo = game.get("tipo", "🎮").split()[0] if game.get("tipo") else "🎮"
    text = (f"{emoji_tipo} *{nome}*\n\n💰 {preco_text}\n"
            f"🖥️ Plataforma: {game.get('plataforma', 'PC')}\n"
            f"📂 Categorias: {categorias}\n\n"
            f"📝 {game.get('descricao', '')}\n\n"
            "---\n\n✅ Entrega digital imediata\n"
            "🔒 Pagamento 100% seguro\n⏳ Link válido por 48h")
    chat_id = query.message.chat_id
    try:
        await query.message.delete()
    except Exception:
        pass
    imagem_url = game.get("imagem_url", "")
    if imagem_url and imagem_url.startswith("http"):
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=imagem_url, caption=text,
                                         reply_markup=game_detail_keyboard(game_id))
            return
        except Exception:
            pass
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=game_detail_keyboard(game_id))

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    await safe_edit(update, "📚 *CATÁLOGO COMPLETO*\n\nSelecione um produto:",
                    catalog_keyboard(page, GAMES_CATALOG))

async def show_offers(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    offers = get_offers()
    if not offers:
        await safe_edit(update, "🔥 Nenhuma oferta no momento.", back_to_menu())
        return
    await safe_edit(update, "🔥 *OFERTAS IMPERDÍVEIS!*",
                    catalog_keyboard(page, offers, prefix="offers"))

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_edit(update, "📂 *CATEGORIAS*\n\nEscolha uma categoria:", categorias_keyboard())

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo: str, page=0):
    produtos = [g for g in GAMES_CATALOG if g.get("tipo") == tipo]
    if not produtos:
        await update.callback_query.answer("❌ Nenhum produto nesta categoria")
        return
    await safe_edit(update, f"📂 *{tipo}*\n\nSelecione um produto:",
                    catalog_keyboard(page, produtos, prefix=f"catpage_{tipo}"))

async def search_product_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["searching"] = True
    await safe_edit(update, "🔍 *Buscar Produto*\n\nDigite o nome do produto:",
                    InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]]))

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("cadastro_passo"):
        await processar_cadastro(update, context)
        return
    if context.user_data.get("searching", False):
        context.user_data["searching"] = False
        q = update.message.text
        results = search_games(q)
        context.user_data["last_search_results"] = results
        if not results:
            await update.message.reply_text(f"❌ Nenhum produto encontrado para: *{q}*",
                                            parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_menu())
            return
        await update.message.reply_text(
            f"🔍 *Resultados para:* '{q}'\nEncontramos {len(results)} produto(s):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=catalog_keyboard(0, results, prefix="search_res"))

# ===================== CARRINHO =====================
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    cart = db.get_cart(user_id)
    if not cart:
        await safe_edit(update, "🛒 *Meu Carrinho*\n\nSeu carrinho está vazio!", back_to_menu())
        return
    total = sum(item["preco"] for item in cart)
    text = "🛒 *SEU CARRINHO*\n\n"
    keyboard = []
    for i, item in enumerate(cart, 1):
        text += f"{i}. 📦 {item['nome']} - R$ {item['preco']:.2f}\n"
        keyboard.append([InlineKeyboardButton(f"❌ Remover #{i}", callback_data=f"remove_{i-1}")])
    keyboard.append([InlineKeyboardButton("💰 Finalizar Compra", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
    await safe_edit(update, text, InlineKeyboardMarkup(keyboard))

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: int):
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)
    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return
    db.add_to_cart(user_id, game_id, game["nome"], game["preco_oferta"])
    await update.callback_query.answer(f"✅ {game['nome']} adicionado!")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Continuar Comprando", callback_data="catalog_0")],
        [InlineKeyboardButton("💳 Ver Carrinho / Finalizar", callback_data="cart")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])
    try:
        await update.callback_query.message.reply_text(
            f"✅ *{game['nome']}* adicionado ao carrinho!\n\n💰 R$ {game['preco_oferta']:.2f}",
            parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    except Exception:
        pass

async def buy_now(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: int):
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)
    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return
    db.clear_cart(user_id)
    db.add_to_cart(user_id, game_id, game["nome"], game["preco_oferta"])
    if not db.get_cadastro(user_id):
        await iniciar_cadastro(update, context, "checkout")
        return
    await start_checkout(update, context)

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
    user_id = update.callback_query.from_user.id
    db.remove_from_cart(user_id, idx)
    await show_cart(update, context)

# ===================== CADASTRO =====================
async def iniciar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE, redirect_to=None):
    context.user_data["cadastro"] = {"redirect": redirect_to}
    context.user_data["cadastro_passo"] = "nome"
    await safe_edit(update,
        "📝 *CADASTRO DO CLIENTE*\n\n"
        "Para finalizar sua compra, precisamos de alguns dados.\n\n"
        "🔒 *Seus dados estão seguros (LGPD)*\n\n*Digite seu nome completo:*", None)

async def processar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    passo = context.user_data.get("cadastro_passo", "nome")
    dados = context.user_data.get("cadastro", {})

    if passo == "nome":
        dados["nome"] = text
        context.user_data["cadastro"] = dados
        context.user_data["cadastro_passo"] = "email"
        await update.message.reply_text(f"✅ Nome salvo: *{text}*\n\n📧 Agora digite seu *email*:",
                                        parse_mode=ParseMode.MARKDOWN)
    elif passo == "email":
        if not validar_email(text):
            await update.message.reply_text("❌ Email inválido! Digite um email válido:")
            return
        dados["email"] = text
        context.user_data["cadastro"] = dados
        context.user_data["cadastro_passo"] = "whatsapp"
        await update.message.reply_text(
            f"✅ Email salvo: *{text}*\n\n📱 Agora digite seu *WhatsApp* com DDD (ex: 11999999999):",
            parse_mode=ParseMode.MARKDOWN)
    elif passo == "whatsapp":
        numero = re.sub(r"\D", "", text)
        if len(numero) < 10:
            await update.message.reply_text("❌ Número inválido! Digite com DDD (ex: 11999999999):")
            return
        dados["whatsapp"] = formatar_whatsapp(numero)
        db.save_cadastro(user_id, dados)
        context.user_data["cadastro"] = {}
        context.user_data["cadastro_passo"] = None
        await update.message.reply_text(
            "✅ *Cadastro completo!*\n\n"
            f"📛 {dados['nome']}\n📧 {dados['email']}\n📱 {dados['whatsapp']}\n\n🔒 Dados salvos com segurança.",
            parse_mode=ParseMode.MARKDOWN)
        redirect = dados.get("redirect")
        if redirect == "checkout":
            await finalizar_checkout_apos_cadastro(update, context)
        elif redirect == "profile":
            await update.message.reply_text("✅ Cadastro atualizado! Use /menu.", reply_markup=back_to_menu())

async def finalizar_checkout_apos_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = db.get_cart(user_id)
    if not cart:
        await update.message.reply_text("🛒 Carrinho vazio!", reply_markup=back_to_menu())
        return
    total = sum(i["preco"] for i in cart)
    text = "💳 *FINALIZAR COMPRA*\n\n📦 *Itens:*\n"
    for i in cart:
        text += f"📦 {i['nome']} - R$ {i['preco']:.2f}\n"
    text += f"\n💰 *TOTAL: R$ {total:.2f}*\n\n*Selecione o pagamento:*"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💚 PIX (Imediato)", callback_data="pay_pix")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")],
        ]))

async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    cart = db.get_cart(user_id)
    if not cart:
        await update.callback_query.answer("🛒 Carrinho vazio!")
        return
    if not db.get_cadastro(user_id):
        await iniciar_cadastro(update, context, "checkout")
        return
    total = sum(i["preco"] for i in cart)
    dados = db.get_cadastro(user_id)
    text = ("💳 *FINALIZAR COMPRA*\n\n"
            f"👤 *Cliente:* {dados.get('nome')}\n"
            f"📧 *Email:* {dados.get('email')}\n"
            f"📱 *WhatsApp:* {dados.get('whatsapp')}\n\n"
            "📦 *Itens:*\n")
    for i in cart:
        text += f"📦 {i['nome']} - R$ {i['preco']:.2f}\n"
    text += f"\n💰 *TOTAL: R$ {total:.2f}*\n\n*Selecione o pagamento:*"
    await safe_edit(update, text, InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 PIX (Imediato)", callback_data="pay_pix")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")],
    ]))

# ===================== PAGAMENTO =====================
async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    cart = db.get_cart(user_id)
    if not cart:
        await query.answer("🛒 Carrinho vazio!")
        return
    total = sum(i["preco"] for i in cart)
    codigo_pedido = gerar_codigo_pedido()
    dados_cliente = db.get_cadastro(user_id) or {}
    pedido = {
        "codigo": codigo_pedido,
        "user_id": user_id,
        "itens": [dict(i) for i in cart],
        "total": total,
        "metodo": method,
        "status": "pendente",
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": dados_cliente,
        "pay_provider": pay.PROVIDER,
    }

    # Gera QR (MP ou fallback local)
    try:
        qr_meta = await pay.gerar_qr_para_pedido(codigo_pedido, total)
        pedido["pagamento_id"] = qr_meta.get("payment_id")
        pedido["qr_code_copia_cola"] = qr_meta.get("qr_code_copia_cola")
    except Exception as e:
        log.exception("Erro ao gerar QR: %s", e)
        # fallback seguro
        from qrcode_pix import generate_qr_code_pix
        buf, cod = generate_qr_code_pix(total, txid=codigo_pedido)
        qr_meta = {"buffer": buf, "codigo_pix": cod, "qr_code_copia_cola": cod,
                   "payment_id": None, "provider": "manual"}
        pedido["pagamento_id"] = None
        pedido["qr_code_copia_cola"] = cod
        pedido["pay_provider"] = "manual"

    db.save_pedido(pedido)
    db.clear_cart(user_id)

    try:
        await query.message.delete()
    except Exception:
        pass

    # Envia QR Code
    await enviar_qrcode_pix_texto(
        context=context, chat_id=chat_id, valor=total,
        pedido_codigo=codigo_pedido,
        buffer=qr_meta["buffer"],
        copia_cola=qr_meta["qr_code_copia_cola"],
    )

    if qr_meta.get("provider") == "mercadopago":
        msg_pagar = (
            "💚 *PIX GERADO - Pagamento Automático!*\n\n"
            "Escaneie o QR Code no app do banco ou use o botão Copia e Cola.\n"
            "Assim que o PIX cair, o pedido é liberado *automaticamente* — sem precisar clicar em nada.\n\n"
            "Se quiser, também pode usar o botão abaixo para avisar manualmente."
        )
    else:
        msg_pagar = "💰 *Após realizar o pagamento, clique em '✅ Já Paguei'*"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Já Paguei", callback_data=f"confirm_payment_{codigo_pedido}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")],
    ])
    await context.bot.send_message(chat_id=chat_id, text=msg_pagar,
                                   parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, codigo_pedido: str):
    user_id = update.callback_query.from_user.id
    pedido = db.carregar_pedido(codigo_pedido)
    if not pedido or pedido["user_id"] != user_id:
        await update.callback_query.answer("❌ Pedido não encontrado!")
        return
    if pedido["status"] in ("aprovado", "pago"):
        await update.callback_query.answer("✅ Pagamento já confirmado!")
        return
    db.update_pedido(codigo_pedido, "aguardando_aprovacao")
    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")
    itens = pedido.get("itens", [])
    total = pedido.get("total", 0)
    msg_elegante, upsell = mensagem_confirmacao_elegante(nome_cliente, codigo_pedido, total, itens)

    admin_text = (
        "⚠️ *CLIENTE INFORMOU QUE PAGOU*\n\n"
        f"📋 Código: `{codigo_pedido}`\n"
        f"👤 Usuário: {user_id}\n"
        f"💰 R$ {total:.2f}  (provedor: {pedido.get('pay_provider','manual')})\n\n"
        "📦 Itens:\n"
    )
    for it in itens:
        admin_text += f"  - {it['nome']} R$ {it['preco']:.2f}\n"
    c = pedido.get("cliente", {})
    admin_text += (
        f"\n👤 Cliente: {c.get('nome')} | {c.get('email')} | {c.get('whatsapp')}\n\n"
        f"✅ /aprovar {codigo_pedido}   ❌ /rejeitar {codigo_pedido}"
    )
    await notificar_admin(context, admin_text)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛡️ {upsell['nome']} - R$ {upsell['preco']:.2f}",
                              callback_data=f"add_cart_{upsell['id']}")],
        [InlineKeyboardButton("✅ Continuar", callback_data="main_menu")],
    ])
    await safe_edit(update, msg_elegante, kb)

# ===================== PEDIDOS / PERFIL =====================
async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    user_pedidos = db.get_pedidos_usuario(user_id, limit=5)
    if not user_pedidos:
        await safe_edit(update, "📦 *Meus Pedidos*\n\nVocê ainda não realizou nenhum pedido.", back_to_menu())
        return
    text = "📦 *MEUS PEDIDOS*\n\n"
    for p in user_pedidos:
        emoji = {"aprovado": "✅", "pago": "💚", "rejeitado": "❌",
                 "pendente": "⏳", "aguardando_aprovacao": "🔍"}.get(p.get("status"), "⏳")
        text += f"{emoji} *Código:* `{p['codigo']}`\n   {p['itens'][0]['nome']}"
        if len(p["itens"]) > 1:
            text += f" +{len(p['itens'])-1} itens"
        text += f"\n   💰 R$ {p['total']:.2f} | {p['status'].upper()}\n   📅 {p.get('data','')}\n\n"
    await safe_edit(update, text, back_to_menu())

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.callback_query.from_user
    user_id = user.id
    dados = db.get_cadastro(user_id) or {}
    text = (
        "👤 *MEU CADASTRO*\n\n"
        f"📛 Nome: {dados.get('nome', user.first_name)}\n"
        f"📧 Email: {dados.get('email', 'Não informado')}\n"
        f"📱 WhatsApp: {dados.get('whatsapp', 'Não informado')}\n"
        f"🔹 Telegram: @{user.username or 'Não informado'}\n"
        f"🆔 ID: `{user.id}`\n\n"
        "🔒 Seus dados estão seguros (armazenamento local).\n\n"
        "*Para atualizar, clique abaixo ou use:* /cadastro"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Atualizar Cadastro", callback_data="update_profile")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])
    await safe_edit(update, text, kb)

# ===================== INSTITUCIONAL / SUPORTE / FAQ =====================
async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💬 *SUPORTE AO CLIENTE*\n\n"
        "🎮 *WareArcadeBot - Ware Arcade Game*\n\n"
        "*Fale conosco:*\n\n"
        "📱 WhatsApp: +5511940462611\n"
        "📧 Email: warearcadebot@gmail.com\n"
        "📸 Instagram: @warearcadebot\n"
        "🕐 Seg a Sex: 9h-19h | Sáb: 9h-14h\n\n"
        "💚 Atendimento humanizado em até 30 minutos."
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chamar no WhatsApp",  url="https://wa.me/5511940462611")],
        [InlineKeyboardButton("📸 Seguir no Instagram", url="https://instagram.com/warearcadebot")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")],
    ])
    if update.callback_query:
        await safe_edit(update, text, kb)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auto = "automático (em segundos)" if pay.PROVIDER != "manual" else "após confirmação manual"
    text = (
        "❓ *PERGUNTAS FREQUENTES*\n\n"
        "🔹 *Como funciona a compra?*\n"
        "1. Escolha  2. Carrinho  3. Pague  4. Receba o link\n\n"
        "🔹 *Quais formas de pagamento?*\n"
        f"✅ PIX (aprovação {auto})\n✅ Cartão\n✅ Boleto\n\n"
        "🔹 *Onde recebo o produto?*\n📱 Aqui no Telegram / 📧 Email / 📱 WhatsApp\n\n"
        "🔹 *E se não funcionar?* Fale com o suporte!"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Suporte", callback_data="support")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])
    await safe_edit(update, text, kb)

async def show_institutional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏛️ *INSTITUCIONAL - WareArcadeBot*\n\nEscolha uma opção:"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Sobre Nós",         callback_data="inst_sobre")],
        [InlineKeyboardButton("🔒 Privacidade",       callback_data="inst_privacidade")],
        [InlineKeyboardButton("📜 Termos de Uso",     callback_data="inst_termos")],
        [InlineKeyboardButton("🚚 Política de Entrega", callback_data="inst_entrega")],
        [InlineKeyboardButton("💰 Reembolso",         callback_data="inst_reembolso")],
        [InlineKeyboardButton("🛡️ Garantias",         callback_data="inst_garantia")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")],
    ])
    await safe_edit(update, text, kb)

async def institutional_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, page: str):
    paginas = {
        "sobre":       "📖 *SOBRE NÓS*\n\n+2.500 clientes • 126 produtos • Entrega imediata 🚀",
        "privacidade": "🔒 *PRIVACIDADE*\n\nDados protegidos pela LGPD, sem compartilhamento.",
        "termos":      "📜 *TERMOS DE USO*\n\nProdutos digitais, links válidos por 48h, uso pessoal.",
        "entrega":     "🚚 *ENTREGA*\n\nPIX: automático ⚡\nBoleto: 1-3 dias úteis.",
        "reembolso":   "💰 *REEMBOLSO*\n\n7 dias de garantia. Problema técnico = troca ou reembolso.",
        "garantia":    "🛡️ *GARANTIA*\n\nProduto original, entrega garantida, suporte humanizado.",
    }
    texto = paginas.get(page, "❌ Página não encontrada.")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Voltar", callback_data="institutional")],
        [InlineKeyboardButton("🏠 Menu",  callback_data="main_menu")],
    ])
    await safe_edit(update, texto, kb)

# ===================== COMANDOS DIRETOS =====================
async def cmd_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cadastro"] = {}
    context.user_data["cadastro_passo"] = "nome"
    await update.message.reply_text("📝 *CADASTRO*\n\nDigite seu *nome completo*:",
                                    parse_mode=ParseMode.MARKDOWN)

async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⭐ *FEEDBACK*\n\nDigite sua mensagem (ela vai para o admin).\nObrigado! 💚",
        parse_mode=ParseMode.MARKDOWN)
    context.user_data["feedback"] = True

# ===================== CALLBACK ROUTER =====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    data = query.data

    if data == "main_menu":
        await start(update, context)
    elif data.startswith("catalog_"):
        await show_catalog(update, context, int(data.split("_")[1]))
    elif data.startswith("offers_"):
        await show_offers(update, context, int(data.split("_")[1]))
    elif data in ("search", "search_product"):
        await search_product_click(update, context)
    elif data.startswith("search_res_"):
        page = int(data.split("_")[2])
        results = context.user_data.get("last_search_results", GAMES_CATALOG)
        await safe_edit(update, "🔍 *RESULTADOS DA BUSCA*",
                        catalog_keyboard(page, results, prefix="search_res"))
    elif data == "categories":
        await show_categories(update, context)
    elif data.startswith("catpage_"):
        parts = data.split("_")
        tipo = "_".join(parts[1:-1])
        page = int(parts[-1])
        await show_category(update, context, tipo, page)
    elif data.startswith("cat_"):
        await show_category(update, context, data[len("cat_"):], 0)
    elif data.startswith("game_"):
        await show_game_detail(update, context, int(data.split("_")[1]))
    elif data == "cart":
        await show_cart(update, context)
    elif data.startswith("remove_"):
        await remove_from_cart(update, context, int(data.split("_")[1]))
    elif data.startswith("add_cart_"):
        await add_to_cart(update, context, int(data.split("_")[2]))
    elif data.startswith("buy_now_"):
        await buy_now(update, context, int(data.split("_")[2]))
    elif data == "checkout":
        await start_checkout(update, context)
    elif data.startswith("pay_"):
        await process_payment(update, context, data.split("_")[1])
    elif data.startswith("confirm_payment_"):
        await confirm_payment(update, context, data[len("confirm_payment_"):])
    elif data == "institutional":
        await show_institutional(update, context)
    elif data.startswith("inst_"):
        await institutional_detail(update, context, data[len("inst_"):])
    elif data == "support":
        await show_support(update, context)
    elif data == "faq":
        await show_faq(update, context)
    elif data == "my_orders":
        await show_orders(update, context)
    elif data == "my_profile":
        await show_profile(update, context)
    elif data == "update_profile":
        await iniciar_cadastro(update, context, "profile")
    elif data == "noop":
        pass

# ===================== CICLO DE VIDA =====================
async def main():
    global _app
    print("=" * 60)
    print("🎮 WareArcadeBot - Ware Arcade Game")
    print("💾 Persistência: SQLite (warearcade.db)")
    print(f"💳 Pagamento PIX: {pay.PROVIDER}")
    print("=" * 60)
    print(f"✅ Token: {TOKEN[:15]}...")
    print(f"📦 Catálogo: {len(GAMES_CATALOG)} produtos | 📂 {len(TIPOS)} categorias")
    print(f"👑 Admins: {ADMIN_IDS or 'Nenhum'}")
    print(f"🏢 Empresa: {EMPRESA['nome']}")
    print(f"💚 PIX (chave): {EMPRESA['pix']}")

    # Inicia webhook server em background
    await pay.start_webhook_server()

    # Configura timeouts maiores para evitar "Timed out" ao enviar fotos grandes
    trequest = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=30.0,
    )
    app = Application.builder().token(TOKEN).request(trequest).build()
    _app = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("cadastro", cmd_cadastro))
    app.add_handler(CommandHandler("feedback", cmd_feedback))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("pendentes", cmd_pendentes))
    app.add_handler(CommandHandler("aprovar", cmd_aprovar))
    app.add_handler(CommandHandler("rejeitar", cmd_rejeitar))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("🚀 Bot rodando! Ctrl+C para parar.")
    print("=" * 60)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

# -*- coding: utf-8 -*-
"""
===============================================
WareArcadeBot - Nexus Digital Shop
Versão: 4.0 - COMPLETA E CORRIGIDA
===============================================
"""

import os
import sys
import logging
import asyncio
import math
import uuid
import hashlib
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden

# ===== IMPORTAÇÕES LOCAIS =====
from config import (
    TELEGRAM_BOT_TOKEN, PORT, WEBHOOK_URL,
    EMPRESA, ADMIN_IDS, DOWNLOAD_BASE_URL, DOWNLOAD_EXPIRY_HOURS,
    STORE_NAME, STORE_EMAIL, STORE_WHATSAPP, STORE_INSTAGRAM, STORE_HOURS,
    ITEMS_PER_PAGE
)
from catalog import (
    GAMES_CATALOG, get_game_by_id, search_games, get_offers,
    get_total_produtos, get_total_ofertas
)

load_dotenv()

# ===== CONFIGURAÇÕES =====
TOKEN = TELEGRAM_BOT_TOKEN

if not TOKEN:
    print("❌ TOKEN NÃO ENCONTRADO!")
    print("   Configure TELEGRAM_BOT_TOKEN no arquivo .env")
    sys.exit(1)

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== BANCO DE DADOS EM MEMÓRIA =====
carrinhos = {}
pedidos = {}
pedidos_pendentes = {}
downloads_liberados = {}
cadastros = {}
ordens = 0

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def gerar_codigo_pedido():
    global ordens
    ordens += 1
    return f"WA-{ordens:06d}"

def gerar_token_download():
    return hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()[:32]

def gerar_link_download(codigo_pedido):
    token = gerar_token_download()
    return f"{DOWNLOAD_BASE_URL}{codigo_pedido}/{token}"

def validar_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validar_whatsapp(telefone):
    numero = re.sub(r'\D', '', telefone)
    return len(numero) >= 10 and len(numero) <= 13

def formatar_whatsapp(numero):
    numero = re.sub(r'\D', '', numero)
    if len(numero) == 11:
        return f"+{numero}"
    elif len(numero) == 10:
        return f"+55{numero}"
    return numero

# ============================================================
# KEYBOARDS
# ============================================================

def menu_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Ver Catálogo Completo", callback_data="catalog_0")],
        [InlineKeyboardButton("🔥 Ofertas Imperdíveis", callback_data="offers_0"),
         InlineKeyboardButton("🔍 Buscar Produto", callback_data="search")],
        [InlineKeyboardButton("📂 Categorias", callback_data="categories"),
         InlineKeyboardButton("🛒 Meu Carrinho", callback_data="cart")],
        [InlineKeyboardButton("📦 Meus Pedidos", callback_data="my_orders"),
         InlineKeyboardButton("👤 Meu Cadastro", callback_data="my_profile")],
        [InlineKeyboardButton("🏛️ Institucional", callback_data="institutional"),
         InlineKeyboardButton("💬 Suporte", callback_data="support")],
    ])

def voltar_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
    ])

def catalog_keyboard(page, games, prefix="catalog"):
    if not games:
        return InlineKeyboardMarkup([[InlineKeyboardButton("📭 Nenhum produto", callback_data="noop")]])
    
    total_pages = max(1, math.ceil(len(games) / ITEMS_PER_PAGE))
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_games = games[start_idx:end_idx]

    keyboard = []
    for game in page_games:
        tag = " 🔥" if game.get("oferta", False) else ""
        nome = game["nome"][:30] + "..." if len(game["nome"]) > 30 else game["nome"]
        btn_text = f"🎮 {nome} - R$ {game['preco_oferta']:.2f}{tag}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"game_{game['id']}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"{prefix}_{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ Próximo", callback_data=f"{prefix}_{page + 1}"))
    keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔍 Buscar Produto", callback_data="search_product")])
    keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)

def game_detail_keyboard(game_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Adicionar ao Carrinho", callback_data=f"add_cart_{game_id}")],
        [InlineKeyboardButton("⚡ Comprar Agora", callback_data=f"buy_now_{game_id}")],
        [InlineKeyboardButton("🔙 Voltar ao Catálogo", callback_data="catalog_0")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 PIX (Imediato)", callback_data="pay_pix")],
        [InlineKeyboardButton("💳 Cartão de Crédito", callback_data="pay_cartao")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")],
    ])

# ============================================================
# HANDLERS - COMANDOS PRINCIPAIS
# ============================================================

async def start(update, context):
    """Comando /start - Inicia o bot"""
    user = update.effective_user
    total = get_total_produtos()
    ofertas = get_total_ofertas()

    welcome = (
        f"🏪 *{STORE_NAME}*\n\n"
        f"Olá, *{user.first_name}*! 😊\n\n"
        f"## CATÁLOGO COMPLETO - {total} PRODUTOS\n\n"
        f"- 🎮 Jogos ...... 157\n"
        f"- 🎓 Cursos ...... 36\n"
        f"- 🎨 Design ...... 11\n"
        f"- 🤖 IA ...... 40\n"
        f"- 🔧 Ferramentas ...... 20\n"
        f"- 🖥️ Sistemas ...... 8\n"
        f"- 🎬 Vídeo ...... 8\n"
        f"- 🔒 Segurança ...... 8\n"
        f"- 📄 Office ...... 7\n"
        f"- 📺 Streaming ...... 7\n"
        f"- 🏗️ Engenharia ...... 6\n"
        f"- 🎁 Gift Cards ...... 6\n"
        f"- 🎵 Música ...... 3\n"
        f"- ☁️ Cloud ...... 3\n"
        f"- 🧪 Teste ...... 1\n\n"
        f"---\n\n"
        f"## INFORMAÇÕES:\n"
        f"- 📦 Total: {total} produtos\n"
        f"- 🔥 Em oferta: {ofertas} produtos\n"
        f"- 💰 Faixa: R$ 1.50 a R$ 499.90\n\n"
        f"---\n\n"
        f"### ⚡ Entrega imediata | 🔒 100% Seguro\n"
        f"- 💚 PIX | 💳 Cartão | 📄 Boleto\n\n"
        f"## Escolha uma opção:"
    )

    if update.message:
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=menu_principal())
    else:
        await update.callback_query.edit_message_text(welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=menu_principal())

async def show_catalog(update, context, page=0):
    """Exibe o catálogo paginado"""
    await update.callback_query.edit_message_text(
        "📚 *CATÁLOGO COMPLETO*\n\nSelecione um produto:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=catalog_keyboard(page, GAMES_CATALOG)
    )

async def show_offers(update, context, page=0):
    """Exibe produtos em oferta"""
    offers = get_offers()
    if not offers:
        await update.callback_query.edit_message_text(
            "🔥 Nenhuma oferta no momento.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=voltar_menu()
        )
        return
    await update.callback_query.edit_message_text(
        "🔥 *OFERTAS IMPERDÍVEIS!*\n\nConfira os descontos:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=catalog_keyboard(page, offers, prefix="offers")
    )

async def show_categories(update, context):
    """Exibe categorias"""
    text = (
        "📂 *CATEGORIAS*\n\n"
        "Escolha uma categoria:\n\n"
        "🎮 Jogos PC (157)\n"
        "🎓 Cursos (36)\n"
        "🎨 Design (11)\n"
        "🤖 IA - Ferramenta (11)\n"
        "🔧 Ferramenta (9)\n"
        "🖥️ Sistema (8)\n"
        "🎬 Vídeo (8)\n"
        "🔒 Segurança (8)\n"
        "📄 Office (7)\n"
        "📺 Streaming (7)\n"
        "🏗️ Engenharia (6)\n"
        "🎁 Gift Card (6)\n"
        "🎵 Música (3)\n"
        "☁️ Cloud (3)\n\n"
        "📌 *Use /start para ver todos os produtos*"
    )
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=voltar_menu())

async def search_product_click(update, context):
    """Inicia busca"""
    context.user_data["searching"] = True
    await update.callback_query.edit_message_text(
        "🔍 *Buscar Produto*\n\nDigite o nome do produto:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]
        ])
    )

async def handle_user_message(update, context):
    """Processa mensagens do usuário (busca)"""
    if context.user_data.get("searching", False):
        context.user_data["searching"] = False
        query = update.message.text
        results = search_games(query)

        if not results:
            await update.message.reply_text(
                f"❌ Nenhum produto encontrado para: *{query}*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=voltar_menu()
            )
            return

        await update.message.reply_text(
            f"🔍 *Resultados para:* '{query}'\nEncontramos {len(results)} produto(s):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=catalog_keyboard(0, results, prefix="search_res")
        )

# ============================================================
# HANDLERS - DETALHES DO PRODUTO
# ============================================================

async def show_game_detail(update, context, game_id):
    """Exibe detalhes de um produto com imagem"""
    game = get_game_by_id(game_id)
    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    nome = game["nome"]
    preco = game["preco_oferta"]
    preco_orig = game.get("preco_original", preco)

    if game.get("oferta", False) and preco_orig != preco:
        desconto = int((1 - preco / preco_orig) * 100)
        preco_text = f"De R$ {preco_orig:.2f} por R$ {preco:.2f} ({desconto}% OFF)"
    else:
        preco_text = f"R$ {preco:.2f}"

    text = (
        f"🎮 *{nome}*\n\n"
        f"💰 {preco_text}\n"
        f"🖥️ Plataforma: {game.get('plataforma', 'PC')}\n"
        f"📂 Categorias: {', '.join(game.get('categorias', []))}\n\n"
        f"📝 {game.get('descricao', '')}\n\n"
        f"---\n\n"
        f"✅ Entrega digital imediata\n"
        f"🔒 Pagamento 100% seguro\n"
        f"⏳ Link válido por 48h"
    )

    try:
        await update.callback_query.message.delete()
    except:
        pass

    imagem_url = game.get("imagem_url", "")
    if imagem_url and imagem_url.startswith("http"):
        try:
            await context.bot.send_photo(
                chat_id=update.callback_query.message.chat_id,
                photo=imagem_url,
                caption=text,
                reply_markup=game_detail_keyboard(game_id)
            )
            return
        except Exception as e:
            logger.warning(f"Erro na imagem: {e}")

    await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=text,
        reply_markup=game_detail_keyboard(game_id)
    )

# ============================================================
# HANDLERS - CARRINHO
# ============================================================

async def show_cart(update, context):
    """Exibe o carrinho"""
    user_id = update.callback_query.from_user.id
    cart = carrinhos.get(user_id, [])

    if not cart:
        await update.callback_query.edit_message_text(
            "🛒 *Meu Carrinho*\n\nSeu carrinho está vazio!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=voltar_menu()
        )
        return

    total = sum(item["preco"] for item in cart)
    text = "🛒 *SEU CARRINHO*\n\n"
    keyboard = []

    for i, item in enumerate(cart, 1):
        text += f"{i}. {item['nome']} - R$ {item['preco']:.2f}\n"
        keyboard.append([InlineKeyboardButton(f"❌ Remover #{i}", callback_data=f"remove_{i-1}")])

    text += f"\n💰 *Total: R$ {total:.2f}*"
    keyboard.append([InlineKeyboardButton("💰 Finalizar Compra", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])

    await update.callback_query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_to_cart(update, context, game_id):
    """Adiciona produto ao carrinho"""
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)

    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    if user_id not in carrinhos:
        carrinhos[user_id] = []

    carrinhos[user_id].append({
        "id": game_id,
        "nome": game["nome"],
        "preco": game["preco_oferta"]
    })

    await update.callback_query.answer(f"✅ {game['nome']} adicionado ao carrinho!")

    await update.callback_query.edit_message_text(
        f"✅ *{game['nome']}* adicionado ao carrinho!\n\n"
        f"💰 R$ {game['preco_oferta']:.2f}\n\n"
        f"O que deseja fazer?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Ver Carrinho", callback_data="cart")],
            [InlineKeyboardButton("📚 Continuar Comprando", callback_data="catalog_0")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ])
    )

async def buy_now(update, context, game_id):
    """Compra direta"""
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)

    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    carrinhos[user_id] = [{"id": game_id, "nome": game["nome"], "preco": game["preco_oferta"]}]
    await start_checkout(update, context)

async def remove_from_cart(update, context):
    """Remove item do carrinho"""
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    idx = int(data.split("_")[1])

    if user_id in carrinhos and 0 <= idx < len(carrinhos[user_id]):
        del carrinhos[user_id][idx]

    await show_cart(update, context)

# ============================================================
# HANDLERS - CHECKOUT E PAGAMENTO
# ============================================================

async def start_checkout(update, context):
    """Inicia checkout"""
    user_id = update.callback_query.from_user.id
    cart = carrinhos.get(user_id, [])

    if not cart:
        await update.callback_query.answer("🛒 Carrinho vazio!")
        return

    total = sum(item["preco"] for item in cart)
    text = "💳 *FINALIZAR COMPRA*\n\n"

    for item in cart:
        text += f"🎮 {item['nome']} - R$ {item['preco']:.2f}\n"

    text += f"\n💰 *TOTAL: R$ {total:.2f}*\n\n*Selecione o pagamento:*"

    await update.callback_query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=payment_keyboard()
    )

async def process_payment(update, context, method):
    """Processa pagamento"""
    user_id = update.callback_query.from_user.id
    cart = carrinhos.get(user_id, [])
    total = sum(item["preco"] for item in cart)

    if not cart:
        await update.callback_query.answer("🛒 Carrinho vazio!")
        return

    codigo_pedido = gerar_c
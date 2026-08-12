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
import database as db

load_dotenv()

# ===== CONFIGURAÇÕES =====
TOKEN = TELEGRAM_BOT_TOKEN

if not TOKEN or TOKEN == "SEU_TOKEN_AQUI":
    print("❌ TOKEN NÃO ENCONTRADO!")
    print("   Configure TELEGRAM_BOT_TOKEN no arquivo .env")
    sys.exit(1)

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== INICIALIZA BANCO DE DADOS PERSISTENTE =====
db.init_db()
db.carregar_tudo_para_memoria()

carrinhos = db.carrinhos_mem
pedidos = db.pedidos_mem
pedidos_pendentes = db.pedidos_pendentes_mem
downloads_liberados = {}
cadastros = db.cadastros_mem

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def gerar_codigo_pedido():
    return db.next_codigo()

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
    return f"+{numero}" if not numero.startswith("+") else numero

async def safe_edit_or_send(query, context, text, parse_mode=ParseMode.MARKDOWN, reply_markup=None):
    """Tenta editar a mensagem; se for foto (BadRequest), deleta e envia nova."""
    try:
        await query.edit_message_text(
            text, parse_mode=parse_mode, reply_markup=reply_markup
        )
    except BadRequest:
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text, parse_mode=parse_mode, reply_markup=reply_markup
        )

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
        await safe_edit_or_send(update.callback_query, context, welcome, reply_markup=menu_principal())

async def show_catalog(update, context, page=0):
    """Exibe o catálogo paginado"""
    await safe_edit_or_send(
        update.callback_query, context,
        "📚 *CATÁLOGO COMPLETO*\n\nSelecione um produto:",
        reply_markup=catalog_keyboard(page, GAMES_CATALOG)
    )

async def show_offers(update, context, page=0):
    """Exibe produtos em oferta"""
    offers = get_offers()
    if not offers:
        await safe_edit_or_send(
            update.callback_query, context,
            "🔥 Nenhuma oferta no momento.",
            reply_markup=voltar_menu()
        )
        return
    await safe_edit_or_send(
        update.callback_query, context,
        "🔥 *OFERTAS IMPERDÍVEIS!*\n\nConfira os descontos:",
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
    await safe_edit_or_send(update.callback_query, context, text, reply_markup=voltar_menu())

async def search_product_click(update, context):
    """Inicia busca"""
    context.user_data["searching"] = True
    await safe_edit_or_send(
        update.callback_query, context,
        "🔍 *Buscar Produto*\n\nDigite o nome do produto:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]
        ])
    )

async def handle_user_message(update, context):
    """Processa mensagens do usuário (busca e cadastro)"""
    if context.user_data.get("cadastro_passo"):
        await processar_cadastro(update, context)
        return

    if context.user_data.get("searching", False):
        context.user_data["searching"] = False
        query = update.message.text
        results = search_games(query)
        context.user_data["last_search_results"] = results

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
    except Exception:
        pass

    imagem_url = game.get("imagem_url", "")
    if imagem_url and imagem_url.startswith("http"):
        try:
            await context.bot.send_photo(
                chat_id=update.callback_query.message.chat_id,
                photo=imagem_url,
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=game_detail_keyboard(game_id)
            )
            return
        except Exception as e:
            logger.warning(f"Erro na imagem: {e}")

    await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=game_detail_keyboard(game_id)
    )

# ============================================================
# HANDLERS - CARRINHO
# ============================================================

async def show_cart(update, context):
    """Exibe o carrinho"""
    user_id = update.callback_query.from_user.id
    cart = db.get_cart(user_id)

    if not cart:
        await safe_edit_or_send(
            update.callback_query, context,
            "🛒 *Meu Carrinho*\n\nSeu carrinho está vazio!",
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

    await safe_edit_or_send(
        update.callback_query, context, text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_to_cart(update, context, game_id):
    """Adiciona produto ao carrinho"""
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)

    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    db.add_to_cart(user_id, game_id, game["nome"], game["preco_oferta"])

    await update.callback_query.answer(f"✅ {game['nome']} adicionado ao carrinho!")

    add_text = (
        f"✅ *{game['nome']}* adicionado ao carrinho!\n\n"
        f"💰 R$ {game['preco_oferta']:.2f}\n\n"
        f"O que deseja fazer?"
    )
    add_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ver Carrinho", callback_data="cart")],
        [InlineKeyboardButton("📚 Continuar Comprando", callback_data="catalog_0")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
    ])
    await safe_edit_or_send(
        update.callback_query, context, add_text,
        reply_markup=add_markup
    )

async def buy_now(update, context, game_id):
    """Compra direta"""
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)

    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    db.clear_cart(user_id)
    db.add_to_cart(user_id, game_id, game["nome"], game["preco_oferta"])
    await start_checkout(update, context)

async def remove_from_cart(update, context):
    """Remove item do carrinho"""
    user_id = update.callback_query.from_user.id
    data = update.callback_query.data
    idx = int(data.split("_")[1])

    db.remove_from_cart(user_id, idx)
    await show_cart(update, context)

# ============================================================
# HANDLERS - CHECKOUT E PAGAMENTO
# ============================================================

async def start_checkout(update, context):
    """Inicia checkout"""
    user_id = update.callback_query.from_user.id
    cart = db.get_cart(user_id)

    if not cart:
        await update.callback_query.answer("🛒 Carrinho vazio!")
        return

    total = sum(item["preco"] for item in cart)
    text = "💳 *FINALIZAR COMPRA*\n\n"

    for item in cart:
        text += f"🎮 {item['nome']} - R$ {item['preco']:.2f}\n"

    text += f"\n💰 *TOTAL: R$ {total:.2f}*\n\n*Selecione o pagamento:*"

    await safe_edit_or_send(
        update.callback_query, context, text,
        reply_markup=payment_keyboard()
    )

async def process_payment(update, context, method):
    """Processa pagamento"""
    user_id = update.callback_query.from_user.id
    cart = db.get_cart(user_id)
    total = sum(item["preco"] for item in cart)

    if not cart:
        await update.callback_query.answer("🛒 Carrinho vazio!")
        return

    codigo_pedido = gerar_codigo_pedido()

    pedido = {
        "codigo": codigo_pedido,
        "user_id": user_id,
        "itens": cart.copy(),
        "total": total,
        "metodo": method,
        "status": "pendente",
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": db.get_cadastro(user_id) or {}
    }

    db.save_pedido(pedido)
    db.clear_cart(user_id)

    try:
        await update.callback_query.message.delete()
    except Exception:
        pass

    # Mensagem de pagamento
    text = (
        f"💚 *PAGAMENTO VIA PIX*\n\n"
        f"💰 *Valor: R$ {total:.2f}*\n"
        f"📋 *Pedido: `{codigo_pedido}`*\n\n"
        f"📱 *Chave PIX (CNPJ):*\n"
        f"`{EMPRESA['pix']}`\n\n"
        f"📛 *Nome:* {EMPRESA['nome']}\n"
        f"🏦 *Banco:* {EMPRESA['banco']}\n"
        f"🏦 *Agência:* {EMPRESA['agencia']}\n"
        f"💳 *Conta:* {EMPRESA['conta']}\n\n"
        f"📝 *Como pagar:*\n"
        f"1️⃣ Copie a chave PIX acima\n"
        f"2️⃣ Abra o app do seu banco\n"
        f"3️⃣ Cole a chave e confirme o valor\n"
        f"4️⃣ Após pagar, clique em *'✅ Já Paguei'*\n\n"
        f"⏳ *Aguardando pagamento...*"
    )

    await context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Já Paguei", callback_data=f"confirm_payment_{codigo_pedido}")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]
        ])
    )

async def confirm_payment(update, context, codigo_pedido):
    """Confirma pagamento e libera download"""
    user_id = update.callback_query.from_user.id
    pedido = db.carregar_pedido(codigo_pedido)

    if not pedido:
        await update.callback_query.answer("❌ Pedido não encontrado!")
        return

    # Gera link de download
    link_download = gerar_link_download(codigo_pedido)
    expira = (datetime.now() + timedelta(hours=DOWNLOAD_EXPIRY_HOURS)).strftime("%d/%m/%Y %H:%M")

    db.update_pedido(codigo_pedido, "aprovado", link_download=link_download)

    downloads_liberados[codigo_pedido] = {
        "link": link_download,
        "expira": expira,
        "itens": pedido["itens"],
        "user_id": user_id
    }

    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")

    # Mensagem de confirmação com link
    msg = (
        f"🎉 *DOWNLOAD LIBERADO!*\n\n"
        f"Olá, *{nome_cliente}*! 🚀\n\n"
        f"✅ Seu pedido foi *confirmado com sucesso*!\n"
        f"📋 *Código:* `{codigo_pedido}`\n"
        f"💰 *Total:* R$ {pedido['total']:.2f}\n\n"
        f"⬇️ *Clique no link abaixo para baixar:*\n"
        f"🔗 `{link_download}`\n\n"
        f"⏳ *Link válido até:* {expira}\n\n"
        f"🔒 *Download 100% seguro*\n\n"
        f"---\n\n"
        f"📌 *IMPORTANTE:*\n"
        f"✅ Faça o download o quanto antes\n"
        f"✅ O link expira em {DOWNLOAD_EXPIRY_HOURS} horas\n"
        f"✅ Se tiver problemas, fale com o suporte"
    )

    await safe_edit_or_send(
        update.callback_query, context, msg,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬇️ Baixar Agora", url=link_download)],
            [InlineKeyboardButton("💬 Suporte", callback_data="support")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ])
    )

    # Notifica admin se houver
    if ADMIN_IDS:
        admin_text = (
            f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
            f"📋 Código: {codigo_pedido}\n"
            f"👤 Usuário: {user_id}\n"
            f"💰 Total: R$ {pedido['total']:.2f}\n"
            f"🔗 Link: {link_download}\n"
            f"⏳ Expira: {expira}"
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass

# ============================================================
# HANDLERS - PEDIDOS E PERFIL
# ============================================================

async def show_orders(update, context):
    """Exibe pedidos do usuário"""
    user_id = update.callback_query.from_user.id
    user_pedidos = db.get_pedidos_usuario(user_id, limit=5)

    if not user_pedidos:
        await safe_edit_or_send(
            update.callback_query, context,
            "📦 *Meus Pedidos*\n\nVocê ainda não realizou nenhum pedido.",
            reply_markup=voltar_menu()
        )
        return

    text = "📦 *MEUS PEDIDOS*\n\n"
    for p in user_pedidos:
        status_emoji = "✅" if p.get("status") == "aprovado" else "⏳"
        text += f"{status_emoji} *Código:* `{p['codigo']}`\n"
        if p.get('itens'):
            text += f"   {p['itens'][0]['nome']}"
            if len(p['itens']) > 1:
                text += f" +{len(p['itens'])-1} itens"
        text += f"\n   💰 R$ {p['total']:.2f} | {p['status'].upper()}\n"
        text += f"   📅 {p.get('data', '')}\n\n"

    await safe_edit_or_send(update.callback_query, context, text, reply_markup=voltar_menu())

async def show_profile(update, context):
    """Exibe perfil do usuário"""
    user = update.callback_query.from_user
    dados = db.get_cadastro(user.id) or {}

    text = (
        f"👤 *MEU CADASTRO*\n\n"
        f"📛 Nome: {dados.get('nome', user.first_name)}\n"
        f"📧 Email: {dados.get('email', 'Não informado')}\n"
        f"📱 WhatsApp: {dados.get('whatsapp', 'Não informado')}\n"
        f"🔹 Telegram: @{user.username or 'Não informado'}\n"
        f"🆔 ID: {user.id}\n\n"
        f"📅 Cadastro: {datetime.now().strftime('%d/%m/%Y')}\n\n"
        f"🔒 Seus dados estão seguros!"
    )

    await safe_edit_or_send(
        update.callback_query, context, text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Atualizar Cadastro", callback_data="update_profile")],
            [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
        ])
    )

async def update_profile(update, context):
    """Inicia atualização de cadastro"""
    await iniciar_cadastro(update, context, "profile")

# ============================================================
# HANDLERS - CADASTRO
# ============================================================

async def iniciar_cadastro(update, context, redirect_to=None):
    """Inicia cadastro do cliente"""
    context.user_data["cadastro"] = {"redirect": redirect_to}
    context.user_data["cadastro_passo"] = "nome"

    await safe_edit_or_send(
        update.callback_query, context,
        "📝 *CADASTRO DO CLIENTE*\n\n"
        "Para finalizar sua compra, precisamos de alguns dados.\n\n"
        "🔒 *Seus dados estão seguros!*\n"
        "✅ Protegidos pela LGPD\n\n"
        "*Digite seu nome completo:*"
    )

async def processar_cadastro(update, context):
    """Processa cadastro do cliente"""
    user_id = update.effective_user.id
    text = update.message.text
    passo = context.user_data.get("cadastro_passo", "nome")
    dados = context.user_data.get("cadastro", {})

    if passo == "nome":
        dados["nome"] = text
        context.user_data["cadastro"] = dados
        context.user_data["cadastro_passo"] = "email"
        await update.message.reply_text(
            f"✅ Nome salvo: *{text}*\n\n📧 Agora digite seu *email*:",
            parse_mode=ParseMode.MARKDOWN
        )

    elif passo == "email":
        if not validar_email(text):
            await update.message.reply_text("❌ Email inválido! Digite um email válido:")
            return
        dados["email"] = text
        context.user_data["cadastro"] = dados
        context.user_data["cadastro_passo"] = "whatsapp"
        await update.message.reply_text(
            f"✅ Email salvo: *{text}*\n\n📱 Agora digite seu *WhatsApp* com DDD:",
            parse_mode=ParseMode.MARKDOWN
        )

    elif passo == "whatsapp":
        numero = re.sub(r'\D', '', text)
        if len(numero) < 10:
            await update.message.reply_text("❌ Número inválido! Digite com DDD (ex: 11999999999):")
            return

        dados["whatsapp"] = formatar_whatsapp(numero)
        db.save_cadastro(user_id, dados)
        context.user_data["cadastro"] = {}
        context.user_data["cadastro_passo"] = None

        await update.message.reply_text(
            f"✅ *Cadastro completo!*\n\n"
            f"📛 Nome: {dados['nome']}\n"
            f"📧 Email: {dados['email']}\n"
            f"📱 WhatsApp: {dados['whatsapp']}\n\n"
            f"🔒 Seus dados estão seguros!\n\n"
            f"📦 Seu pedido será processado...",
            parse_mode=ParseMode.MARKDOWN
        )

async def cmd_cadastro(update, context):
    """Comando /cadastro"""
    context.user_data["cadastro"] = {}
    context.user_data["cadastro_passo"] = "nome"
    await update.message.reply_text(
        "📝 *CADASTRO DO CLIENTE*\n\nDigite seu *nome completo*:",
        parse_mode=ParseMode.MARKDOWN
    )

# ============================================================
# HANDLERS - INSTITUCIONAL E SUPORTE
# ============================================================

async def show_institutional(update, context):
    """Exibe institucional"""
    text = (
        "🏛️ *INSTITUCIONAL - WareArcadeBot*\n\n"
        "Conheça nossa loja e políticas.\n"
        "Sua segurança é prioridade!\n\n"
        "---\n\n"
        "📖 *SOBRE NÓS*\n"
        "Somos a maior loja digital do Telegram! 🚀\n\n"
        "✅ +2.500 clientes satisfeitos\n"
        "✅ 321 produtos disponíveis\n"
        "✅ Entrega imediata 100%\n\n"
        "---\n\n"
        "🔒 *PRIVACIDADE*\n"
        "✅ Dados protegidos pela LGPD\n"
        "✅ Não armazenamos cartões\n"
        "✅ Nunca compartilhamos dados\n\n"
        "---\n\n"
        "🛡️ *GARANTIAS*\n"
        "✅ Produto original\n"
        "✅ Entrega imediata\n"
        "✅ Suporte humanizado\n"
        "✅ Melhor preço"
    )

    await safe_edit_or_send(update.callback_query, context, text, reply_markup=voltar_menu())

async def show_support(update, context):
    """Exibe suporte"""
    text = (
        "💬 *SUPORTE AO CLIENTE*\n\n"
        f"🏪 *{STORE_NAME}*\n\n"
        "*Fale conosco:*\n\n"
        f"📱 WhatsApp: {STORE_WHATSAPP}\n"
        f"📧 Email: {STORE_EMAIL}\n"
        f"📸 Instagram: {STORE_INSTAGRAM}\n"
        f"🕐 Horário: {STORE_HOURS}\n\n"
        "💚 *Atendimento humanizado!*\n"
        "Respondemos em até 30 minutos."
    )

    keyboard = [
        [InlineKeyboardButton("💬 Chamar no WhatsApp", url=f"https://wa.me/{STORE_WHATSAPP.replace('+', '')}")],
        [InlineKeyboardButton("📸 Seguir no Instagram", url="https://instagram.com/warearcadebot")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
    ]

    if update.callback_query:
        await safe_edit_or_send(
            update.callback_query, context, text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============================================================
# COMANDOS ADMIN
# ============================================================

async def cmd_admin(update, context):
    """Verifica se o usuário é admin"""
    user_id = update.effective_user.id

    if user_id in ADMIN_IDS:
        await update.message.reply_text(
            "👑 *ADMINISTRADOR VERIFICADO*\n\n"
            "✅ Você é um administrador!\n\n"
            "📋 *Comandos:*\n"
            "🔹 /admin - Verificar status\n"
            "🔹 /pendentes - Listar pedidos\n"
            "🔹 /aprovar CODIGO - Aprovar pedido\n"
            "🔹 /rejeitar CODIGO - Rejeitar pedido\n"
            "🔹 /liberar CODIGO - Liberar download\n\n"
            f"👤 Seu ID: {user_id}\n"
            f"👥 Admins: {len(ADMIN_IDS)}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            f"❌ *ACESSO NEGADO*\n\n"
            f"Você não é administrador!\n\n"
            f"Para ser admin, adicione no .env:\n"
            f"`ADMIN_CHAT_IDS={user_id}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def cmd_pendentes(update, context):
    """Lista pedidos pendentes"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return

    pendentes = db.get_pedidos_pendentes()

    if not pendentes:
        await update.message.reply_text("📋 *PEDIDOS PENDENTES*\n\n✅ Nenhum pedido pendente!", parse_mode=ParseMode.MARKDOWN)
        return

    text = "📋 *PEDIDOS PENDENTES*\n\n"
    for codigo, pedido in pendentes.items():
        cliente = pedido.get("cliente", {})
        text += f"🔹 *{codigo}* - R$ {pedido['total']:.2f}\n"
        text += f"   👤 {cliente.get('nome', 'Não informado')}\n"
        text += f"   📦 {len(pedido.get('itens', []))} itens\n"
        text += f"   ⏳ {pedido.get('data', '')}\n\n"

    text += "✅ Use: /aprovar CODIGO ou /liberar CODIGO"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def cmd_aprovar(update, context):
    """Aprova pedido e libera download"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📋 *APROVAR PEDIDO*\n\nUse: /aprovar CODIGO\nEx: /aprovar WA-000001",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    codigo = args[0].upper()
    pedido = db.carregar_pedido(codigo)

    if not pedido:
        await update.message.reply_text(f"❌ Pedido `{codigo}` não encontrado!")
        return

    link_download = gerar_link_download(codigo)
    expira = (datetime.now() + timedelta(hours=DOWNLOAD_EXPIRY_HOURS)).strftime("%d/%m/%Y %H:%M")

    db.update_pedido(codigo, "aprovado", link_download=link_download)

    downloads_liberados[codigo] = {
        "link": link_download,
        "expira": expira,
        "itens": pedido["itens"],
        "user_id": pedido["user_id"]
    }

    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")

    try:
        await context.bot.send_message(
            pedido["user_id"],
            f"🎉 *PEDIDO APROVADO!*\n\n"
            f"Olá, *{nome_cliente}*! 🚀\n\n"
            f"✅ Seu pedido foi *aprovado com sucesso*!\n"
            f"📋 *Código:* `{codigo}`\n\n"
            f"⬇️ *Seu link de download:*\n"
            f"🔗 `{link_download}`\n\n"
            f"⏳ *Link válido até:* {expira}\n\n"
            f"🔒 *Download 100% seguro*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬇️ Baixar Agora", url=link_download)],
                [InlineKeyboardButton("💬 Suporte", callback_data="support")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Erro ao notificar cliente: {e}")

    await update.message.reply_text(
        f"✅ *Pedido aprovado!*\n\n📋 Código: `{codigo}`\n👤 Cliente: {nome_cliente}\n🔗 Link: {link_download}",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_rejeitar(update, context):
    """Rejeita pedido"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📋 *REJEITAR PEDIDO*\n\nUse: /rejeitar CODIGO\nEx: /rejeitar WA-000001",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    codigo = args[0].upper()
    pedido = db.carregar_pedido(codigo)

    if not pedido:
        await update.message.reply_text(f"❌ Pedido `{codigo}` não encontrado!")
        return

    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")
    db.update_pedido(codigo, "rejeitado")

    try:
        await context.bot.send_message(
            pedido["user_id"],
            f"❌ *PEDIDO REJEITADO*\n\nOlá {nome_cliente}!\n\nSeu pedido `{codigo}` foi rejeitado.\n\n💬 Para mais informações, fale com nosso suporte.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Suporte", callback_data="support")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ])
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"❌ *Pedido rejeitado!*\n\n📋 Código: `{codigo}`\n👤 Cliente: {nome_cliente}",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_liberar(update, context):
    """Libera download sem aprovar"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Acesso negado!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "📋 *LIBERAR DOWNLOAD*\n\nUse: /liberar CODIGO\nEx: /liberar WA-000001",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    codigo = args[0].upper()
    pedido = db.carregar_pedido(codigo)

    if not pedido:
        await update.message.reply_text(f"❌ Pedido `{codigo}` não encontrado!")
        return

    link_download = gerar_link_download(codigo)
    expira = (datetime.now() + timedelta(hours=DOWNLOAD_EXPIRY_HOURS)).strftime("%d/%m/%Y %H:%M")

    db.update_pedido(codigo, "aprovado", link_download=link_download)

    downloads_liberados[codigo] = {
        "link": link_download,
        "expira": expira,
        "itens": pedido["itens"],
        "user_id": pedido["user_id"]
    }

    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")

    try:
        await context.bot.send_message(
            pedido["user_id"],
            f"🎉 *DOWNLOAD LIBERADO!*\n\n"
            f"Olá, *{nome_cliente}*! 🚀\n\n"
            f"✅ Seu download foi *liberado*!\n"
            f"📋 *Código:* `{codigo}`\n\n"
            f"⬇️ *Clique no link abaixo:*\n"
            f"🔗 `{link_download}`\n\n"
            f"⏳ *Link válido até:* {expira}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬇️ Baixar Agora", url=link_download)],
                [InlineKeyboardButton("💬 Suporte", callback_data="support")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ])
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ *Download liberado!*\n\n📋 Código: `{codigo}`\n👤 Cliente: {nome_cliente}\n🔗 Link: {link_download}",
        parse_mode=ParseMode.MARKDOWN
    )

# ============================================================
# CALLBACK PRINCIPAL
# ============================================================

async def button(update, context):
    """Gerenciador central de callbacks"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data

    # Menu principal
    if data == "main_menu":
        await start(update, context)

    # Catálogo
    elif data.startswith("catalog_"):
        page = int(data.split("_")[1])
        await show_catalog(update, context, page)

    # Ofertas
    elif data.startswith("offers_"):
        page = int(data.split("_")[1])
        await show_offers(update, context, page)

    # Busca
    elif data == "search" or data == "search_product":
        await search_product_click(update, context)

    elif data.startswith("search_res_"):
        page = int(data.split("_")[2])
        results = context.user_data.get("last_search_results", GAMES_CATALOG)
        await safe_edit_or_send(
            query, context,
            "🔍 *RESULTADOS DA BUSCA*",
            reply_markup=catalog_keyboard(page, results, prefix="search_res")
        )

    # Categorias
    elif data == "categories":
        await show_categories(update, context)

    # Detalhes do produto
    elif data.startswith("game_"):
        game_id = int(data.split("_")[1])
        await show_game_detail(update, context, game_id)

    # Carrinho
    elif data == "cart":
        await show_cart(update, context)

    elif data.startswith("remove_"):
        await remove_from_cart(update, context)

    elif data.startswith("add_cart_"):
        game_id = int(data.split("_")[2])
        await add_to_cart(update, context, game_id)

    elif data.startswith("buy_now_"):
        game_id = int(data.split("_")[2])
        await buy_now(update, context, game_id)

    elif data == "checkout":
        await start_checkout(update, context)

    # Pagamento
    elif data.startswith("pay_"):
        method = data.split("_")[1]
        await process_payment(update, context, method)

    elif data.startswith("confirm_payment_"):
        codigo = data.replace("confirm_payment_", "")
        await confirm_payment(update, context, codigo)

    # Pedidos e perfil
    elif data == "my_orders":
        await show_orders(update, context)

    elif data == "my_profile":
        await show_profile(update, context)

    elif data == "update_profile":
        await iniciar_cadastro(update, context, "profile")

    # Institucional e suporte
    elif data == "institutional":
        await show_institutional(update, context)

    elif data == "support":
        await show_support(update, context)

    elif data == "noop":
        pass

# ============================================================
# SERVIDORES E HEALTH CHECK PARA O RENDER
# ============================================================

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - WareArcadeBot is online!")

    def log_message(self, format, *args):
        pass  # Silencia logs repetitivos do Render health check

def start_health_check_server(port):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Servidor HTTP para Render (/health) ativo na porta {port}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Servidor HTTP: {e}")

# ============================================================
# MAIN - PONTO DE ENTRADA
# ============================================================

def main():
    """Função principal que inicia e mantém o bot rodando"""
    print("=" * 60)
    print("🎮 WareArcadeBot - NEXUS DIGITAL SHOP")
    print("=" * 60)
    print(f"📦 Catálogo: {len(GAMES_CATALOG)} produtos")
    print(f"🔥 Ofertas: {get_total_ofertas()} produtos")
    print(f"👑 Admins: {len(ADMIN_IDS)}")
    print(f"💚 PIX: {EMPRESA['pix']}")
    print("🚀 Bot iniciado e aguardando mensagens...")
    print("=" * 60)

    # Inicia servidor HTTP em background para responder ao Render health check
    t = threading.Thread(target=start_health_check_server, args=(PORT,), daemon=True)
    t.start()

    # Cria a aplicação
    app = Application.builder().token(TOKEN).build()

    # ===== COMANDOS =====
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("cadastro", cmd_cadastro))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # ===== COMANDOS ADMIN =====
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("pendentes", cmd_pendentes))
    app.add_handler(CommandHandler("aprovar", cmd_aprovar))
    app.add_handler(CommandHandler("rejeitar", cmd_rejeitar))
    app.add_handler(CommandHandler("liberar", cmd_liberar))

    # ===== MODO DE EXECUÇÃO =====
    if WEBHOOK_URL:
        print(f"✅ Webhook configurado: {WEBHOOK_URL}/webhook na porta {PORT}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    else:
        print("📡 Modo Polling (desenvolvimento/produção contínua)")
        # Inicia health‑check server em background
        t = threading.Thread(target=start_health_check_server, args=(PORT,), daemon=True)
        t.start()
        app.run_polling()

# ===== ENTRY POINT =====
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot parado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

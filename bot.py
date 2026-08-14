# -*- coding: utf-8 -*-
"""
===============================================
WareArcadeBot - Nexus Digital Shop
Versão: 4.0 - COMPLETA E CORRIGIDA
===============================================
"""

import os
import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import logging
import asyncio
import threading
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
import payments

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
        [InlineKeyboardButton("📚 Ver Catálogo", callback_data="catalog_0"),
         InlineKeyboardButton("🔥 Ofertas", callback_data="offers_0")],
        [InlineKeyboardButton("📂 Categorias", callback_data="categories"),
         InlineKeyboardButton("🔍 Buscar", callback_data="search")],
        [InlineKeyboardButton("🛒 Carrinho", callback_data="cart"),
         InlineKeyboardButton("📦 Pedidos", callback_data="my_orders")],
        [InlineKeyboardButton("👤 Cadastro", callback_data="my_profile"),
         InlineKeyboardButton("💬 Suporte VIP", callback_data="support")],
        [InlineKeyboardButton("🏛️ Conheça a Loja (Site)", callback_data="institutional")]
    ])

def voltar_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
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

    keyboard.append([
        InlineKeyboardButton("🔍 Buscar", callback_data="search_product"),
        InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

def game_detail_keyboard(game_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Adicionar", callback_data=f"add_cart_{game_id}"),
         InlineKeyboardButton("⚡ Comprar", callback_data=f"buy_now_{game_id}")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="catalog_0"),
         InlineKeyboardButton("🏠 Menu", callback_data="main_menu")],
    ])

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 PIX", callback_data="pay_pix"),
         InlineKeyboardButton("💳 Cartão", callback_data="pay_cartao")],
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
        f"🌟 Olá, *{user.first_name}*! Seja muito bem-vindo(a)!\n\n"
        f"💎 *EXPLORE NOSSO CATÁLOGO PREMIUM*\n"
        f"Temos *{total} produtos* de alto nível aguardando você, incluindo softwares essenciais, super lançamentos e ferramentas de ponta.\n\n"
        f"🔥 *OFERTAS ESPECIAIS:*\n"
        f"Existem hoje *{ofertas} produtos* com descontos limitados.\n\n"
        f"🚀 *NOSSOS DIFERENCIAIS:*\n"
        f"✅ Entrega Automática Imediata\n"
        f"✅ Catálogo 100% Original e Seguro\n"
        f"✅ Central de Concierge VIP\n\n"
        f"💸 *FORMAS DE PAGAMENTO:*\n"
        f"💚 PIX (Aprovação na hora)\n"
        f"💳 Cartão de Crédito ou Boleto\n\n"
        f"👇 *Selecione uma opção abaixo para começar:*"
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
    """Exibe categorias (Dinâmico)"""
    cat_counts = {}
    for game in GAMES_CATALOG:
        for cat in game.get("categorias", []):
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    
    keyboard = []
    row = []
    for cat, count in sorted_cats[:20]: # Top 20
        btn_text = f"📂 {cat} ({count})"
        # Para caber nos 64 bytes do callback_data: limitamos o tamanho do nome
        safe_cat = cat[:25]
        row.append(InlineKeyboardButton(btn_text, callback_data=f"cat_{safe_cat}_0"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")])

    await safe_edit_or_send(
        update.callback_query, context,
        "📂 *FILTRAR POR CATEGORIA*\n\nSelecione uma categoria abaixo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
        estoque_falso = (game_id % 3) + 1
        preco_text = (f"De ~R$ {preco_orig:.2f}~ por *R$ {preco:.2f}* ({desconto}% OFF)\n"
                      f"🚨 *ATENÇÃO: Restam apenas {estoque_falso} unidades!*")
    else:
        preco_text = f"*R$ {preco:.2f}*"

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

    # --- LÓGICA DE UP-SELL (COMPRE JUNTO) ---
    import random
    upsell_text = ""
    cart_nomes = [item['nome'] for item in cart]
    # Pega ofertas que ainda não estão no carrinho
    sugestoes = [g for g in get_offers() if g['nome'] not in cart_nomes]
    
    if sugestoes:
        upsell = random.choice(sugestoes)
        upsell_text = (f"\n\n🔥 *OFERTA RELÂMPAGO PARA VOCÊ:*\n"
                       f"Que tal levar também *{upsell['nome']}* por apenas R$ {upsell['preco_oferta']:.2f}?")
        # Botão de adicionar o upsell
        keyboard.append([InlineKeyboardButton(f"➕ Adicionar {upsell['nome'][:15]}...", callback_data=f"add_cart_{upsell['id']}")])

    text += f"\n💰 *Total da Compra: R$ {total:.2f}*{upsell_text}"
    keyboard.append([InlineKeyboardButton("💰 Finalizar Compra", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])

    await safe_edit_or_send(
        update.callback_query, context, text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def notificar_carrinho_abandonado(context, chat_id, user_id, nome_produto):
    # ==========================================
    # GATILHO 1: Escassez (Após 30 minutos)
    # ==========================================
    await asyncio.sleep(1800)  
    cart = db.get_cart(user_id)
    if not cart:
        context.user_data["cart_reminder_active"] = False
        return

    texto_urgencia = (
        f"🛒 *Opa! Você esqueceu algo no carrinho...*\n\n"
        f"Vi que você separou o *{nome_produto}*, mas não finalizou a compra.\n"
        f"🚨 *ATENÇÃO:* As ofertas promocionais esgotam rápido e seu carrinho será esvaziado em breve!\n\n"
        f"Quer finalizar agora e garantir o seu?"
    )
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=texto_urgencia, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Voltar ao Carrinho", callback_data="cart")]])
        )
    except:
        pass

    # ==========================================
    # GATILHO 2: Oferta Irrecusável (Após + 1.5 horas = 2 horas total)
    # ==========================================
    await asyncio.sleep(5400)
    cart = db.get_cart(user_id)
    if not cart:
        context.user_data["cart_reminder_active"] = False
        return
        
    texto_oferta = (
        f"🎁 *PRESENTE SURPRESA PARA VOCÊ!*\n\n"
        f"Como você é um cliente especial, o chefe liberou um desconto secreto para você levar o *{nome_produto}* HOJE!\n\n"
        f"💰 Mas seja rápido! Clique no botão abaixo para ver o desconto exclusivo direto no carrinho."
    )
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=texto_oferta, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔥 Pegar Meu Desconto VIP", callback_data="cart_desconto_vip")]])
        )
    except:
        pass
        
    context.user_data["cart_reminder_active"] = False

async def add_to_cart(update, context, game_id):
    """Adiciona produto ao carrinho"""
    user_id = update.callback_query.from_user.id
    game = get_game_by_id(game_id)

    if not game:
        await update.callback_query.answer("❌ Produto não encontrado!")
        return

    db.add_to_cart(user_id, game_id, game["nome"], game["preco_oferta"])

    # Dispara a tarefa silenciosa de carrinho abandonado se não houver uma rodando
    if not context.user_data.get("cart_reminder_active"):
        context.user_data["cart_reminder_active"] = True
        chat_id = update.callback_query.message.chat_id
        asyncio.create_task(notificar_carrinho_abandonado(context, chat_id, user_id, game['nome']))

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

    # ===== INTEGRAÇÃO PIX VIA PAYMENT PROVIDER =====
    await context.bot.send_message(chat_id=user_id, text="⏳ Gerando PIX... aguarde!")
    
    try:
        pix_data = await payments.gerar_qr_para_pedido(codigo_pedido, total)
    except Exception as e:
        logger.error(f"Erro ao gerar PIX: {e}")
        await context.bot.send_message(chat_id=user_id, text="❌ Falha ao gerar PIX. Tente novamente mais tarde.")
        return

    copia_cola = pix_data.get("qr_code_copia_cola") or EMPRESA['pix']

    text = (
        f"💚 *PAGAMENTO VIA PIX*\n\n"
        f"💰 *Valor: R$ {total:.2f}*\n"
        f"📋 *Pedido: `{codigo_pedido}`*\n\n"
        f"📱 *Copia e Cola:*\n"
        f"`{copia_cola}`\n\n"
        f"📝 *Como pagar:*\n"
        f"1️⃣ Copie o código acima ou escaneie o QR Code\n"
        f"2️⃣ Abra o app do seu banco\n"
        f"3️⃣ Confirme o valor e finalize o pagamento\n\n"
        f"⏳ O sistema aprovará automaticamente em instantes!"
    )

    botoes = [
        [InlineKeyboardButton("✅ Já Paguei (Forçar Baixa)", callback_data=f"confirm_payment_{codigo_pedido}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]
    ]

    if pix_data.get("buffer"):
        await context.bot.send_photo(
            chat_id=user_id,
            photo=pix_data["buffer"],
            caption=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(botoes)
        )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(botoes)
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

    # ===== INTEGRAÇÃO WHATSAPP OMNICHANNEL =====
    telefone_cliente = pedido.get("cliente", {}).get("whatsapp")
    if telefone_cliente:
        try:
            wa_token = os.getenv("WHATSAPP_API_TOKEN", "")
            wa_url = os.getenv("WHATSAPP_API_URL", "") # Ex: URL do Evolution API, Z-API, Zapier, Make
            
            if wa_token and wa_url:
                wa_payload = {
                    "number": telefone_cliente,
                    "text": msg.replace("*", "") # Mensagem limpa
                }
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        wa_url, 
                        json=wa_payload, 
                        headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
                    )
        except Exception as e:
            logger.warning(f"Erro ao enviar WhatsApp: {e}")
            
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
    """Exibe suporte VIP e links sociais"""
    import urllib.parse
    wa_msg = (
        "🚀 *Olá, Equipe de Elite!*\n\n"
        "Acabei de acessar o catálogo VIP pelo Bot 🤖 e exijo o meu atendimento prioritário! 🌟\n\n"
        "Tenho interesse em conhecer os bastidores, acessar os *descontos secretos* 🤫 e garantir a melhor solução para mim hoje.\n\n"
        "Vocês estão disponíveis? 💳🔥"
    )
    wa_link = f"https://wa.me/{STORE_WHATSAPP.replace('+', '')}?text={urllib.parse.quote(wa_msg)}"

    text = (
        "👑 *CENTRAL DE CONCIERGE VIP*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Você acaba de acessar o canal mais exclusivo da nossa operação. "
        "Não temos 'atendentes', temos *Especialistas de Elite* prontos para blindar sua compra e entregar a melhor experiência do mercado! 🚀⚡\n\n"
        "🔥 *Benefícios de Falar com a Gente:*\n"
        "💠 Acesso a Ofertas Secretas Privadas\n"
        "💠 Recomendações sob medida para você\n"
        "💠 Suporte Técnico Ultra-Rápido (SLA 30min)\n\n"
        "🛎️ *Seus Canais de Elite:*\n"
        f"🟢 *WhatsApp:* Canal direto com a nossa diretoria de vendas. Clique abaixo para prioridade máxima.\n"
        f"🌌 *Instagram:* `{STORE_INSTAGRAM}` — Siga para desbloquear Sorteios Relâmpago e Cupons Invisíveis! 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⌛ *Nossa equipe está online AGORA.*\n"
        "Toque no botão abaixo e sinta a diferença de um atendimento Premium. 👇"
    )

    keyboard = [
        [InlineKeyboardButton("💎 Falar no WhatsApp (VIP)", url=wa_link)],
        [InlineKeyboardButton("🌌 Desbloquear Cupons no Instagram", url="https://instagram.com/warearcadebot")],
        [InlineKeyboardButton("🏠 Voltar ao Menu", callback_data="main_menu")]
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

    elif data.startswith("cat_"):
        parts = data.split("_")
        page = int(parts[-1])
        cat_name = "_".join(parts[1:-1])
        
        # Filtra jogos que tenham a categoria
        results = [g for g in GAMES_CATALOG if any(cat_name in c for c in g.get("categorias", []))]
        
        await safe_edit_or_send(
            query, context,
            f"📂 *Categoria: {cat_name}*\n\nSelecione um produto:",
            reply_markup=catalog_keyboard(page, results, prefix=f"cat_{cat_name}")
        )

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
        
    elif data == "cart_desconto_vip":
        user_id = update.callback_query.from_user.id
        cart = db.get_cart(user_id)
        
        # Limpa o carrinho e readiciona os itens com 10% de desconto
        db.clear_cart(user_id)
        for item in cart:
            novo_preco = item["preco"] * 0.90 # 10% de desconto
            db.add_to_cart(user_id, item["id"], f"{item['nome']} (VIP 10% OFF)", novo_preco)
            
        await update.callback_query.answer("🎉 Desconto de 10% aplicado com sucesso!")
        await show_cart(update, context)

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

from payments import start_webhook_server
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
# WEBHOOK CALLBACK (APROVAÇÃO AUTOMÁTICA)
# ============================================================

@payments.on_payment_confirmed
async def on_webhook_payment(codigo_pedido: str, payload: dict):
    """Chamado automaticamente pelo payments.py quando o gateway aprovar o PIX"""
    pedido = db.carregar_pedido(codigo_pedido)
    if not pedido or pedido["status"] == "aprovado":
        return

    # Usa a mesma lógica de aprovação manual para reuso
    link_download = gerar_link_download(codigo_pedido)
    expira = (datetime.now() + timedelta(hours=DOWNLOAD_EXPIRY_HOURS)).strftime("%d/%m/%Y %H:%M")
    db.update_pedido(codigo_pedido, "aprovado", link_download=link_download)
    
    user_id = pedido["user_id"]
    nome_cliente = pedido.get("cliente", {}).get("nome", "Cliente")

    msg = (
        f"🎉 *DOWNLOAD LIBERADO (Aprovação Automática)!\n\n"
        f"Olá, *{nome_cliente}*! 🚀\n"
        f"✅ Seu pagamento foi *confirmado automaticamente*!\n"
        f"📋 *Código:* `{codigo_pedido}`\n"
        f"💰 *Total:* R$ {pedido['total']:.2f}\n\n"
        f"⬇️ *Clique no link abaixo para baixar:*\n"
        f"🔗 `{link_download}`\n\n"
        f"⏳ *Link válido até:* {expira}\n\n"
        f"🔒 *Download 100% seguro*"
    )

    if global_bot:
        try:
            await global_bot.send_message(
                chat_id=user_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬇️ Baixar Agora", url=link_download)],
                    [InlineKeyboardButton("💬 Suporte", callback_data="support")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ])
            )
        except Exception as e:
            logger.error(f"Erro ao enviar msg auto de pagamento: {e}")

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

    # Inicia o servidor de webhook/health check em background numa thread dedicada (compatível com Python 3.14+)
    def _run_webhook_thread():
        loop_wh = asyncio.new_event_loop()
        asyncio.set_event_loop(loop_wh)
        loop_wh.run_until_complete(start_webhook_server())
        loop_wh.run_forever()

    t_wh = threading.Thread(target=_run_webhook_thread, daemon=True)
    t_wh.start()

    # Cria a aplicação do Telegram
    app = Application.builder().token(TOKEN).build()
    
    global global_bot
    global_bot = app.bot

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
        # Configura webhook do Telegram
        print(f"✅ Webhook configurado: {WEBHOOK_URL}/webhook na porta {PORT}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    else:
        print("📡 Modo Polling (desenvolvimento/produção contínua)")
        app.run_polling()

# ===== ENTRY POINT =====
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot parado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

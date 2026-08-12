# -*- coding: utf-8 -*-
"""
WareArcadeBot - Integração de PAGAMENTO PIX automático
Implementa duas estratégias:
  1) Mercado Pago (recomendado, mais fácil no Brasil)
  2) Webhook genérico (qualquer gateway que mande POST JSON)

Variáveis de ambiente usadas:
  PAYMENT_PROVIDER        = "mercadopago" | "generic" | "manual"
  MERCADOPAGO_ACCESS_TOKEN= token de produção do Mercado Pago
  WEBHOOK_SECRET          = token secreto compartilhado para validar webhook genérico
  WEBHOOK_PATH            = caminho do webhook (padrão /webhook/pix)
  WEBHOOK_PORT            = porta do servidor HTTP (padrão 8000)
  PUBLIC_WEBHOOK_URL      = URL pública completa (para registrar no MP)
  DOWNLOAD_URL_TEMPLATE   = modelo de URL ex: https://warearcadebot.com.br/download/{codigo}
"""
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Awaitable

import aiohttp
from aiohttp import web

from qrcode_pix import generate_qr_code_pix, EMPRESA

log = logging.getLogger(__name__)

PROVIDER = os.getenv("PAYMENT_PROVIDER", "manual").lower()
MP_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook/pix")
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8000")))
PUBLIC_WEBHOOK_URL = os.getenv("PUBLIC_WEBHOOK_URL", "").rstrip("/") + WEBHOOK_PATH
DOWNLOAD_URL_TEMPLATE = os.getenv(
    "DOWNLOAD_URL_TEMPLATE",
    "https://warearcadebot.com.br/download/{codigo}",
)

# Callback chamado quando um pagamento é confirmado
# Recebe (codigo_pedido, payload)
_on_paid_callbacks: list[Callable[[str, dict], Awaitable[None]]] = []


def on_payment_confirmed(coro: Callable[[str, dict], Awaitable[None]]):
    """Registra um callback async para ser disparado quando um pedido for pago."""
    _on_paid_callbacks.append(coro)
    return coro


async def _dispatch_paid(codigo: str, payload: dict):
    for cb in _on_paid_callbacks:
        try:
            await cb(codigo, payload)
        except Exception as e:
            log.exception("Erro no callback de pagamento %s: %s", codigo, e)


# ===================== MERCADO PAGO =====================
async def criar_cobranca_mercadopago(codigo_pedido: str, valor: float, descricao: str = "Pedido WareArcade"):
    """Cria um PIX no Mercado Pago e retorna {qr_code, qr_code_base64, payment_id}."""
    if not MP_TOKEN:
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurado")

    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {MP_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": codigo_pedido,
    }
    body = {
        "transaction_amount": round(float(valor), 2),
        "description": f"{descricao} - {codigo_pedido}",
        "payment_method_id": "pix",
        "external_reference": codigo_pedido,
        "notification_url": PUBLIC_WEBHOOK_URL,
        "payer": {"email": "cliente@warearcadebot.com.br"},
        "date_of_expiration": (datetime.utcnow() + timedelta(minutes=30)).strftime(
            "%Y-%m-%dT%H:%M:%S.000-03:00"
        ),
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as r:
            data = await r.json()
            if r.status >= 400:
                log.error("Erro ao criar cobrança MP: %s", data)
                raise RuntimeError(f"Erro MP {r.status}: {data.get('message', data)}")
    pix = data.get("point_of_interaction", {}).get("transaction_data", {})
    return {
        "payment_id": str(data.get("id")),
        "qr_code": pix.get("qr_code_base64", ""),
        "qr_code_copia_cola": pix.get("qr_code", ""),
        "ticket_url": pix.get("ticket_url", ""),
        "status": data.get("status"),
    }


async def consultar_pagamento_mercadopago(payment_id: str):
    headers = {"Authorization": f"Bearer {MP_TOKEN}"}
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return None
            return await r.json()


# ===================== SYNC PAY =====================
async def criar_cobranca_syncpay(codigo_pedido: str, valor: float, descricao: str = "Pedido WareArcade"):
    """Cria um PIX via Sync Pay Pagamentos LTDA."""
    token = os.getenv("SYNCPAY_TOKEN", "").strip()
    if not token:
        raise RuntimeError("SYNCPAY_TOKEN não configurado")

    # Substitua pela URL real da documentação da Sync Pay
    url = "https://api.syncpay.com.br/v1/pix" 
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "value": round(float(valor), 2),
        "description": f"{descricao} - {codigo_pedido}",
        "external_id": codigo_pedido,
        "webhook_url": PUBLIC_WEBHOOK_URL
    }
    
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=body, headers=headers, timeout=15) as r:
            data = await r.json()
            if r.status >= 400:
                log.error("Erro ao criar PIX Sync Pay: %s", data)
                raise RuntimeError(f"Erro Sync Pay {r.status}: {data}")
                
    return {
        "payment_id": str(data.get("id")),
        "qr_code_copia_cola": data.get("pix_copia_cola", ""),
        "qr_code": data.get("qr_code_base64", "")
    }

# ===================== GERAR QR CODE PARA ENVIO =====================
async def gerar_qr_para_pedido(codigo_pedido: str, valor: float):
    """
    Gera o QR que será enviado ao cliente.
    Suporta: mercadopago, syncpay e manual.
    """
    meta = {
        "provider": PROVIDER,
        "payment_id": None,
        "qr_code_copia_cola": None,
        "usar_qr_mp_base64": False,
        "qr_base64": None,
    }

    if PROVIDER == "syncpay":
        try:
            sp = await criar_cobranca_syncpay(codigo_pedido, valor)
            meta["payment_id"] = sp["payment_id"]
            meta["qr_code_copia_cola"] = sp["qr_code_copia_cola"]
            meta["qr_base64"] = sp["qr_code"]
            meta["usar_qr_mp_base64"] = bool(sp["qr_code"])
            buffer, codigo = generate_qr_code_pix_com_texto(sp["qr_code_copia_cola"] or EMPRESA["pix"])
            meta["buffer"] = buffer
            meta["codigo_pix"] = codigo
            return meta
        except Exception as e:
            log.warning("Falha na Sync Pay, usando QR local: %s", e)

    elif PROVIDER == "mercadopago" and MP_TOKEN:
        try:
            mp = await criar_cobranca_mercadopago(codigo_pedido, valor)
            meta["payment_id"] = mp["payment_id"]
            meta["qr_code_copia_cola"] = mp["qr_code_copia_cola"]
            meta["qr_base64"] = mp["qr_code"]
            meta["usar_qr_mp_base64"] = True
            # Buffer: geramos QR local com o "copia e cola" do MP (melhor compatibilidade)
            buffer, codigo = generate_qr_code_pix_com_texto(mp["qr_code_copia_cola"] or EMPRESA["pix"])
            meta["buffer"] = buffer
            meta["codigo_pix"] = codigo
            return meta
        except Exception as e:
            log.warning("Falha ao criar PIX no MP, usando QR local: %s", e)

    # Fallback: QR PIX estático local
    from qrcode_pix import generate_qr_code_pix
    buffer, codigo = generate_qr_code_pix(valor, txid=codigo_pedido)
    meta["buffer"] = buffer
    meta["codigo_pix"] = codigo
    meta["qr_code_copia_cola"] = codigo
    return meta


def generate_qr_code_pix_com_texto(texto: str):
    """Gera um QR a partir de um texto arbitrário (ex: copia-e-cola do MP)."""
    import io
    import qrcode
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=4)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, texto


# ===================== WEBHOOK SERVER =====================
def _verificar_assinatura(request: web.Request, body: bytes) -> bool:
    if not WEBHOOK_SECRET:
        return True  # sem secret = em modo dev, confia
    sig = request.headers.get("X-Webhook-Signature", "") or request.headers.get("X-Hub-Signature", "")
    # Suporta sha256=HEX
    esperado = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, esperado)


async def handle_webhook(request: web.Request):
    try:
        body = await request.read()
        if not _verificar_assinatura(request, body):
            log.warning("Webhook com assinatura inválida")
            return web.json_response({"ok": False, "erro": "assinatura invalida"}, status=403)
        try:
            data = await request.json()
        except Exception:
            data = {}

        codigo = None
        payment_id = None
        status = None

        # ===== Mercado Pago =====
        # Tópicos de notification: merchant_order ou payment
        if "type" in data or "action" in data:
            # Busca por payment_id: MP envia /v1/payments/ID no data.id
            dt = data.get("data", {}) or {}
            pid = dt.get("id") or data.get("id")
            action = data.get("action", "")
            if pid and (action in ("payment.updated", "payment.created")
                        or data.get("type") in ("payment",)):
                payment_id = str(pid)
                info = await consultar_pagamento_mercadopago(payment_id)
                if info:
                    status = info.get("status")
                    codigo = info.get("external_reference")
        else:
            # ===== Webhook genérico =====
            codigo = (data.get("codigo") or data.get("external_reference")
                      or data.get("order_id") or data.get("pedido"))
            payment_id = str(data.get("payment_id") or data.get("id") or "")
            status = (data.get("status") or "").lower()
            # Mapeamento de status comuns
            if status in ("paid", "approved", "success", "confirmed", "pago", "aprovado"):
                status = "approved"

        if codigo and status in ("approved", "authorized"):
            log.info(f"✅ Pagamento confirmado para {codigo} (prov={PROVIDER})")
            await _dispatch_paid(codigo, data)

        return web.json_response({"ok": True})
    except Exception as e:
        log.exception("Erro no webhook: %s", e)
        return web.json_response({"ok": False, "erro": str(e)}, status=500)


async def api_stats(request: web.Request):
    import database as db
    try:
        pedidos = db.listar_pedidos_por_status("aprovado")
        total_revenue = sum(p["total"] for p in pedidos)
        
        # Mock de novos clientes para o dashboard
        cadastros = len(db.cadastros_mem) if hasattr(db, "cadastros_mem") else 0
        
        headers = {"Access-Control-Allow-Origin": "*"}
        return web.json_response({
            "total_sales": len(pedidos),
            "total_revenue": total_revenue,
            "total_customers": cadastros,
            "recent_orders": pedidos[-10:] if pedidos else []
        }, headers=headers)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def start_webhook_server():
    """Inicia (em background) o servidor HTTP aiohttp para responder health checks, webhooks e API do Dashboard."""
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.router.add_get("/", lambda r: web.json_response({"status": "ok", "service": "WareArcadeBot"}, headers={"Access-Control-Allow-Origin": "*"}))
    app.router.add_get("/health", lambda r: web.json_response({"ok": True, "provider": PROVIDER}, headers={"Access-Control-Allow-Origin": "*"}))
    app.router.add_get("/api/stats", api_stats)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    log.info(f"🌐 Servidor HTTP/Webhook rodando em 0.0.0.0:{WEBHOOK_PORT}{WEBHOOK_PATH} (provider={PROVIDER})")
    return runner


def get_download_link(codigo: str) -> str:
    return DOWNLOAD_URL_TEMPLATE.format(codigo=codigo)

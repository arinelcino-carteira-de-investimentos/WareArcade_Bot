# -*- coding: utf-8 -*-
"""
WareArcadeBot - Gerador de QR Code PIX
"""
import io
import qrcode
from datetime import datetime

EMPRESA = {
    "nome": "MARY DIEISI COSTA CORREA",
    "cnpj": "57.906.055/0001-82",
    "banco": "260 - Nu Pagamentos S.A.",
    "agencia": "0001",
    "conta": "323548181-3",
    "pix": "57.906.055/0001-82",
    "pix_tipo": "CNPJ",
    "cidade": "Sao Paulo",
}


def gerar_pix_payload(chave_pix, nome, cidade, valor, txid="WARE"):
    def format_field(id_field, value):
        return f"{id_field:02d}{len(str(value)):02d}{value}"

    chave_limpa = (chave_pix.replace(".", "").replace("/", "")
                              .replace("-", "").replace(" ", "").strip())

    payload_format          = format_field(0, "01")
    merchant_account        = format_field(0, "br.gov.bcb.pix") + format_field(1, chave_limpa)
    merchant_account_field  = format_field(26, merchant_account)
    merchant_category       = format_field(52, "0000")
    transaction_currency    = format_field(53, "986")
    transaction_amount      = format_field(54, f"{valor:.2f}")
    country_code            = format_field(58, "BR")
    merchant_name           = format_field(59, nome[:25].upper())
    merchant_city           = format_field(60, cidade[:15].upper())
    additional_data         = format_field(62, format_field(5, txid[:25]))

    payload_sem_crc = (
        payload_format + merchant_account_field + merchant_category +
        transaction_currency + transaction_amount + country_code +
        merchant_name + merchant_city + additional_data + "6304"
    )

    def calcular_crc16(payload):
        crc = 0xFFFF
        for byte in payload.encode("utf-8"):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return format(crc, "04X")

    crc = calcular_crc16(payload_sem_crc)
    return payload_sem_crc + crc


def generate_qr_code_pix(valor, txid=None):
    """Gera QR code PIX 'copia e cola' estático usando a chave da empresa."""
    if txid is None:
        txid = f"WA{datetime.now().strftime('%y%m%d%H%M%S')}"

    codigo_pix = gerar_pix_payload(
        chave_pix=EMPRESA["pix"],
        nome=EMPRESA["nome"],
        cidade=EMPRESA["cidade"],
        valor=valor,
        txid=txid,
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(codigo_pix)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, codigo_pix


def generate_qr_from_text(texto: str):
    """Gera um QR Code PNG em memória a partir de qualquer texto (ex: copia-e-cola do MP)."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def enviar_qrcode_pix_texto(context, chat_id, valor, pedido_codigo=None,
                                  buffer=None, copia_cola=None):
    """Envia a mensagem completa de pagamento com o QR photo (usa buffer se fornecido)."""
    try:
        if buffer is None or copia_cola is None:
            buffer, copia_cola = generate_qr_code_pix(valor, txid=pedido_codigo)

        texto = (
            "💚 *PAGAMENTO VIA PIX*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 *Valor: R$ {valor:.2f}*\n\n"
            "📋 *Dados da Empresa:*\n"
            f"📛 {EMPRESA['nome']}\n"
            f"📌 CNPJ: {EMPRESA['cnpj']}\n"
            f"🏦 {EMPRESA['banco']}\n"
            f"🏦 Agência: {EMPRESA['agencia']}\n"
            f"💳 Conta: {EMPRESA['conta']}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💚 *PIX Copia e Cola:*\n"
            f"`{copia_cola}`\n\n"
            "📱 *Escaneie o QR Code* ou toque na chave acima para copiar\n\n"
        )
        if pedido_codigo:
            texto += f"📋 *Código do Pedido:* `{pedido_codigo}`\n\n"
        texto += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *Como pagar:*\n"
            "1️⃣ Abra o app do seu banco\n"
            "2️⃣ Escolha PIX → Pagar com QR Code\n"
            "3️⃣ Aponte a câmera para o código acima OU cole o Copia e Cola\n"
            f"4️⃣ Confirme o valor de *R$ {valor:.2f}*\n"
            "5️⃣ O sistema detecta o pagamento automaticamente ✅\n\n"
            "⏳ *Aguardando pagamento...*"
        )

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=buffer,
            caption=texto,
            parse_mode="Markdown",
        )
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar QR Code: {e}")
        # Fallback: envia só a chave
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"💚 *Chave PIX (CNPJ):* `{EMPRESA['pix']}`\n\n💰 *Valor: R$ {valor:.2f}*",
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return False


# Compatibilidade com assinatura antiga (buffer/copia_cola default)
async def enviar_qrcode_pix(context, chat_id, valor, txid=None, pedido_codigo=None):
    buffer, copia_cola = generate_qr_code_pix(valor, txid=txid or pedido_codigo)
    return await enviar_qrcode_pix_texto(
        context, chat_id, valor,
        pedido_codigo=pedido_codigo,
        buffer=buffer, copia_cola=copia_cola,
    )


def get_dados_pix_texto(valor, pedido_codigo=None):
    texto = (
        "💚 *PAGAMENTO VIA PIX*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Valor: R$ {valor:.2f}*\n\n"
        "📋 *Dados da Empresa:*\n"
        f"📛 {EMPRESA['nome']}\n"
        f"📌 CNPJ: {EMPRESA['cnpj']}\n"
        f"🏦 {EMPRESA['banco']}\n"
        f"🏦 Agência: {EMPRESA['agencia']}\n"
        f"💳 Conta: {EMPRESA['conta']}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💚 *Chave PIX (CNPJ):*\n`{EMPRESA['pix']}`\n\n"
    )
    if pedido_codigo:
        texto += f"📋 *Código do Pedido:* `{pedido_codigo}`\n\n"
    texto += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 *Como pagar:*\n"
        "1️⃣ Copie a chave PIX acima\n"
        "2️⃣ Abra o app do seu banco\n"
        "3️⃣ Escolha PIX → Pagar com chave\n"
        "4️⃣ Cole a chave e confirme o valor\n"
        "5️⃣ Após pagar, o sistema confirma automaticamente ✅\n\n"
        "⏳ *Aguardando pagamento...*"
    )
    return texto

"""
===============================================
WareArcadeBot - Configurações do Sistema
===============================================
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== TOKEN =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ===== CONFIGURAÇÕES =====
ITEMS_PER_PAGE = 10
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# ===== DADOS DA EMPRESA =====
EMPRESA = {
    "nome": "MARY DIEISI COSTA CORREA",
    "cnpj": "57.906.055/0001-82",
    "banco": "260 - Nu Pagamentos S.A.",
    "agencia": "0001",
    "conta": "323548181-3",
    "pix": "57.906.055/0001-82",
    "pix_tipo": "CNPJ"
}

# ===== ADMIN =====
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
if admin_ids_str:
    for admin_id in admin_ids_str.split(","):
        try:
            admin_id = admin_id.strip()
            if admin_id:
                ADMIN_IDS.append(int(admin_id))
        except ValueError:
            pass

# ===== DOWNLOADS =====
DOWNLOAD_BASE_URL = os.getenv("DOWNLOAD_BASE_URL", "https://warearcadebot.com.br/download/")
DOWNLOAD_EXPIRY_HOURS = int(os.getenv("DOWNLOAD_LINK_EXPIRY_HOURS", "48"))

# ===== INFO LOJA =====
STORE_NAME = "🎮 WareArcadeBot - Nexus Digital Shop"
STORE_EMAIL = "warearcadebot@gmail.com"
STORE_WHATSAPP = "+5511940462611"
STORE_INSTAGRAM = "@warearcadebot"
STORE_HOURS = "Seg a Sex: 9h-19h | Sáb: 9h-14h"

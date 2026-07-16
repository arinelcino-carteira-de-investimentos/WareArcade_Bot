# -*- coding: utf-8 -*-
"""
WareArcadeBot - Instalador/Reparador UNICO em Python puro (ASCII).
Funciona em Windows/Linux/Mac. Sem problemas de encoding do PowerShell.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# --- Cores Windows ---
try:
    os.system("")
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
except Exception:
    GREEN = YELLOW = RED = CYAN = RESET = ""

BASE = Path(__file__).resolve().parent
os.chdir(BASE)

def print_ok(msg):   print(f"{GREEN}[OK]{RESET} {msg}")
def print_info(msg): print(f"{CYAN}[INFO]{RESET} {msg}")
def print_warn(msg): print(f"{YELLOW}[AVISO]{RESET} {msg}")
def print_err(msg):  print(f"{RED}[ERRO]{RESET} {msg}")

def banner():
    print()
    print("="*60)
    print("  WareArcadeBot - Instalacao / Reparo")
    print("="*60)
    print()
    print_info(f"Pasta: {BASE}")
    print()

def run_pip(pkg):
    print_info(f"Instalando {pkg} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def py_import_ok(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False

def main():
    banner()

    # --- 1) Backup ---
    print_info("[1/8] Fazendo backup...")
    files_backup = ["catalog.py","database.py","qrcode_pix.py","payments.py","bot.py",".env","warearcade.db"]
    for f in files_backup:
        p = BASE / f
        if p.exists():
            bak = BASE / (f + ".bak")
            try:
                shutil.copy2(p, bak)
                print_ok(f"Backup: {f}.bak")
            except Exception as e:
                print_warn(f"Falha backup {f}: {e}")

    # --- 2) Verifica arquivos do projeto ---
    print()
    print_info("[2/8] Verificando arquivos do projeto...")
    required = ["bot.py","catalog.py","database.py","payments.py","qrcode_pix.py"]
    missing = []
    for f in required:
        p = BASE / f
        if p.exists() and p.stat().st_size > 100:
            print_ok(f"Arquivo: {f}")
        else:
            print_err(f"Faltando: {f}")
            missing.append(f)

    # --- 3) Dependencias ---
    print()
    print_info("[3/8] Verificando dependencias Python...")
    deps = [
        ("python-telegram-bot==20.0", "telegram"),
        ("python-dotenv==1.0.0",      "dotenv"),
        ("qrcode[pil]==7.4.2",        "qrcode"),
        ("Pillow==10.1.0",            "PIL"),
        ("aiohttp==3.9.5",            "aiohttp"),
    ]
    for pkg, mod in deps:
        if py_import_ok(mod):
            print_ok(f"{pkg}")
        else:
            try:
                run_pip(pkg)
                print_ok(f"{pkg} instalado")
            except Exception as e:
                print_err(f"Falha ao instalar {pkg}: {e}")

    # --- 4) Verifica .env ---
    print()
    print_info("[4/8] Configurando .env ...")
    env_path = BASE / ".env"
    token_set = False
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                val = line.split("=",1)[1].strip()
                if val and "SEU_TOKEN" not in val and "COLE_SEU" not in val and len(val) > 10:
                    token_set = True
    if not token_set:
        env_template = """# =====================================================
# WareArcadeBot - Configuracoes
# =====================================================

TELEGRAM_BOT_TOKEN=COLE_SEU_TOKEN_AQUI
ADMIN_CHAT_IDS=

DB_PATH=warearcade.db

# Pagamento PIX: manual | mercadopago | generic
PAYMENT_PROVIDER=manual
MERCADOPAGO_ACCESS_TOKEN=

WEBHOOK_SECRET=troque-esta-senha-forte
WEBHOOK_PORT=8000
WEBHOOK_PATH=/webhook/pix
PUBLIC_WEBHOOK_URL=https://SEU-DOMINIO.com.br/webhook/pix

DOWNLOAD_URL_TEMPLATE=https://warearcadebot.com.br/download/{codigo}

AUTO_APPROVE_ON_PAID=1
"""
        env_path.write_text(env_template, encoding="utf-8")
        print_ok(".env criado. EDITE-O E COLOQUE SEU TELEGRAM_BOT_TOKEN!")
    else:
        print_ok(".env com token configurado.")

    # --- 5) Validacao de sintaxe Python ---
    print()
    print_info("[5/8] Validando sintaxe dos arquivos...")
    ok = True
    for f in required:
        p = BASE / f
        if not p.exists():
            continue
        r = subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print_ok(f"Sintaxe: {f}")
        else:
            print_err(f"Erro sintaxe em {f}:")
            print(r.stderr)
            ok = False

    # --- 6) Inicializa banco ---
    print()
    print_info("[6/8] Inicializando banco SQLite...")
    try:
        sys.path.insert(0, str(BASE))
        import database as db
        db.init_db()
        print_ok(f"Banco pronto: {db.DB_PATH}")
    except Exception as e:
        print_err(f"Falha ao inicializar banco: {e}")
        ok = False

    # --- 7) Resumo catalogo ---
    print()
    print_info("[7/8] Carregando catalogo...")
    try:
        import catalog
        print_ok(f"Produtos no catalogo: {len(catalog.GAMES_CATALOG)}")
        print_ok(f"Categorias: {len(catalog.TIPOS)} tipos / {len(catalog.CATEGORIAS)} subcategorias")
        print_ok(f"Ofertas: {len(catalog.get_offers())}")
    except Exception as e:
        print_err(f"Erro ao carregar catalogo: {e}")
        ok = False

    # --- 8) Inicia o bot ---
    print()
    print_info("[8/8] Tudo pronto!")
    print("="*60)
    print()
    print("Comandos do bot:")
    print("  Publicos: /start | /menu | /cadastro | /feedback")
    print("  Admin:    /admin | /pendentes | /aprovar COD | /rejeitar COD | /info COD")
    print()

    if missing:
        print_err("Arquivos faltando - nao foi possivel iniciar.")
        print_warn("Copie todos os arquivos .py para a pasta e execute novamente.")
        input("\nPressione ENTER para sair...")
        return 1

    if not ok:
        print_err("Foram encontrados erros. Verifique as mensagens acima.")
        input("\nPressione ENTER para sair...")
        return 1

    print("Iniciando o bot... (Ctrl+C para parar)")
    print("="*60)
    print()

    try:
        subprocess.run([sys.executable, str(BASE / "bot.py")], check=False)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_err(f"Erro ao rodar bot: {e}")

    print()
    print("Bot encerrado.")
    input("Pressione ENTER para sair...")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrompido.")
    except Exception as e:
        print_err(f"Falha geral: {e}")
        input("\nPressione ENTER...")
        sys.exit(1)

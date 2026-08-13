# -*- coding: utf-8 -*-
"""
WareArcadeBot - Camada de persistência em PostgreSQL (Neon)
Salva cadastros, carrinhos e pedidos. Thread/async-safe via pool.
Migrado de SQLite para Neon PostgreSQL para persistência na nuvem.
"""
import os
import json
import threading
import logging
from datetime import datetime
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2 import pool

logger = logging.getLogger(__name__)

# ===================== CONEXÃO =====================
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    logger.critical("❌ DATABASE_URL não configurada! Defina no .env ou variáveis de ambiente.")

_pool = None
_lock = threading.RLock()


def _get_pool():
    """Cria o pool de conexões sob demanda (lazy init)."""
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=DATABASE_URL,
                )
                logger.info("🟢 Pool de conexões Neon PostgreSQL criado.")
    return _pool


@contextmanager
def get_conn():
    """Obtém uma conexão do pool, faz commit/rollback automático."""
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


# ===================== INIT =====================
def init_db():
    """Cria as tabelas se não existirem no Neon PostgreSQL."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cadastros (
            user_id BIGINT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            codigo TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            itens TEXT NOT NULL,
            total REAL NOT NULL,
            metodo TEXT NOT NULL,
            status TEXT NOT NULL,
            data TEXT NOT NULL,
            link_download TEXT,
            cliente_nome TEXT,
            cliente_email TEXT,
            cliente_whatsapp TEXT,
            pagamento_id TEXT,
            qr_code TEXT,
            qr_code_copia_cola TEXT,
            confirmed_at TEXT,
            approved_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_pedidos_user ON pedidos(user_id);
        CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status);

        CREATE TABLE IF NOT EXISTS carrinhos (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            game_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            added_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_carrinho_user ON carrinhos(user_id);

        CREATE TABLE IF NOT EXISTS ordem_counter (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL
        );
        """)
        # Garante contador
        cur.execute("SELECT valor FROM ordem_counter WHERE id = 1")
        if cur.fetchone() is None:
            prox = _proximo_numero_inicial()
            cur.execute("INSERT INTO ordem_counter(id, valor) VALUES (1, %s)", (prox,))
        conn.commit()
    logger.info("✅ Banco Neon PostgreSQL inicializado com sucesso.")


def _proximo_numero_inicial():
    """Tenta continuar a numeração a partir do último pedido no banco."""
    try:
        with get_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT codigo FROM pedidos ORDER BY data DESC LIMIT 1")
            row = cur.fetchone()
            if row and row["codigo"].startswith("WA-"):
                try:
                    return int(row["codigo"][3:]) + 1
                except ValueError:
                    return 1
    except Exception:
        pass
    return 1


# ===================== CONTADOR DE PEDIDOS =====================
def proximo_codigo_pedido():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT valor FROM ordem_counter WHERE id = 1 FOR UPDATE")
        row = cur.fetchone()
        valor = row["valor"]
        cur.execute("UPDATE ordem_counter SET valor = %s WHERE id = 1", (valor + 1,))
        return f"WA-{valor:06d}"


# ===================== CADASTROS =====================
def salvar_cadastro(user_id, nome, email, whatsapp):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM cadastros WHERE user_id = %s", (user_id,))
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE cadastros SET nome=%s, email=%s, whatsapp=%s, updated_at=%s WHERE user_id=%s",
                (nome, email, whatsapp, now, user_id),
            )
        else:
            cur.execute(
                "INSERT INTO cadastros(user_id, nome, email, whatsapp, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (user_id, nome, email, whatsapp, now, now),
            )


def carregar_cadastro(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT nome, email, whatsapp FROM cadastros WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"nome": row["nome"], "email": row["email"], "whatsapp": row["whatsapp"]}


# ===================== CARRINHO =====================
def adicionar_carrinho(user_id, game_id, nome, preco):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO carrinhos(user_id, game_id, nome, preco, added_at) VALUES (%s,%s,%s,%s,%s)",
            (user_id, game_id, nome, preco, now),
        )


def remover_item_carrinho(user_id, idx):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT id FROM carrinhos WHERE user_id = %s ORDER BY added_at ASC, id ASC",
            (user_id,),
        )
        rows = cur.fetchall()
        if 0 <= idx < len(rows):
            cur.execute("DELETE FROM carrinhos WHERE id = %s", (rows[idx]["id"],))


def limpar_carrinho(user_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM carrinhos WHERE user_id = %s", (user_id,))


def carregar_carrinho(user_id):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT game_id, nome, preco FROM carrinhos WHERE user_id = %s "
            "ORDER BY added_at ASC, id ASC",
            (user_id,),
        )
        rows = cur.fetchall()
        return [{"id": r["game_id"], "nome": r["nome"], "preco": r["preco"]} for r in rows]


# ===================== PEDIDOS =====================
def salvar_pedido(pedido):
    now = datetime.now().isoformat()
    cliente = pedido.get("cliente", {})
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pedidos(
                codigo, user_id, itens, total, metodo, status, data, link_download,
                cliente_nome, cliente_email, cliente_whatsapp, pagamento_id,
                qr_code, qr_code_copia_cola, confirmed_at, approved_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (codigo) DO UPDATE SET
                user_id=EXCLUDED.user_id, itens=EXCLUDED.itens, total=EXCLUDED.total,
                metodo=EXCLUDED.metodo, status=EXCLUDED.status, data=EXCLUDED.data,
                link_download=EXCLUDED.link_download, cliente_nome=EXCLUDED.cliente_nome,
                cliente_email=EXCLUDED.cliente_email, cliente_whatsapp=EXCLUDED.cliente_whatsapp,
                pagamento_id=EXCLUDED.pagamento_id, qr_code=EXCLUDED.qr_code,
                qr_code_copia_cola=EXCLUDED.qr_code_copia_cola,
                confirmed_at=EXCLUDED.confirmed_at, approved_at=EXCLUDED.approved_at
        """, (
            pedido["codigo"],
            pedido["user_id"],
            json.dumps(pedido.get("itens", []), ensure_ascii=False),
            pedido["total"],
            pedido.get("metodo", "pix"),
            pedido.get("status", "pendente"),
            pedido.get("data", now),
            pedido.get("link_download"),
            cliente.get("nome"),
            cliente.get("email"),
            cliente.get("whatsapp"),
            pedido.get("pagamento_id"),
            pedido.get("qr_code"),
            pedido.get("qr_code_copia_cola"),
            pedido.get("confirmed_at"),
            pedido.get("approved_at"),
        ))


def atualizar_status_pedido(codigo, status, **extra):
    with get_conn() as conn:
        cur = conn.cursor()
        sets = ["status = %s"]
        vals = [status]
        for k, v in extra.items():
            sets.append(f"{k} = %s")
            vals.append(v)
        vals.append(codigo)
        cur.execute(f"UPDATE pedidos SET {', '.join(sets)} WHERE codigo = %s", vals)


def carregar_pedido(codigo):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM pedidos WHERE codigo = %s", (codigo,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_pedido(row)


def listar_pedidos_por_status(*statuses):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        qmarks = ",".join(["%s"] * len(statuses))
        cur.execute(
            f"SELECT * FROM pedidos WHERE status IN ({qmarks}) ORDER BY data ASC",
            statuses,
        )
        rows = cur.fetchall()
        return [_row_to_pedido(r) for r in rows]


def listar_pedidos_usuario(user_id, limit=5):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT * FROM pedidos WHERE user_id = %s ORDER BY data DESC LIMIT %s",
            (user_id, limit),
        )
        rows = cur.fetchall()
        return [_row_to_pedido(r) for r in rows]


def _row_to_pedido(row):
    return {
        "codigo": row["codigo"],
        "user_id": row["user_id"],
        "itens": json.loads(row["itens"] or "[]"),
        "total": row["total"],
        "metodo": row["metodo"],
        "status": row["status"],
        "data": row["data"],
        "link_download": row["link_download"],
        "cliente": {
            "nome": row["cliente_nome"],
            "email": row["cliente_email"],
            "whatsapp": row["cliente_whatsapp"],
        },
        "pagamento_id": row["pagamento_id"],
        "qr_code": row["qr_code"],
        "qr_code_copia_cola": row["qr_code_copia_cola"],
        "confirmed_at": row["confirmed_at"],
        "approved_at": row["approved_at"],
    }


# ===================== DICIONÁRIOS EM MEMÓRIA (compatibilidade com o bot.py) =====================
# Estes dicionários são preenchidos no startup e sincronizados com o BD.
carrinhos_mem = {}
pedidos_mem = {}
pedidos_pendentes_mem = {}
cadastros_mem = {}


def carregar_tudo_para_memoria():
    """Carrega estado do banco para os dicionários em memória usados pelo bot."""
    carrinhos_mem.clear()
    pedidos_mem.clear()
    pedidos_pendentes_mem.clear()
    cadastros_mem.clear()

    # Cadastros
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT user_id, nome, email, whatsapp FROM cadastros")
        for row in cur.fetchall():
            cadastros_mem[row["user_id"]] = {
                "nome": row["nome"], "email": row["email"], "whatsapp": row["whatsapp"],
            }

    # Carrinhos (agrupados por user)
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT DISTINCT user_id FROM carrinhos")
        user_ids = [r["user_id"] for r in cur.fetchall()]
    for uid in user_ids:
        carrinhos_mem[uid] = carregar_carrinho(uid)

    # Pedidos
    pendentes = listar_pedidos_por_status("pendente", "aguardando_aprovacao")
    for p in pendentes:
        pedidos_pendentes_mem[p["codigo"]] = p

    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM pedidos")
        rows = cur.fetchall()
    for r in rows:
        p = _row_to_pedido(r)
        pedidos_mem.setdefault(p["user_id"], []).append(p)


# ===================== HELPERS DE ALTO NÍVEL =====================
def add_to_cart(user_id, game_id, nome, preco):
    adicionar_carrinho(user_id, game_id, nome, preco)
    carrinhos_mem.setdefault(user_id, []).append(
        {"id": game_id, "nome": nome, "preco": preco})


def remove_from_cart(user_id, idx):
    remover_item_carrinho(user_id, idx)
    carrinhos_mem[user_id] = carregar_carrinho(user_id)


def clear_cart(user_id):
    limpar_carrinho(user_id)
    carrinhos_mem[user_id] = []


def get_cart(user_id):
    if user_id not in carrinhos_mem:
        carrinhos_mem[user_id] = carregar_carrinho(user_id)
    return carrinhos_mem[user_id]


def save_cadastro(user_id, dados):
    salvar_cadastro(user_id, dados["nome"], dados["email"], dados["whatsapp"])
    cadastros_mem[user_id] = dict(dados)


def get_cadastro(user_id):
    return cadastros_mem.get(user_id)


def save_pedido(pedido):
    salvar_pedido(pedido)
    pedidos_mem.setdefault(pedido["user_id"], []).append(pedido)
    if pedido["status"] in ("pendente", "aguardando_aprovacao"):
        pedidos_pendentes_mem[pedido["codigo"]] = pedido


def update_pedido(codigo, status, **extra):
    atualizar_status_pedido(codigo, status, **extra)
    p = carregar_pedido(codigo)
    if not p:
        return None
    # Atualiza memória
    pedidos_pendentes_mem.pop(codigo, None)
    if p["status"] in ("pendente", "aguardando_aprovacao"):
        pedidos_pendentes_mem[codigo] = p
    if p["user_id"] in pedidos_mem:
        for i, ex in enumerate(pedidos_mem[p["user_id"]]):
            if ex["codigo"] == codigo:
                pedidos_mem[p["user_id"]][i] = p
                break
    return p


def next_codigo():
    return proximo_codigo_pedido()


def get_pedidos_pendentes():
    return dict(pedidos_pendentes_mem)


def get_pedidos_usuario(user_id, limit=5):
    return listar_pedidos_usuario(user_id, limit)

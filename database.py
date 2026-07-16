# -*- coding: utf-8 -*-
"""
WareArcadeBot - Camada de persistência em SQLite
Salva cadastros, carrinhos e pedidos. Thread/async-safe via lock.
"""
import sqlite3
import json
import threading
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "warearcade.db")
_lock = threading.RLock()


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_conn():
    with _lock:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db():
    """Cria as tabelas se não existirem."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS cadastros (
            user_id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            whatsapp TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            codigo TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
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
            user_id INTEGER NOT NULL,
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
        cur = conn.execute("SELECT valor FROM ordem_counter WHERE id = 1")
        if cur.fetchone() is None:
            conn.execute("INSERT INTO ordem_counter(id, valor) VALUES (1, ?)",
                         (_proximo_numero_inicial(),))


def _proximo_numero_inicial():
    """Tenta continuar a numeração a partir do último pedido no banco."""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT codigo FROM pedidos ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
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
        row = conn.execute("SELECT valor FROM ordem_counter WHERE id = 1").fetchone()
        valor = row["valor"]
        conn.execute("UPDATE ordem_counter SET valor = ? WHERE id = 1", (valor + 1,))
        return f"WA-{valor:06d}"


# ===================== CADASTROS =====================
def salvar_cadastro(user_id, nome, email, whatsapp):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT user_id FROM cadastros WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE cadastros SET nome=?, email=?, whatsapp=?, updated_at=? WHERE user_id=?",
                (nome, email, whatsapp, now, user_id),
            )
        else:
            conn.execute(
                "INSERT INTO cadastros(user_id, nome, email, whatsapp, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?)",
                (user_id, nome, email, whatsapp, now, now),
            )


def carregar_cadastro(user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT nome, email, whatsapp FROM cadastros WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {"nome": row["nome"], "email": row["email"], "whatsapp": row["whatsapp"]}


# ===================== CARRINHO =====================
def adicionar_carrinho(user_id, game_id, nome, preco):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO carrinhos(user_id, game_id, nome, preco, added_at) VALUES (?,?,?,?,?)",
            (user_id, game_id, nome, preco, now),
        )


def remover_item_carrinho(user_id, idx):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT rowid FROM carrinhos WHERE user_id = ? ORDER BY added_at ASC, rowid ASC",
            (user_id,),
        ).fetchall()
        if 0 <= idx < len(rows):
            conn.execute("DELETE FROM carrinhos WHERE rowid = ?", (rows[idx]["rowid"],))


def limpar_carrinho(user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM carrinhos WHERE user_id = ?", (user_id,))


def carregar_carrinho(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT game_id, nome, preco FROM carrinhos WHERE user_id = ? "
            "ORDER BY added_at ASC, rowid ASC",
            (user_id,),
        ).fetchall()
        return [{"id": r["game_id"], "nome": r["nome"], "preco": r["preco"]} for r in rows]


# ===================== PEDIDOS =====================
def salvar_pedido(pedido):
    now = datetime.now().isoformat()
    cliente = pedido.get("cliente", {})
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pedidos("
            "codigo, user_id, itens, total, metodo, status, data, link_download,"
            "cliente_nome, cliente_email, cliente_whatsapp, pagamento_id,"
            "qr_code, qr_code_copia_cola, confirmed_at, approved_at"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
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
            ),
        )


def atualizar_status_pedido(codigo, status, **extra):
    with get_conn() as conn:
        sets = ["status = ?"]
        vals = [status]
        for k, v in extra.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(codigo)
        conn.execute(f"UPDATE pedidos SET {', '.join(sets)} WHERE codigo = ?", vals)


def carregar_pedido(codigo):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM pedidos WHERE codigo = ?", (codigo,)).fetchone()
        if not row:
            return None
        return _row_to_pedido(row)


def listar_pedidos_por_status(*statuses):
    with get_conn() as conn:
        qmarks = ",".join("?" * len(statuses))
        rows = conn.execute(
            f"SELECT * FROM pedidos WHERE status IN ({qmarks}) ORDER BY data ASC",
            statuses,
        ).fetchall()
        return [_row_to_pedido(r) for r in rows]


def listar_pedidos_usuario(user_id, limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pedidos WHERE user_id = ? ORDER BY rowid DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
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
        for row in conn.execute("SELECT user_id, nome, email, whatsapp FROM cadastros"):
            cadastros_mem[row["user_id"]] = {
                "nome": row["nome"], "email": row["email"], "whatsapp": row["whatsapp"],
            }

    # Carrinhos (agrupados por user)
    for uid in {k["user_id"] for k in [
            dict(r) for r in (
                sqlite3.connect(DB_PATH).execute(
                    "SELECT DISTINCT user_id FROM carrinhos").fetchall())]}:
        carrinhos_mem[uid] = carregar_carrinho(uid)

    # Pedidos
    pendentes = listar_pedidos_por_status("pendente", "aguardando_aprovacao")
    for p in pendentes:
        pedidos_pendentes_mem[p["codigo"]] = p

    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM pedidos").fetchall()
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

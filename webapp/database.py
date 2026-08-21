"""Camada de acesso a dados (SQLite) da versão web, com dados isolados por usuário."""

import sqlite3
import uuid
from datetime import date
from pathlib import Path

from dateutil.relativedelta import relativedelta

DB_PATH = Path.home() / ".controle_financeiro" / "financas_web.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'conta',
    saldo_atual REAL NOT NULL DEFAULT 0,
    limite REAL DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    grupo_orcamento TEXT NOT NULL DEFAULT 'necessidade',
    orcamento_mensal REAL DEFAULT 0,
    UNIQUE (usuario_id, nome),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'fixa',
    data_prevista TEXT NOT NULL,
    conta_id INTEGER NOT NULL,
    recebida INTEGER NOT NULL DEFAULT 0,
    data_recebimento TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);

CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    categoria_id INTEGER NOT NULL,
    conta_id INTEGER NOT NULL,
    data_prevista TEXT NOT NULL,
    parcela_numero INTEGER NOT NULL DEFAULT 1,
    parcelas_total INTEGER NOT NULL DEFAULT 1,
    compra_grupo TEXT,
    paga INTEGER NOT NULL DEFAULT 0,
    data_pagamento TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);

CREATE TABLE IF NOT EXISTS investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'renda_fixa',
    data TEXT NOT NULL,
    conta_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);
"""

DEFAULT_CATEGORIAS = [
    ("Moradia", "necessidade"),
    ("Alimentação", "necessidade"),
    ("Transporte", "necessidade"),
    ("Saúde", "necessidade"),
    ("Lazer", "desejo"),
    ("Compras", "desejo"),
    ("Assinaturas", "desejo"),
    ("Investimentos", "poupanca"),
    ("Reserva de Emergência", "poupanca"),
]


def conectar(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    conn.commit()


# ---------------- Usuários ----------------
def criar_usuario(conn, nome, email, senha_hash):
    cur = conn.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, date.today().isoformat()),
    )
    usuario_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO categorias (usuario_id, nome, grupo_orcamento) VALUES (?, ?, ?)",
        [(usuario_id, nome_cat, grupo) for nome_cat, grupo in DEFAULT_CATEGORIAS],
    )
    conn.commit()
    return usuario_id


def buscar_usuario_por_email(conn, email):
    return conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()


def buscar_usuario_por_id(conn, usuario_id):
    return conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()


# ---------------- Contas ----------------
def listar_contas(conn, usuario_id):
    return conn.execute(
        "SELECT * FROM contas WHERE usuario_id = ? ORDER BY nome", (usuario_id,)
    ).fetchall()


def buscar_conta(conn, usuario_id, conta_id):
    return conn.execute(
        "SELECT * FROM contas WHERE usuario_id = ? AND id = ?", (usuario_id, conta_id)
    ).fetchone()


def criar_conta(conn, usuario_id, nome, tipo="conta", saldo_atual=0.0, limite=0.0):
    cur = conn.execute(
        "INSERT INTO contas (usuario_id, nome, tipo, saldo_atual, limite) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, nome, tipo, saldo_atual, limite),
    )
    conn.commit()
    return cur.lastrowid


def ajustar_saldo_conta(conn, usuario_id, conta_id, delta):
    conn.execute(
        "UPDATE contas SET saldo_atual = saldo_atual + ? WHERE id = ? AND usuario_id = ?",
        (delta, conta_id, usuario_id),
    )
    conn.commit()


def excluir_conta(conn, usuario_id, conta_id):
    conn.execute("DELETE FROM contas WHERE id = ? AND usuario_id = ?", (conta_id, usuario_id))
    conn.commit()


def saldo_total(conn, usuario_id):
    row = conn.execute(
        "SELECT COALESCE(SUM(saldo_atual), 0) AS total FROM contas "
        "WHERE usuario_id = ? AND tipo = 'conta'",
        (usuario_id,),
    ).fetchone()
    return row["total"]


# ---------------- Categorias ----------------
def listar_categorias(conn, usuario_id):
    return conn.execute(
        "SELECT * FROM categorias WHERE usuario_id = ? ORDER BY nome", (usuario_id,)
    ).fetchall()


def criar_categoria(conn, usuario_id, nome, grupo_orcamento="necessidade", orcamento_mensal=0.0):
    cur = conn.execute(
        "INSERT INTO categorias (usuario_id, nome, grupo_orcamento, orcamento_mensal) "
        "VALUES (?, ?, ?, ?)",
        (usuario_id, nome, grupo_orcamento, orcamento_mensal),
    )
    conn.commit()
    return cur.lastrowid


def excluir_categoria(conn, usuario_id, categoria_id):
    conn.execute(
        "DELETE FROM categorias WHERE id = ? AND usuario_id = ?", (categoria_id, usuario_id)
    )
    conn.commit()


# ---------------- Receitas ----------------
def listar_receitas(conn, usuario_id, ano=None):
    if ano:
        return conn.execute(
            "SELECT r.*, c.nome AS conta_nome FROM receitas r "
            "JOIN contas c ON c.id = r.conta_id "
            "WHERE r.usuario_id = ? AND strftime('%Y', r.data_prevista) = ? "
            "ORDER BY r.data_prevista",
            (usuario_id, str(ano)),
        ).fetchall()
    return conn.execute(
        "SELECT r.*, c.nome AS conta_nome FROM receitas r "
        "JOIN contas c ON c.id = r.conta_id "
        "WHERE r.usuario_id = ? ORDER BY r.data_prevista",
        (usuario_id,),
    ).fetchall()


def criar_receita(conn, usuario_id, descricao, valor, tipo, data_prevista, conta_id):
    cur = conn.execute(
        "INSERT INTO receitas (usuario_id, descricao, valor, tipo, data_prevista, conta_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, descricao, valor, tipo, data_prevista, conta_id),
    )
    conn.commit()
    return cur.lastrowid


def marcar_receita_recebida(conn, usuario_id, receita_id, recebida=True):
    receita = conn.execute(
        "SELECT * FROM receitas WHERE id = ? AND usuario_id = ?", (receita_id, usuario_id)
    ).fetchone()
    if receita is None:
        return
    ja_recebida = bool(receita["recebida"])
    if recebida and not ja_recebida:
        ajustar_saldo_conta(conn, usuario_id, receita["conta_id"], receita["valor"])
        conn.execute(
            "UPDATE receitas SET recebida=1, data_recebimento=? WHERE id=? AND usuario_id=?",
            (date.today().isoformat(), receita_id, usuario_id),
        )
    elif not recebida and ja_recebida:
        ajustar_saldo_conta(conn, usuario_id, receita["conta_id"], -receita["valor"])
        conn.execute(
            "UPDATE receitas SET recebida=0, data_recebimento=NULL WHERE id=? AND usuario_id=?",
            (receita_id, usuario_id),
        )
    conn.commit()


def excluir_receita(conn, usuario_id, receita_id):
    receita = conn.execute(
        "SELECT * FROM receitas WHERE id = ? AND usuario_id = ?", (receita_id, usuario_id)
    ).fetchone()
    if receita and receita["recebida"]:
        ajustar_saldo_conta(conn, usuario_id, receita["conta_id"], -receita["valor"])
    conn.execute("DELETE FROM receitas WHERE id = ? AND usuario_id = ?", (receita_id, usuario_id))
    conn.commit()


# ---------------- Despesas ----------------
def listar_despesas(conn, usuario_id, ano=None):
    if ano:
        return conn.execute(
            "SELECT d.*, c.nome AS categoria_nome, c.grupo_orcamento, ct.nome AS conta_nome "
            "FROM despesas d "
            "JOIN categorias c ON c.id = d.categoria_id "
            "JOIN contas ct ON ct.id = d.conta_id "
            "WHERE d.usuario_id = ? AND strftime('%Y', d.data_prevista) = ? "
            "ORDER BY d.data_prevista",
            (usuario_id, str(ano)),
        ).fetchall()
    return conn.execute(
        "SELECT d.*, c.nome AS categoria_nome, c.grupo_orcamento, ct.nome AS conta_nome "
        "FROM despesas d "
        "JOIN categorias c ON c.id = d.categoria_id "
        "JOIN contas ct ON ct.id = d.conta_id "
        "WHERE d.usuario_id = ? ORDER BY d.data_prevista",
        (usuario_id,),
    ).fetchall()


def criar_despesa_parcelada(
    conn, usuario_id, descricao, valor_total, categoria_id, conta_id, data_prevista, parcelas_total=1
):
    compra_grupo = str(uuid.uuid4())
    valor_parcela = round(valor_total / parcelas_total, 2)
    data_base = date.fromisoformat(data_prevista)
    ids = []
    for i in range(parcelas_total):
        data_parcela = data_base + relativedelta(months=i)
        cur = conn.execute(
            "INSERT INTO despesas (usuario_id, descricao, valor, categoria_id, conta_id, "
            "data_prevista, parcela_numero, parcelas_total, compra_grupo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                usuario_id, descricao, valor_parcela, categoria_id, conta_id,
                data_parcela.isoformat(), i + 1, parcelas_total, compra_grupo,
            ),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def marcar_despesa_paga(conn, usuario_id, despesa_id, paga=True):
    despesa = conn.execute(
        "SELECT * FROM despesas WHERE id = ? AND usuario_id = ?", (despesa_id, usuario_id)
    ).fetchone()
    if despesa is None:
        return
    ja_paga = bool(despesa["paga"])
    if paga and not ja_paga:
        ajustar_saldo_conta(conn, usuario_id, despesa["conta_id"], -despesa["valor"])
        conn.execute(
            "UPDATE despesas SET paga=1, data_pagamento=? WHERE id=? AND usuario_id=?",
            (date.today().isoformat(), despesa_id, usuario_id),
        )
    elif not paga and ja_paga:
        ajustar_saldo_conta(conn, usuario_id, despesa["conta_id"], despesa["valor"])
        conn.execute(
            "UPDATE despesas SET paga=0, data_pagamento=NULL WHERE id=? AND usuario_id=?",
            (despesa_id, usuario_id),
        )
    conn.commit()


def excluir_despesa(conn, usuario_id, despesa_id):
    despesa = conn.execute(
        "SELECT * FROM despesas WHERE id = ? AND usuario_id = ?", (despesa_id, usuario_id)
    ).fetchone()
    if despesa and despesa["paga"]:
        ajustar_saldo_conta(conn, usuario_id, despesa["conta_id"], despesa["valor"])
    conn.execute("DELETE FROM despesas WHERE id = ? AND usuario_id = ?", (despesa_id, usuario_id))
    conn.commit()


def gasto_por_categoria_mes(conn, usuario_id, ano, mes):
    return conn.execute(
        "SELECT c.id, c.nome, c.grupo_orcamento, c.orcamento_mensal, "
        "COALESCE(SUM(CASE WHEN strftime('%Y', d.data_prevista) = ? "
        "AND strftime('%m', d.data_prevista) = ? THEN d.valor END), 0) AS gasto "
        "FROM categorias c "
        "LEFT JOIN despesas d ON d.categoria_id = c.id AND d.usuario_id = c.usuario_id "
        "WHERE c.usuario_id = ? "
        "GROUP BY c.id ORDER BY c.nome",
        (str(ano), f"{mes:02d}", usuario_id),
    ).fetchall()


# ---------------- Investimentos ----------------
def listar_investimentos(conn, usuario_id, ano=None):
    if ano:
        return conn.execute(
            "SELECT * FROM investimentos WHERE usuario_id = ? AND strftime('%Y', data) = ? "
            "ORDER BY data",
            (usuario_id, str(ano)),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM investimentos WHERE usuario_id = ? ORDER BY data", (usuario_id,)
    ).fetchall()


def criar_investimento(conn, usuario_id, descricao, valor, tipo, data, conta_id=None):
    cur = conn.execute(
        "INSERT INTO investimentos (usuario_id, descricao, valor, tipo, data, conta_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, descricao, valor, tipo, data, conta_id),
    )
    if conta_id:
        ajustar_saldo_conta(conn, usuario_id, conta_id, -valor)
    conn.commit()
    return cur.lastrowid


def excluir_investimento(conn, usuario_id, investimento_id):
    inv = conn.execute(
        "SELECT * FROM investimentos WHERE id = ? AND usuario_id = ?",
        (investimento_id, usuario_id),
    ).fetchone()
    if inv and inv["conta_id"]:
        ajustar_saldo_conta(conn, usuario_id, inv["conta_id"], inv["valor"])
    conn.execute(
        "DELETE FROM investimentos WHERE id = ? AND usuario_id = ?", (investimento_id, usuario_id)
    )
    conn.commit()


def patrimonio_investido_total(conn, usuario_id):
    row = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM investimentos WHERE usuario_id = ?",
        (usuario_id,),
    ).fetchone()
    return row["total"]


def evolucao_investimentos(conn, usuario_id, ano):
    rows = conn.execute(
        "SELECT strftime('%Y-%m', data) AS mes_ref, SUM(valor) AS total "
        "FROM investimentos WHERE usuario_id = ? AND strftime('%Y', data) <= ? "
        "GROUP BY mes_ref ORDER BY mes_ref",
        (usuario_id, str(ano)),
    ).fetchall()
    return rows


# ---------------- Reset ----------------
def resetar_tudo(conn, usuario_id):
    conn.execute("DELETE FROM despesas WHERE usuario_id = ?", (usuario_id,))
    conn.execute("DELETE FROM receitas WHERE usuario_id = ?", (usuario_id,))
    conn.execute("DELETE FROM investimentos WHERE usuario_id = ?", (usuario_id,))
    conn.execute("DELETE FROM contas WHERE usuario_id = ?", (usuario_id,))
    conn.execute("DELETE FROM categorias WHERE usuario_id = ?", (usuario_id,))
    conn.executemany(
        "INSERT INTO categorias (usuario_id, nome, grupo_orcamento) VALUES (?, ?, ?)",
        [(usuario_id, nome_cat, grupo) for nome_cat, grupo in DEFAULT_CATEGORIAS],
    )
    conn.commit()

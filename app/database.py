"""Camada de acesso a dados (SQLite) do sistema de controle financeiro."""

import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path.home() / ".controle_financeiro" / "financas.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'conta', -- conta | cartao
    saldo_atual REAL NOT NULL DEFAULT 0,
    limite REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    grupo_orcamento TEXT NOT NULL DEFAULT 'necessidade', -- necessidade | desejo | poupanca
    orcamento_mensal REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'fixa', -- fixa | variavel
    data_prevista TEXT NOT NULL,
    conta_id INTEGER NOT NULL,
    recebida INTEGER NOT NULL DEFAULT 0,
    data_recebimento TEXT,
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);

CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL, -- valor da parcela
    categoria_id INTEGER NOT NULL,
    conta_id INTEGER NOT NULL,
    data_prevista TEXT NOT NULL,
    parcela_numero INTEGER NOT NULL DEFAULT 1,
    parcelas_total INTEGER NOT NULL DEFAULT 1,
    compra_grupo TEXT, -- agrupa parcelas da mesma compra
    paga INTEGER NOT NULL DEFAULT 0,
    data_pagamento TEXT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);

CREATE TABLE IF NOT EXISTS investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL, -- positivo = aporte, negativo = resgate
    tipo TEXT NOT NULL DEFAULT 'renda_fixa',
    data TEXT NOT NULL,
    conta_id INTEGER,
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


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        cur = self.conn.execute("SELECT COUNT(*) FROM categorias")
        if cur.fetchone()[0] == 0:
            self.conn.executemany(
                "INSERT INTO categorias (nome, grupo_orcamento) VALUES (?, ?)",
                DEFAULT_CATEGORIAS,
            )
            self.conn.commit()

    # ---------------- Contas ----------------
    def listar_contas(self):
        return self.conn.execute("SELECT * FROM contas ORDER BY nome").fetchall()

    def criar_conta(self, nome, tipo="conta", saldo_atual=0.0, limite=0.0):
        cur = self.conn.execute(
            "INSERT INTO contas (nome, tipo, saldo_atual, limite) VALUES (?, ?, ?, ?)",
            (nome, tipo, saldo_atual, limite),
        )
        self.conn.commit()
        return cur.lastrowid

    def atualizar_saldo_conta(self, conta_id, novo_saldo):
        self.conn.execute(
            "UPDATE contas SET saldo_atual = ? WHERE id = ?", (novo_saldo, conta_id)
        )
        self.conn.commit()

    def ajustar_saldo_conta(self, conta_id, delta):
        self.conn.execute(
            "UPDATE contas SET saldo_atual = saldo_atual + ? WHERE id = ?",
            (delta, conta_id),
        )
        self.conn.commit()

    def excluir_conta(self, conta_id):
        self.conn.execute("DELETE FROM contas WHERE id = ?", (conta_id,))
        self.conn.commit()

    def saldo_total(self):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(saldo_atual), 0) AS total FROM contas WHERE tipo = 'conta'"
        ).fetchone()
        return row["total"]

    # ---------------- Categorias ----------------
    def listar_categorias(self):
        return self.conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()

    def criar_categoria(self, nome, grupo_orcamento="necessidade", orcamento_mensal=0.0):
        cur = self.conn.execute(
            "INSERT INTO categorias (nome, grupo_orcamento, orcamento_mensal) VALUES (?, ?, ?)",
            (nome, grupo_orcamento, orcamento_mensal),
        )
        self.conn.commit()
        return cur.lastrowid

    def atualizar_categoria(self, categoria_id, nome, grupo_orcamento, orcamento_mensal):
        self.conn.execute(
            "UPDATE categorias SET nome=?, grupo_orcamento=?, orcamento_mensal=? WHERE id=?",
            (nome, grupo_orcamento, orcamento_mensal, categoria_id),
        )
        self.conn.commit()

    def excluir_categoria(self, categoria_id):
        self.conn.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        self.conn.commit()

    # ---------------- Receitas ----------------
    def listar_receitas(self, ano=None):
        if ano:
            return self.conn.execute(
                "SELECT r.*, c.nome AS conta_nome FROM receitas r "
                "JOIN contas c ON c.id = r.conta_id "
                "WHERE strftime('%Y', r.data_prevista) = ? ORDER BY r.data_prevista",
                (str(ano),),
            ).fetchall()
        return self.conn.execute(
            "SELECT r.*, c.nome AS conta_nome FROM receitas r "
            "JOIN contas c ON c.id = r.conta_id ORDER BY r.data_prevista"
        ).fetchall()

    def criar_receita(self, descricao, valor, tipo, data_prevista, conta_id):
        cur = self.conn.execute(
            "INSERT INTO receitas (descricao, valor, tipo, data_prevista, conta_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (descricao, valor, tipo, data_prevista, conta_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def marcar_receita_recebida(self, receita_id, recebida=True):
        receita = self.conn.execute(
            "SELECT * FROM receitas WHERE id = ?", (receita_id,)
        ).fetchone()
        if receita is None:
            return
        ja_recebida = bool(receita["recebida"])
        if recebida and not ja_recebida:
            self.ajustar_saldo_conta(receita["conta_id"], receita["valor"])
            self.conn.execute(
                "UPDATE receitas SET recebida=1, data_recebimento=? WHERE id=?",
                (date.today().isoformat(), receita_id),
            )
        elif not recebida and ja_recebida:
            self.ajustar_saldo_conta(receita["conta_id"], -receita["valor"])
            self.conn.execute(
                "UPDATE receitas SET recebida=0, data_recebimento=NULL WHERE id=?",
                (receita_id,),
            )
        self.conn.commit()

    def excluir_receita(self, receita_id):
        receita = self.conn.execute(
            "SELECT * FROM receitas WHERE id = ?", (receita_id,)
        ).fetchone()
        if receita and receita["recebida"]:
            self.ajustar_saldo_conta(receita["conta_id"], -receita["valor"])
        self.conn.execute("DELETE FROM receitas WHERE id = ?", (receita_id,))
        self.conn.commit()

    # ---------------- Despesas ----------------
    def listar_despesas(self, ano=None):
        if ano:
            return self.conn.execute(
                "SELECT d.*, c.nome AS categoria_nome, c.grupo_orcamento, ct.nome AS conta_nome "
                "FROM despesas d "
                "JOIN categorias c ON c.id = d.categoria_id "
                "JOIN contas ct ON ct.id = d.conta_id "
                "WHERE strftime('%Y', d.data_prevista) = ? ORDER BY d.data_prevista",
                (str(ano),),
            ).fetchall()
        return self.conn.execute(
            "SELECT d.*, c.nome AS categoria_nome, c.grupo_orcamento, ct.nome AS conta_nome "
            "FROM despesas d "
            "JOIN categorias c ON c.id = d.categoria_id "
            "JOIN contas ct ON ct.id = d.conta_id "
            "ORDER BY d.data_prevista"
        ).fetchall()

    def criar_despesa_parcelada(
        self, descricao, valor_total, categoria_id, conta_id, data_prevista, parcelas_total=1
    ):
        """Cria uma despesa, gerando N parcelas mensais a partir da data prevista."""
        import uuid
        from dateutil.relativedelta import relativedelta

        compra_grupo = str(uuid.uuid4())
        valor_parcela = round(valor_total / parcelas_total, 2)
        data_base = date.fromisoformat(data_prevista)
        ids = []
        for i in range(parcelas_total):
            data_parcela = data_base + relativedelta(months=i)
            cur = self.conn.execute(
                "INSERT INTO despesas (descricao, valor, categoria_id, conta_id, "
                "data_prevista, parcela_numero, parcelas_total, compra_grupo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    descricao,
                    valor_parcela,
                    categoria_id,
                    conta_id,
                    data_parcela.isoformat(),
                    i + 1,
                    parcelas_total,
                    compra_grupo,
                ),
            )
            ids.append(cur.lastrowid)
        self.conn.commit()
        return ids

    def marcar_despesa_paga(self, despesa_id, paga=True):
        despesa = self.conn.execute(
            "SELECT * FROM despesas WHERE id = ?", (despesa_id,)
        ).fetchone()
        if despesa is None:
            return
        ja_paga = bool(despesa["paga"])
        if paga and not ja_paga:
            self.ajustar_saldo_conta(despesa["conta_id"], -despesa["valor"])
            self.conn.execute(
                "UPDATE despesas SET paga=1, data_pagamento=? WHERE id=?",
                (date.today().isoformat(), despesa_id),
            )
        elif not paga and ja_paga:
            self.ajustar_saldo_conta(despesa["conta_id"], despesa["valor"])
            self.conn.execute(
                "UPDATE despesas SET paga=0, data_pagamento=NULL WHERE id=?",
                (despesa_id,),
            )
        self.conn.commit()

    def excluir_despesa(self, despesa_id):
        despesa = self.conn.execute(
            "SELECT * FROM despesas WHERE id = ?", (despesa_id,)
        ).fetchone()
        if despesa and despesa["paga"]:
            self.ajustar_saldo_conta(despesa["conta_id"], despesa["valor"])
        self.conn.execute("DELETE FROM despesas WHERE id = ?", (despesa_id,))
        self.conn.commit()

    def gasto_por_categoria_mes(self, ano, mes):
        return self.conn.execute(
            "SELECT c.nome, c.grupo_orcamento, c.orcamento_mensal, "
            "COALESCE(SUM(d.valor), 0) AS gasto "
            "FROM categorias c "
            "LEFT JOIN despesas d ON d.categoria_id = c.id "
            "  AND strftime('%Y', d.data_prevista) = ? "
            "  AND strftime('%m', d.data_prevista) = ? "
            "GROUP BY c.id ORDER BY c.nome",
            (str(ano), f"{mes:02d}"),
        ).fetchall()

    # ---------------- Investimentos ----------------
    def listar_investimentos(self, ano=None):
        if ano:
            return self.conn.execute(
                "SELECT * FROM investimentos WHERE strftime('%Y', data) = ? ORDER BY data",
                (str(ano),),
            ).fetchall()
        return self.conn.execute("SELECT * FROM investimentos ORDER BY data").fetchall()

    def criar_investimento(self, descricao, valor, tipo, data, conta_id=None):
        cur = self.conn.execute(
            "INSERT INTO investimentos (descricao, valor, tipo, data, conta_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (descricao, valor, tipo, data, conta_id),
        )
        if conta_id:
            self.ajustar_saldo_conta(conta_id, -valor)
        self.conn.commit()
        return cur.lastrowid

    def excluir_investimento(self, investimento_id):
        inv = self.conn.execute(
            "SELECT * FROM investimentos WHERE id = ?", (investimento_id,)
        ).fetchone()
        if inv and inv["conta_id"]:
            self.ajustar_saldo_conta(inv["conta_id"], inv["valor"])
        self.conn.execute("DELETE FROM investimentos WHERE id = ?", (investimento_id,))
        self.conn.commit()

    def patrimonio_investido_total(self):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(valor), 0) AS total FROM investimentos"
        ).fetchone()
        return row["total"]

    def evolucao_investimentos(self, ano):
        """Retorna saldo acumulado de investimentos mês a mês para um ano."""
        rows = self.conn.execute(
            "SELECT strftime('%m', data) AS mes, SUM(valor) AS total "
            "FROM investimentos WHERE strftime('%Y', data) <= ? "
            "GROUP BY strftime('%Y-%m', data) ORDER BY data",
            (str(ano),),
        ).fetchall()
        return rows

    def close(self):
        self.conn.close()

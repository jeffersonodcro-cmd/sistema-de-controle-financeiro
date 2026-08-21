"""Aplicação web (Flask) do sistema de controle financeiro."""

import secrets
from pathlib import Path

from flask import Flask, g, session

from webapp import database as db
from webapp.auth import bp as auth_bp
from webapp.financeiro import bp as financeiro_bp

SECRET_KEY_PATH = Path.home() / ".controle_financeiro" / "secret_key_web.txt"


def _obter_secret_key():
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()
    chave = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(chave)
    return chave


def criar_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = _obter_secret_key()

    conn_inicial = db.conectar()
    db.inicializar_schema(conn_inicial)
    conn_inicial.close()

    @app.before_request
    def carregar_usuario():
        g.db = db.conectar()
        usuario_id = session.get("usuario_id")
        g.usuario = db.buscar_usuario_por_id(g.db, usuario_id) if usuario_id else None

    @app.teardown_request
    def fechar_conexao(exception=None):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    app.register_blueprint(auth_bp)
    app.register_blueprint(financeiro_bp)

    return app


if __name__ == "__main__":
    aplicativo = criar_app()
    aplicativo.run(debug=True, port=5000)

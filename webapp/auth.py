"""Blueprint de autenticação: registro, login e logout."""

from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from webapp import database as db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar", "")

        erro = None
        if not nome or not email or not senha:
            erro = "Preencha nome, e-mail e senha."
        elif len(senha) < 6:
            erro = "A senha precisa ter pelo menos 6 caracteres."
        elif senha != confirmar:
            erro = "As senhas não coincidem."
        elif db.buscar_usuario_por_email(g.db, email) is not None:
            erro = "Já existe uma conta com esse e-mail."

        if erro:
            flash(erro, "erro")
        else:
            usuario_id = db.criar_usuario(g.db, nome, email, generate_password_hash(senha))
            session.clear()
            session["usuario_id"] = usuario_id
            return redirect(url_for("financeiro.dashboard"))

    return render_template("auth/registro.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = db.buscar_usuario_por_email(g.db, email)
        erro = None
        if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
            erro = "E-mail ou senha inválidos."

        if erro:
            flash(erro, "erro")
        else:
            session.clear()
            session["usuario_id"] = usuario["id"]
            destino = request.args.get("next") or url_for("financeiro.dashboard")
            return redirect(destino)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

"""Blueprint com as telas principais: dashboard, contas, receitas, despesas,
investimentos e metas/orçamento."""

from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from webapp import database as db
from webapp.auth import login_required
from webapp.utils import GRUPOS_ORCAMENTO, NOMES_MESES, ano_atual, formatar_moeda, mes_atual

bp = Blueprint("financeiro", __name__)
bp.add_app_template_filter(formatar_moeda, name="moeda")


def _parse_float(valor, campo):
    try:
        return float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError(f"Valor inválido para '{campo}'.")


@bp.before_request
@login_required
def exigir_login():
    pass


# ---------------- Dashboard ----------------
@bp.route("/")
def dashboard():
    usuario_id = g.usuario["id"]
    ano, mes = ano_atual(), mes_atual()

    saldo = db.saldo_total(g.db, usuario_id)
    despesas = db.listar_despesas(g.db, usuario_id, ano)
    receitas = db.listar_receitas(g.db, usuario_id, ano)
    investido = db.patrimonio_investido_total(g.db, usuario_id)

    gasto_mes = sum(d["valor"] for d in despesas if d["data_prevista"][:7] == f"{ano}-{mes:02d}")
    receita_mes = sum(r["valor"] for r in receitas if r["data_prevista"][:7] == f"{ano}-{mes:02d}")
    pendente_ano = sum(d["valor"] for d in despesas if not d["paga"])

    linhas_categoria = db.gasto_por_categoria_mes(g.db, usuario_id, ano, mes)
    pizza_labels = [l["nome"] for l in linhas_categoria if l["gasto"] > 0]
    pizza_valores = [round(l["gasto"], 2) for l in linhas_categoria if l["gasto"] > 0]

    receitas_mes_map = {i: 0.0 for i in range(1, 13)}
    despesas_mes_map = {i: 0.0 for i in range(1, 13)}
    for r in receitas:
        receitas_mes_map[int(r["data_prevista"][5:7])] += r["valor"]
    for d in despesas:
        despesas_mes_map[int(d["data_prevista"][5:7])] += d["valor"]

    return render_template(
        "dashboard.html",
        saldo=saldo, gasto_mes=gasto_mes, receita_mes=receita_mes,
        pendente_ano=pendente_ano, investido=investido, ano=ano,
        pizza_labels=pizza_labels, pizza_valores=pizza_valores,
        meses_labels=[m[:3] for m in NOMES_MESES],
        receitas_serie=[round(receitas_mes_map[m], 2) for m in range(1, 13)],
        despesas_serie=[round(despesas_mes_map[m], 2) for m in range(1, 13)],
    )


# ---------------- Contas ----------------
@bp.route("/contas", methods=["GET", "POST"])
def contas():
    usuario_id = g.usuario["id"]
    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            if not nome:
                raise ValueError("Informe o nome da conta.")
            tipo = request.form.get("tipo", "conta")
            saldo = _parse_float(request.form.get("saldo_atual") or 0, "saldo")
            limite = _parse_float(request.form.get("limite") or 0, "limite")
            db.criar_conta(g.db, usuario_id, nome, tipo, saldo, limite)
            flash("Conta cadastrada com sucesso.", "sucesso")
        except ValueError as e:
            flash(str(e), "erro")
        return redirect(url_for("financeiro.contas"))

    return render_template("contas.html", contas=db.listar_contas(g.db, usuario_id))


@bp.route("/contas/<int:conta_id>/excluir", methods=["POST"])
def excluir_conta(conta_id):
    try:
        db.excluir_conta(g.db, g.usuario["id"], conta_id)
        flash("Conta excluída.", "sucesso")
    except Exception:
        flash("Não foi possível excluir: existem lançamentos vinculados a essa conta.", "erro")
    return redirect(url_for("financeiro.contas"))


# ---------------- Receitas ----------------
@bp.route("/receitas", methods=["GET", "POST"])
def receitas():
    usuario_id = g.usuario["id"]
    if request.method == "POST":
        try:
            desc = request.form.get("descricao", "").strip()
            if not desc:
                raise ValueError("Informe a descrição.")
            valor = _parse_float(request.form.get("valor"), "valor")
            tipo = request.form.get("tipo", "fixa")
            data_prevista = date.fromisoformat(request.form.get("data_prevista"))
            conta_id = int(request.form.get("conta_id"))
            repetir = request.form.get("repetir") == "on"

            if repetir:
                mes = data_prevista.month
                while mes <= 12:
                    d = data_prevista.replace(month=mes)
                    db.criar_receita(g.db, usuario_id, desc, valor, tipo, d.isoformat(), conta_id)
                    mes += 1
            else:
                db.criar_receita(g.db, usuario_id, desc, valor, tipo, data_prevista.isoformat(), conta_id)
            flash("Receita cadastrada com sucesso.", "sucesso")
        except (ValueError, TypeError):
            flash("Dados inválidos. Confira valor, data e conta selecionada.", "erro")
        return redirect(url_for("financeiro.receitas"))

    return render_template(
        "receitas.html",
        receitas=db.listar_receitas(g.db, usuario_id, ano_atual()),
        contas=db.listar_contas(g.db, usuario_id),
        hoje=date.today().isoformat(),
    )


@bp.route("/receitas/<int:receita_id>/toggle", methods=["POST"])
def toggle_receita(receita_id):
    usuario_id = g.usuario["id"]
    recebida = request.form.get("recebida") == "on"
    db.marcar_receita_recebida(g.db, usuario_id, receita_id, recebida)
    return redirect(url_for("financeiro.receitas"))


@bp.route("/receitas/<int:receita_id>/excluir", methods=["POST"])
def excluir_receita(receita_id):
    db.excluir_receita(g.db, g.usuario["id"], receita_id)
    flash("Receita excluída.", "sucesso")
    return redirect(url_for("financeiro.receitas"))


# ---------------- Despesas ----------------
@bp.route("/despesas", methods=["GET", "POST"])
def despesas():
    usuario_id = g.usuario["id"]
    if request.method == "POST":
        try:
            desc = request.form.get("descricao", "").strip()
            if not desc:
                raise ValueError("Informe a descrição.")
            valor_total = _parse_float(request.form.get("valor_total"), "valor")
            categoria_id = int(request.form.get("categoria_id"))
            conta_id = int(request.form.get("conta_id"))
            data_prevista = date.fromisoformat(request.form.get("data_prevista"))
            parcelas = max(1, int(request.form.get("parcelas") or 1))

            db.criar_despesa_parcelada(
                g.db, usuario_id, desc, valor_total, categoria_id, conta_id,
                data_prevista.isoformat(), parcelas,
            )
            flash("Despesa cadastrada com sucesso.", "sucesso")
        except (ValueError, TypeError):
            flash("Dados inválidos. Confira valor, data, categoria e conta.", "erro")
        return redirect(url_for("financeiro.despesas"))

    despesas_lista = db.listar_despesas(g.db, usuario_id, ano_atual())
    total = sum(d["valor"] for d in despesas_lista)
    total_pago = sum(d["valor"] for d in despesas_lista if d["paga"])

    limites_cartao = db.gasto_por_conta_mes(g.db, usuario_id, ano_atual(), mes_atual())

    return render_template(
        "despesas.html",
        despesas=despesas_lista,
        categorias=db.listar_categorias(g.db, usuario_id),
        contas=db.listar_contas(g.db, usuario_id),
        hoje=date.today().isoformat(),
        total=total, total_pago=total_pago, total_pendente=total - total_pago,
        limites_cartao=limites_cartao,
    )


@bp.route("/despesas/<int:despesa_id>/toggle", methods=["POST"])
def toggle_despesa(despesa_id):
    usuario_id = g.usuario["id"]
    paga = request.form.get("paga") == "on"
    db.marcar_despesa_paga(g.db, usuario_id, despesa_id, paga)
    return redirect(url_for("financeiro.despesas"))


@bp.route("/despesas/<int:despesa_id>/excluir", methods=["POST"])
def excluir_despesa(despesa_id):
    db.excluir_despesa(g.db, g.usuario["id"], despesa_id)
    flash("Despesa excluída.", "sucesso")
    return redirect(url_for("financeiro.despesas"))


# ---------------- Investimentos ----------------
@bp.route("/investimentos", methods=["GET", "POST"])
def investimentos():
    usuario_id = g.usuario["id"]
    if request.method == "POST":
        try:
            desc = request.form.get("descricao", "").strip()
            if not desc:
                raise ValueError("Informe a descrição.")
            valor = _parse_float(request.form.get("valor"), "valor")
            tipo = request.form.get("tipo", "renda_fixa")
            data_lanc = date.fromisoformat(request.form.get("data"))
            conta_raw = request.form.get("conta_id")
            conta_id = int(conta_raw) if conta_raw else None

            db.criar_investimento(g.db, usuario_id, desc, valor, tipo, data_lanc.isoformat(), conta_id)
            flash("Lançamento registrado com sucesso.", "sucesso")
        except (ValueError, TypeError):
            flash("Dados inválidos. Confira valor e data.", "erro")
        return redirect(url_for("financeiro.investimentos"))

    ano = ano_atual()
    investimentos_lista = db.listar_investimentos(g.db, usuario_id, ano)
    rows = db.evolucao_investimentos(g.db, usuario_id, ano)
    acumulado_por_mes = {i: 0.0 for i in range(1, 13)}
    saldo_acumulado = 0.0
    valores_por_mes = {int(r["mes_ref"][5:7]): r["total"] for r in rows}
    for mes in range(1, 13):
        saldo_acumulado += valores_por_mes.get(mes, 0.0)
        acumulado_por_mes[mes] = saldo_acumulado

    return render_template(
        "investimentos.html",
        investimentos=investimentos_lista,
        contas=db.listar_contas(g.db, usuario_id),
        hoje=date.today().isoformat(),
        total=db.patrimonio_investido_total(g.db, usuario_id),
        meses_labels=[m[:3] for m in NOMES_MESES],
        evolucao_serie=[round(acumulado_por_mes[m], 2) for m in range(1, 13)],
        ano=ano,
    )


@bp.route("/investimentos/<int:investimento_id>/excluir", methods=["POST"])
def excluir_investimento(investimento_id):
    db.excluir_investimento(g.db, g.usuario["id"], investimento_id)
    flash("Lançamento excluído.", "sucesso")
    return redirect(url_for("financeiro.investimentos"))


# ---------------- Metas / Orçamento ----------------
@bp.route("/metas", methods=["GET", "POST"])
def metas():
    usuario_id = g.usuario["id"]
    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            if not nome:
                raise ValueError("Informe o nome da categoria.")
            grupo = request.form.get("grupo_orcamento", "necessidade")
            orcamento = _parse_float(request.form.get("orcamento_mensal") or 0, "orçamento")
            db.criar_categoria(g.db, usuario_id, nome, grupo, orcamento)
            flash("Categoria cadastrada com sucesso.", "sucesso")
        except ValueError as e:
            flash(str(e) if "Informe" in str(e) else "Já existe uma categoria com esse nome.", "erro")
        return redirect(url_for("financeiro.metas"))

    ano, mes = ano_atual(), mes_atual()
    linhas = db.gasto_por_categoria_mes(g.db, usuario_id, ano, mes)
    receitas = db.listar_receitas(g.db, usuario_id, ano)
    renda_mensal = sum(r["valor"] for r in receitas if r["data_prevista"][:7] == f"{ano}-{mes:02d}")

    totais_grupo = {"necessidade": 0.0, "desejo": 0.0, "poupanca": 0.0}
    for linha in linhas:
        totais_grupo[linha["grupo_orcamento"]] = totais_grupo.get(linha["grupo_orcamento"], 0.0) + linha["gasto"]

    recomendado = {
        "necessidade": renda_mensal * 0.5,
        "desejo": renda_mensal * 0.3,
        "poupanca": renda_mensal * 0.2,
    }

    return render_template(
        "metas.html",
        linhas=linhas, grupos=GRUPOS_ORCAMENTO,
        totais_grupo=totais_grupo, recomendado=recomendado,
        renda_mensal=renda_mensal,
    )


@bp.route("/metas/<int:categoria_id>/excluir", methods=["POST"])
def excluir_categoria(categoria_id):
    try:
        db.excluir_categoria(g.db, g.usuario["id"], categoria_id)
        flash("Categoria excluída.", "sucesso")
    except Exception:
        flash(
            "Não é possível excluir: há despesas lançadas nessa categoria. "
            "Exclua ou mova essas despesas antes.",
            "erro",
        )
    return redirect(url_for("financeiro.metas"))


# ---------------- Reset ----------------
@bp.route("/resetar", methods=["POST"])
def resetar():
    confirmacao = request.form.get("confirmacao", "")
    if confirmacao != "RESETAR":
        flash('Digite exatamente "RESETAR" para confirmar. Nenhum dado foi apagado.', "erro")
        return redirect(url_for("financeiro.metas"))
    db.resetar_tudo(g.db, g.usuario["id"])
    flash("Todos os seus dados foram apagados. O app voltou ao estado inicial.", "sucesso")
    return redirect(url_for("financeiro.dashboard"))

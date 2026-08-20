"""Funções utilitárias compartilhadas pela interface."""

from datetime import date


def formatar_moeda(valor: float) -> str:
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ano_atual() -> int:
    return date.today().year


def mes_atual() -> int:
    return date.today().month


NOMES_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

GRUPOS_ORCAMENTO = {
    "necessidade": "Necessidades (50%)",
    "desejo": "Desejos (30%)",
    "poupanca": "Poupança/Investimento (20%)",
}

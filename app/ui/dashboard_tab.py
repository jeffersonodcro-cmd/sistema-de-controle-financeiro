"""Aba de Dashboard: visão geral com saldo, gráficos e resumo do orçamento."""

import customtkinter as ctk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.utils import formatar_moeda, ano_atual, mes_atual, NOMES_MESES


class DashboardTab(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=10, pady=10)

        self.graficos_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.graficos_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.graficos_frame.columnconfigure(0, weight=1)
        self.graficos_frame.columnconfigure(1, weight=1)

        self.grafico_pizza_frame = ctk.CTkFrame(self.graficos_frame)
        self.grafico_pizza_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        self.grafico_barras_frame = ctk.CTkFrame(self.graficos_frame)
        self.grafico_barras_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

    def _card(self, titulo, valor, cor="#3b82f6"):
        card = ctk.CTkFrame(self.cards_frame, corner_radius=10)
        card.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card, text=titulo, font=("", 12)).pack(pady=(10, 0))
        ctk.CTkLabel(card, text=valor, font=("", 18, "bold"), text_color=cor).pack(pady=(0, 10))

    def refresh(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        ano, mes = ano_atual(), mes_atual()
        saldo_total = self.db.saldo_total()
        despesas = self.db.listar_despesas(ano)
        receitas = self.db.listar_receitas(ano)
        investido = self.db.patrimonio_investido_total()

        gasto_mes = sum(
            d["valor"] for d in despesas if d["data_prevista"][:7] == f"{ano}-{mes:02d}"
        )
        receita_mes = sum(
            r["valor"] for r in receitas if r["data_prevista"][:7] == f"{ano}-{mes:02d}"
        )
        pendente_ano = sum(d["valor"] for d in despesas if not d["paga"])

        self._card("Saldo total em contas", formatar_moeda(saldo_total))
        self._card("Receita prevista (mês)", formatar_moeda(receita_mes), "#2fa84f")
        self._card("Despesas previstas (mês)", formatar_moeda(gasto_mes), "#d9534f")
        self._card("Planejado a pagar no ano", formatar_moeda(pendente_ano), "#f0ad4e")
        self._card("Patrimônio investido", formatar_moeda(investido), "#3b82f6")

        self._desenhar_pizza(ano, mes)
        self._desenhar_barras(ano)

    def _desenhar_pizza(self, ano, mes):
        for widget in self.grafico_pizza_frame.winfo_children():
            widget.destroy()

        linhas = self.db.gasto_por_categoria_mes(ano, mes)
        dados = [(r["nome"], r["gasto"]) for r in linhas if r["gasto"] > 0]

        fig = Figure(figsize=(5, 3.4), dpi=100)
        ax = fig.add_subplot(111)
        if dados:
            labels = [d[0] for d in dados]
            valores = [d[1] for d in dados]
            ax.pie(valores, labels=labels, autopct="%1.0f%%", textprops={"fontsize": 8})
        else:
            ax.text(0.5, 0.5, "Sem despesas neste mês", ha="center", va="center")
            ax.axis("off")
        ax.set_title(f"Gastos por categoria - {NOMES_MESES[mes - 1]}/{ano}")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.grafico_pizza_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _desenhar_barras(self, ano):
        for widget in self.grafico_barras_frame.winfo_children():
            widget.destroy()

        receitas = self.db.listar_receitas(ano)
        despesas = self.db.listar_despesas(ano)

        receitas_mes = {i: 0.0 for i in range(1, 13)}
        despesas_mes = {i: 0.0 for i in range(1, 13)}
        for r in receitas:
            mes = int(r["data_prevista"][5:7])
            receitas_mes[mes] += r["valor"]
        for d in despesas:
            mes = int(d["data_prevista"][5:7])
            despesas_mes[mes] += d["valor"]

        fig = Figure(figsize=(5, 3.4), dpi=100)
        ax = fig.add_subplot(111)
        meses_labels = [m[:3] for m in NOMES_MESES]
        largura = 0.35
        posicoes = range(1, 13)
        ax.bar(
            [p - largura / 2 for p in posicoes],
            [receitas_mes[m] for m in posicoes],
            width=largura, label="Receitas", color="#2fa84f",
        )
        ax.bar(
            [p + largura / 2 for p in posicoes],
            [despesas_mes[m] for m in posicoes],
            width=largura, label="Despesas", color="#d9534f",
        )
        ax.set_xticks(list(posicoes))
        ax.set_xticklabels(meses_labels, rotation=45)
        ax.set_title(f"Receitas x Despesas - {ano}")
        ax.legend(fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.grafico_barras_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

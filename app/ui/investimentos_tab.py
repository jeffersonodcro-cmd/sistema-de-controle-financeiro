"""Aba de Investimentos: aportes/resgates e evolução do patrimônio."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.utils import formatar_moeda, ano_atual, NOMES_MESES

TIPOS_INVESTIMENTO = ["renda_fixa", "renda_variavel", "fundos", "previdencia", "outro"]


class InvestimentosTab(ctk.CTkFrame):
    def __init__(self, master, db, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Novo aporte / resgate", font=("", 15, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", padx=5, pady=(5, 10)
        )

        ctk.CTkLabel(form, text="Descrição").grid(row=1, column=0, padx=5, sticky="w")
        self.desc_entry = ctk.CTkEntry(form, placeholder_text="Ex: Aporte Tesouro Direto")
        self.desc_entry.grid(row=2, column=0, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Valor (R$, use negativo p/ resgate)").grid(row=1, column=1, padx=5, sticky="w")
        self.valor_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.valor_entry.grid(row=2, column=1, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Tipo").grid(row=1, column=2, padx=5, sticky="w")
        self.tipo_combo = ctk.CTkComboBox(form, values=TIPOS_INVESTIMENTO)
        self.tipo_combo.grid(row=2, column=2, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Data").grid(row=1, column=3, padx=5, sticky="w")
        self.data_entry = ctk.CTkEntry(form, placeholder_text="AAAA-MM-DD")
        self.data_entry.insert(0, date.today().isoformat())
        self.data_entry.grid(row=2, column=3, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Debitar de conta (opcional)").grid(row=1, column=4, padx=5, sticky="w")
        self.conta_combo = ctk.CTkComboBox(form, values=["(nenhuma)"])
        self.conta_combo.grid(row=2, column=4, padx=5, pady=(0, 10))

        ctk.CTkButton(form, text="Adicionar", command=self._adicionar).grid(
            row=2, column=5, padx=10
        )

        self.total_label = ctk.CTkLabel(self, text="", font=("", 15, "bold"))
        self.total_label.pack(anchor="w", padx=10, pady=(0, 5))

        self.grafico_frame = ctk.CTkFrame(self)
        self.grafico_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="Lançamentos de investimento")
        self.lista_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _contas_map(self):
        return {c["nome"]: c["id"] for c in self.db.listar_contas()}

    def _adicionar(self):
        desc = self.desc_entry.get().strip()
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.")
            return
        try:
            valor = float(self.valor_entry.get().replace(",", "."))
            data = date.fromisoformat(self.data_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Valor ou data inválidos.")
            return
        contas_map = self._contas_map()
        conta_nome = self.conta_combo.get()
        conta_id = contas_map.get(conta_nome)

        self.db.criar_investimento(desc, valor, self.tipo_combo.get(), data.isoformat(), conta_id)
        self.desc_entry.delete(0, "end")
        self.valor_entry.delete(0, "end")
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        contas_map = self._contas_map()
        opcoes = ["(nenhuma)"] + list(contas_map.keys())
        self.conta_combo.configure(values=opcoes)
        if self.conta_combo.get() not in opcoes:
            self.conta_combo.set("(nenhuma)")

        total = self.db.patrimonio_investido_total()
        self.total_label.configure(text=f"Patrimônio investido total: {formatar_moeda(total)}")

        self._desenhar_grafico()

        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        investimentos = self.db.listar_investimentos(ano_atual())
        if not investimentos:
            ctk.CTkLabel(self.lista_frame, text="Nenhum investimento cadastrado para este ano.").pack(pady=10)
            return

        for inv in investimentos:
            row = ctk.CTkFrame(self.lista_frame)
            row.pack(fill="x", pady=3)
            cor = "#2fa84f" if inv["valor"] >= 0 else "#d9534f"
            ctk.CTkLabel(row, text=inv["data"], width=90, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=inv["descricao"], width=180, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=inv["tipo"], width=110, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=formatar_moeda(inv["valor"]), width=110, anchor="w", text_color=cor).pack(
                side="left", padx=4
            )
            ctk.CTkButton(
                row, text="Excluir", width=70, fg_color="#d9534f", hover_color="#b52b2b",
                command=lambda iid=inv["id"]: self._excluir(iid),
            ).pack(side="left", padx=4)

    def _desenhar_grafico(self):
        for widget in self.grafico_frame.winfo_children():
            widget.destroy()

        ano = ano_atual()
        rows = self.db.evolucao_investimentos(ano)
        acumulado = {i: 0.0 for i in range(1, 13)}
        saldo = 0.0
        vistos = {int(r["mes"]): r["total"] for r in rows}
        for mes in range(1, 13):
            saldo += vistos.get(mes, 0.0)
            acumulado[mes] = saldo

        fig = Figure(figsize=(6, 2.6), dpi=100)
        ax = fig.add_subplot(111)
        meses_labels = [m[:3] for m in NOMES_MESES]
        valores = [acumulado[m] for m in range(1, 13)]
        ax.plot(meses_labels, valores, marker="o", color="#3b82f6")
        ax.fill_between(meses_labels, valores, color="#3b82f6", alpha=0.15)
        ax.set_title(f"Evolução do patrimônio investido em {ano}")
        ax.tick_params(axis="x", labelrotation=45)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.grafico_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x")

    def _excluir(self, investimento_id):
        if messagebox.askyesno("Confirmar", "Excluir este lançamento?"):
            self.db.excluir_investimento(investimento_id)
            self.refresh()
            if self.on_change:
                self.on_change()

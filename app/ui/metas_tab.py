"""Aba de Metas: orçamento por categoria e visão 50/30/20."""

import customtkinter as ctk
from tkinter import messagebox

from app.utils import formatar_moeda, ano_atual, mes_atual, GRUPOS_ORCAMENTO


class MetasTab(ctk.CTkFrame):
    def __init__(self, master, db, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Nova categoria / orçamento mensal", font=("", 15, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 10)
        )

        ctk.CTkLabel(form, text="Nome").grid(row=1, column=0, padx=5, sticky="w")
        self.nome_entry = ctk.CTkEntry(form, placeholder_text="Ex: Mercado")
        self.nome_entry.grid(row=2, column=0, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Grupo (50/30/20)").grid(row=1, column=1, padx=5, sticky="w")
        self.grupo_combo = ctk.CTkComboBox(form, values=list(GRUPOS_ORCAMENTO.values()))
        self.grupo_combo.grid(row=2, column=1, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Orçamento mensal (R$)").grid(row=1, column=2, padx=5, sticky="w")
        self.orcamento_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.orcamento_entry.grid(row=2, column=2, padx=5, pady=(0, 10))

        ctk.CTkButton(form, text="Adicionar", command=self._adicionar).grid(row=2, column=3, padx=10)

        self.resumo_frame = ctk.CTkFrame(self)
        self.resumo_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="Metas por categoria (mês atual)")
        self.lista_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _grupo_chave(self, label):
        for chave, texto in GRUPOS_ORCAMENTO.items():
            if texto == label:
                return chave
        return "necessidade"

    def _adicionar(self):
        nome = self.nome_entry.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da categoria.")
            return
        try:
            orcamento = float(self.orcamento_entry.get().replace(",", ".") or 0)
        except ValueError:
            messagebox.showerror("Erro", "Orçamento inválido.")
            return
        grupo = self._grupo_chave(self.grupo_combo.get())
        try:
            self.db.criar_categoria(nome, grupo, orcamento)
        except Exception:
            messagebox.showerror("Erro", "Já existe uma categoria com esse nome.")
            return
        self.nome_entry.delete(0, "end")
        self.orcamento_entry.delete(0, "end")
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        for widget in self.resumo_frame.winfo_children():
            widget.destroy()
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        ano, mes = ano_atual(), mes_atual()
        linhas = self.db.gasto_por_categoria_mes(ano, mes)

        receitas = self.db.listar_receitas(ano)
        renda_mensal = sum(
            r["valor"] for r in receitas
            if r["data_prevista"][:7] == f"{ano}-{mes:02d}"
        )

        totais_grupo = {"necessidade": 0.0, "desejo": 0.0, "poupanca": 0.0}
        for linha in linhas:
            totais_grupo[linha["grupo_orcamento"]] = totais_grupo.get(
                linha["grupo_orcamento"], 0.0
            ) + linha["gasto"]

        recomendado = {"necessidade": renda_mensal * 0.5, "desejo": renda_mensal * 0.3, "poupanca": renda_mensal * 0.2}

        ctk.CTkLabel(
            self.resumo_frame, text=f"Renda prevista no mês: {formatar_moeda(renda_mensal)}",
            font=("", 14, "bold"),
        ).pack(anchor="w", padx=5, pady=(5, 10))

        for chave, texto in GRUPOS_ORCAMENTO.items():
            gasto = totais_grupo.get(chave, 0.0)
            meta = recomendado[chave]
            pct = (gasto / meta * 100) if meta > 0 else 0
            row = ctk.CTkFrame(self.resumo_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=3)
            ctk.CTkLabel(row, text=texto, width=220, anchor="w").pack(side="left")
            barra = ctk.CTkProgressBar(row, width=250)
            barra.set(min(pct / 100, 1.0))
            if pct > 100:
                barra.configure(progress_color="#d9534f")
            barra.pack(side="left", padx=10)
            ctk.CTkLabel(
                row, text=f"{formatar_moeda(gasto)} / {formatar_moeda(meta)} ({pct:.0f}%)"
            ).pack(side="left", padx=10)

        if not linhas:
            ctk.CTkLabel(self.lista_frame, text="Cadastre categorias para ver metas.").pack(pady=10)
            return

        header = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        for text, w in [("Categoria", 140), ("Grupo", 140), ("Orçamento", 100), ("Gasto no mês", 100), ("", 220)]:
            ctk.CTkLabel(header, text=text, width=w, font=("", 12, "bold")).pack(side="left", padx=4)

        for linha in linhas:
            row = ctk.CTkFrame(self.lista_frame)
            row.pack(fill="x", pady=3)
            orcamento = linha["orcamento_mensal"] or 0
            gasto = linha["gasto"]
            pct = (gasto / orcamento * 100) if orcamento > 0 else 0
            ctk.CTkLabel(row, text=linha["nome"], width=140, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=GRUPOS_ORCAMENTO[linha["grupo_orcamento"]], width=140, anchor="w").pack(
                side="left", padx=4
            )
            ctk.CTkLabel(row, text=formatar_moeda(orcamento), width=100, anchor="w").pack(side="left", padx=4)
            cor = "#d9534f" if orcamento and gasto > orcamento else None
            ctk.CTkLabel(row, text=formatar_moeda(gasto), width=100, anchor="w", text_color=cor).pack(
                side="left", padx=4
            )
            if orcamento > 0:
                barra = ctk.CTkProgressBar(row, width=180)
                barra.set(min(pct / 100, 1.0))
                if pct > 100:
                    barra.configure(progress_color="#d9534f")
                barra.pack(side="left", padx=4)
                ctk.CTkLabel(row, text=f"{pct:.0f}%", width=40).pack(side="left", padx=4)

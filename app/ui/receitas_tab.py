"""Aba de Receitas: fixas e variáveis planejadas ao longo do ano."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

from app.utils import formatar_moeda, ano_atual


class ReceitasTab(ctk.CTkFrame):
    def __init__(self, master, db, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Nova receita", font=("", 15, "bold")).grid(
            row=0, column=0, columnspan=5, sticky="w", padx=5, pady=(5, 10)
        )

        ctk.CTkLabel(form, text="Descrição").grid(row=1, column=0, padx=5, sticky="w")
        self.desc_entry = ctk.CTkEntry(form, placeholder_text="Ex: Salário")
        self.desc_entry.grid(row=2, column=0, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Valor (R$)").grid(row=1, column=1, padx=5, sticky="w")
        self.valor_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.valor_entry.grid(row=2, column=1, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Tipo").grid(row=1, column=2, padx=5, sticky="w")
        self.tipo_combo = ctk.CTkComboBox(form, values=["fixa", "variavel"])
        self.tipo_combo.grid(row=2, column=2, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Data prevista").grid(row=1, column=3, padx=5, sticky="w")
        self.data_entry = ctk.CTkEntry(form, placeholder_text="AAAA-MM-DD")
        self.data_entry.insert(0, date.today().isoformat())
        self.data_entry.grid(row=2, column=3, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Conta").grid(row=1, column=4, padx=5, sticky="w")
        self.conta_combo = ctk.CTkComboBox(form, values=[])
        self.conta_combo.grid(row=2, column=4, padx=5, pady=(0, 10))

        self.repetir_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Repetir todo mês até dez/ano", variable=self.repetir_var
        ).grid(row=2, column=5, padx=10)

        ctk.CTkButton(form, text="Adicionar", command=self._adicionar).grid(
            row=2, column=6, padx=10
        )

        self.resumo_label = ctk.CTkLabel(self, text="", font=("", 13, "bold"))
        self.resumo_label.pack(anchor="w", padx=10)

        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="Receitas do ano")
        self.lista_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _contas_map(self):
        contas = self.db.listar_contas()
        return {c["nome"]: c["id"] for c in contas}

    def _adicionar(self):
        desc = self.desc_entry.get().strip()
        contas_map = self._contas_map()
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.")
            return
        if not contas_map:
            messagebox.showwarning("Atenção", "Cadastre uma conta antes.")
            return
        try:
            valor = float(self.valor_entry.get().replace(",", "."))
            data_prevista = date.fromisoformat(self.data_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Valor ou data inválidos (use AAAA-MM-DD).")
            return
        conta_nome = self.conta_combo.get()
        if conta_nome not in contas_map:
            messagebox.showwarning("Atenção", "Selecione uma conta válida.")
            return
        conta_id = contas_map[conta_nome]
        tipo = self.tipo_combo.get()

        if self.repetir_var.get():
            mes = data_prevista.month
            ano = data_prevista.year
            while mes <= 12:
                d = data_prevista.replace(month=mes)
                self.db.criar_receita(desc, valor, tipo, d.isoformat(), conta_id)
                mes += 1
        else:
            self.db.criar_receita(desc, valor, tipo, data_prevista.isoformat(), conta_id)

        self.desc_entry.delete(0, "end")
        self.valor_entry.delete(0, "end")
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        contas_map = self._contas_map()
        self.conta_combo.configure(values=list(contas_map.keys()))
        if contas_map and self.conta_combo.get() not in contas_map:
            self.conta_combo.set(list(contas_map.keys())[0])

        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        receitas = self.db.listar_receitas(ano_atual())
        if not receitas:
            ctk.CTkLabel(self.lista_frame, text="Nenhuma receita cadastrada para este ano.").pack(pady=10)
            self.resumo_label.configure(text="")
            return

        total = sum(r["valor"] for r in receitas)
        total_recebido = sum(r["valor"] for r in receitas if r["recebida"])
        total_a_receber = total - total_recebido
        self.resumo_label.configure(
            text=(
                f"Total previsto no ano: {formatar_moeda(total)}   |   "
                f"Já recebido: {formatar_moeda(total_recebido)}   |   "
                f"Ainda a receber: {formatar_moeda(total_a_receber)}"
            )
        )

        for r in receitas:
            row = ctk.CTkFrame(self.lista_frame)
            row.pack(fill="x", pady=3)
            status = "Recebida" if r["recebida"] else "Prevista"
            cor = "#2fa84f" if r["recebida"] else "#888888"
            ctk.CTkLabel(row, text=r["data_prevista"], width=90, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=r["descricao"], width=180, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=r["tipo"], width=70, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=formatar_moeda(r["valor"]), width=110, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=r["conta_nome"], width=110, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=status, width=80, anchor="w", text_color=cor).pack(side="left", padx=4)

            var = ctk.BooleanVar(value=bool(r["recebida"]))
            ctk.CTkCheckBox(
                row, text="Recebida", variable=var,
                command=lambda rid=r["id"], v=var: self._toggle(rid, v.get()),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                row, text="Excluir", width=70, fg_color="#d9534f", hover_color="#b52b2b",
                command=lambda rid=r["id"]: self._excluir(rid),
            ).pack(side="left", padx=4)

    def _toggle(self, receita_id, recebida):
        self.db.marcar_receita_recebida(receita_id, recebida)
        self.refresh()
        if self.on_change:
            self.on_change()

    def _excluir(self, receita_id):
        if messagebox.askyesno("Confirmar", "Excluir esta receita?"):
            self.db.excluir_receita(receita_id)
            self.refresh()
            if self.on_change:
                self.on_change()

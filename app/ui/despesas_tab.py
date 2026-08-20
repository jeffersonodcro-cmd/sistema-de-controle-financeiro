"""Aba de Despesas: lançamentos previstos para o ano, incluindo parceladas."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

from app.utils import formatar_moeda, ano_atual


class DespesasTab(ctk.CTkFrame):
    def __init__(self, master, db, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Nova despesa", font=("", 15, "bold")).grid(
            row=0, column=0, columnspan=6, sticky="w", padx=5, pady=(5, 10)
        )

        ctk.CTkLabel(form, text="Descrição").grid(row=1, column=0, padx=5, sticky="w")
        self.desc_entry = ctk.CTkEntry(form, placeholder_text="Ex: Aluguel")
        self.desc_entry.grid(row=2, column=0, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Valor total (R$)").grid(row=1, column=1, padx=5, sticky="w")
        self.valor_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.valor_entry.grid(row=2, column=1, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Categoria").grid(row=1, column=2, padx=5, sticky="w")
        self.categoria_combo = ctk.CTkComboBox(form, values=[])
        self.categoria_combo.grid(row=2, column=2, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Conta/Cartão").grid(row=1, column=3, padx=5, sticky="w")
        self.conta_combo = ctk.CTkComboBox(form, values=[])
        self.conta_combo.grid(row=2, column=3, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="1ª data prevista").grid(row=1, column=4, padx=5, sticky="w")
        self.data_entry = ctk.CTkEntry(form, placeholder_text="AAAA-MM-DD")
        self.data_entry.insert(0, date.today().isoformat())
        self.data_entry.grid(row=2, column=4, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Parcelas").grid(row=1, column=5, padx=5, sticky="w")
        self.parcelas_entry = ctk.CTkEntry(form, placeholder_text="1")
        self.parcelas_entry.insert(0, "1")
        self.parcelas_entry.grid(row=2, column=5, padx=5, pady=(0, 10))

        ctk.CTkButton(form, text="Adicionar", command=self._adicionar).grid(
            row=2, column=6, padx=10
        )

        self.resumo_label = ctk.CTkLabel(self, text="", font=("", 13, "bold"))
        self.resumo_label.pack(anchor="w", padx=10)

        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="Despesas do ano")
        self.lista_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _categorias_map(self):
        return {c["nome"]: c["id"] for c in self.db.listar_categorias()}

    def _contas_map(self):
        return {c["nome"]: c["id"] for c in self.db.listar_contas()}

    def _adicionar(self):
        desc = self.desc_entry.get().strip()
        cat_map = self._categorias_map()
        conta_map = self._contas_map()
        if not desc:
            messagebox.showwarning("Atenção", "Informe a descrição.")
            return
        if not cat_map or not conta_map:
            messagebox.showwarning("Atenção", "Cadastre categorias e contas antes.")
            return
        try:
            valor_total = float(self.valor_entry.get().replace(",", "."))
            data_prevista = date.fromisoformat(self.data_entry.get().strip())
            parcelas = int(self.parcelas_entry.get().strip() or 1)
        except ValueError:
            messagebox.showerror("Erro", "Valor, data ou parcelas inválidos.")
            return
        categoria = self.categoria_combo.get()
        conta = self.conta_combo.get()
        if categoria not in cat_map or conta not in conta_map:
            messagebox.showwarning("Atenção", "Selecione categoria e conta válidas.")
            return

        self.db.criar_despesa_parcelada(
            desc, valor_total, cat_map[categoria], conta_map[conta],
            data_prevista.isoformat(), max(1, parcelas),
        )
        self.desc_entry.delete(0, "end")
        self.valor_entry.delete(0, "end")
        self.parcelas_entry.delete(0, "end")
        self.parcelas_entry.insert(0, "1")
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        cat_map = self._categorias_map()
        conta_map = self._contas_map()
        self.categoria_combo.configure(values=list(cat_map.keys()))
        self.conta_combo.configure(values=list(conta_map.keys()))
        if cat_map and self.categoria_combo.get() not in cat_map:
            self.categoria_combo.set(list(cat_map.keys())[0])
        if conta_map and self.conta_combo.get() not in conta_map:
            self.conta_combo.set(list(conta_map.keys())[0])

        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        despesas = self.db.listar_despesas(ano_atual())
        if not despesas:
            ctk.CTkLabel(self.lista_frame, text="Nenhuma despesa cadastrada para este ano.").pack(pady=10)
            self.resumo_label.configure(text="")
            return

        total = sum(d["valor"] for d in despesas)
        total_pago = sum(d["valor"] for d in despesas if d["paga"])
        total_pendente = total - total_pago
        self.resumo_label.configure(
            text=(
                f"Total previsto no ano: {formatar_moeda(total)}   |   "
                f"Já pago: {formatar_moeda(total_pago)}   |   "
                f"Ainda planejado (não pago): {formatar_moeda(total_pendente)}"
            )
        )

        for d in despesas:
            row = ctk.CTkFrame(self.lista_frame)
            row.pack(fill="x", pady=3)
            status = "Paga" if d["paga"] else "Prevista"
            cor = "#2fa84f" if d["paga"] else "#888888"
            parcela_txt = f"{d['parcela_numero']}/{d['parcelas_total']}" if d["parcelas_total"] > 1 else "-"
            ctk.CTkLabel(row, text=d["data_prevista"], width=90, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=d["descricao"], width=160, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=d["categoria_nome"], width=110, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=formatar_moeda(d["valor"]), width=100, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=parcela_txt, width=50, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=d["conta_nome"], width=100, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=status, width=70, anchor="w", text_color=cor).pack(side="left", padx=4)

            var = ctk.BooleanVar(value=bool(d["paga"]))
            ctk.CTkCheckBox(
                row, text="Paga", variable=var,
                command=lambda did=d["id"], v=var: self._toggle(did, v.get()),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                row, text="Excluir", width=70, fg_color="#d9534f", hover_color="#b52b2b",
                command=lambda did=d["id"]: self._excluir(did),
            ).pack(side="left", padx=4)

    def _toggle(self, despesa_id, paga):
        self.db.marcar_despesa_paga(despesa_id, paga)
        self.refresh()
        if self.on_change:
            self.on_change()

    def _excluir(self, despesa_id):
        if messagebox.askyesno("Confirmar", "Excluir esta despesa/parcela?"):
            self.db.excluir_despesa(despesa_id)
            self.refresh()
            if self.on_change:
                self.on_change()

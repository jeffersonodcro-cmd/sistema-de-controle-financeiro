"""Aba de Contas e Cartões: saldo em conta atualizado manualmente."""

import customtkinter as ctk
from tkinter import messagebox

from app.utils import formatar_moeda


class ContasTab(ctk.CTkFrame):
    def __init__(self, master, db, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.on_change = on_change
        self._build()
        self.refresh()

    def _build(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Nova conta / cartão", font=("", 15, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 10)
        )

        ctk.CTkLabel(form, text="Nome").grid(row=1, column=0, padx=5, sticky="w")
        self.nome_entry = ctk.CTkEntry(form, placeholder_text="Ex: Conta Corrente")
        self.nome_entry.grid(row=2, column=0, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Tipo").grid(row=1, column=1, padx=5, sticky="w")
        self.tipo_combo = ctk.CTkComboBox(form, values=["conta", "cartao"])
        self.tipo_combo.grid(row=2, column=1, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Saldo atual (R$)").grid(row=1, column=2, padx=5, sticky="w")
        self.saldo_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.saldo_entry.grid(row=2, column=2, padx=5, pady=(0, 10))

        ctk.CTkLabel(form, text="Limite (cartão)").grid(row=1, column=3, padx=5, sticky="w")
        self.limite_entry = ctk.CTkEntry(form, placeholder_text="0.00")
        self.limite_entry.grid(row=2, column=3, padx=5, pady=(0, 10))

        ctk.CTkButton(form, text="Adicionar", command=self._adicionar).grid(
            row=2, column=4, padx=10
        )

        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="Contas cadastradas")
        self.lista_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _adicionar(self):
        nome = self.nome_entry.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da conta.")
            return
        try:
            saldo = float(self.saldo_entry.get().replace(",", ".") or 0)
            limite = float(self.limite_entry.get().replace(",", ".") or 0)
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos.")
            return
        self.db.criar_conta(nome, self.tipo_combo.get(), saldo, limite)
        self.nome_entry.delete(0, "end")
        self.saldo_entry.delete(0, "end")
        self.limite_entry.delete(0, "end")
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        contas = self.db.listar_contas()
        if not contas:
            ctk.CTkLabel(self.lista_frame, text="Nenhuma conta cadastrada ainda.").pack(pady=10)
            return

        header = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        for text, w in [("Nome", 20), ("Tipo", 10), ("Saldo", 15), ("Limite", 15), ("", 10)]:
            ctk.CTkLabel(header, text=text, width=w * 8, font=("", 12, "bold")).pack(
                side="left", padx=4
            )

        for conta in contas:
            row = ctk.CTkFrame(self.lista_frame)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=conta["nome"], width=160, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=conta["tipo"], width=80, anchor="w").pack(side="left", padx=4)
            cor = "#2fa84f" if conta["saldo_atual"] >= 0 else "#d9534f"
            ctk.CTkLabel(
                row, text=formatar_moeda(conta["saldo_atual"]), width=120,
                anchor="w", text_color=cor,
            ).pack(side="left", padx=4)
            limite_txt = formatar_moeda(conta["limite"]) if conta["tipo"] == "cartao" else "-"
            ctk.CTkLabel(row, text=limite_txt, width=120, anchor="w").pack(side="left", padx=4)
            ctk.CTkButton(
                row, text="Excluir", width=80, fg_color="#d9534f", hover_color="#b52b2b",
                command=lambda c=conta: self._excluir(c["id"]),
            ).pack(side="left", padx=4)

    def _excluir(self, conta_id):
        if messagebox.askyesno("Confirmar", "Excluir esta conta? Lançamentos vinculados também usam este ID."):
            try:
                self.db.excluir_conta(conta_id)
            except Exception as exc:
                messagebox.showerror("Erro", f"Não foi possível excluir: {exc}")
            self.refresh()
            if self.on_change:
                self.on_change()

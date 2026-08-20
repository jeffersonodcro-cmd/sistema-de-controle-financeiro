"""Janela principal do sistema de controle financeiro."""

import customtkinter as ctk

from app.database import Database
from app.ui.dashboard_tab import DashboardTab
from app.ui.contas_tab import ContasTab
from app.ui.receitas_tab import ReceitasTab
from app.ui.despesas_tab import DespesasTab
from app.ui.investimentos_tab import InvestimentosTab
from app.ui.metas_tab import MetasTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Controle Financeiro Pessoal")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        self.db = Database()

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Dashboard")
        self.tabview.add("Contas e Cartões")
        self.tabview.add("Receitas")
        self.tabview.add("Despesas")
        self.tabview.add("Investimentos")
        self.tabview.add("Metas / Orçamento")

        self.dashboard_tab = DashboardTab(self.tabview.tab("Dashboard"), self.db)
        self.dashboard_tab.pack(fill="both", expand=True)

        self.contas_tab = ContasTab(
            self.tabview.tab("Contas e Cartões"), self.db, on_change=self._refresh_all
        )
        self.contas_tab.pack(fill="both", expand=True)

        self.receitas_tab = ReceitasTab(
            self.tabview.tab("Receitas"), self.db, on_change=self._refresh_all
        )
        self.receitas_tab.pack(fill="both", expand=True)

        self.despesas_tab = DespesasTab(
            self.tabview.tab("Despesas"), self.db, on_change=self._refresh_all
        )
        self.despesas_tab.pack(fill="both", expand=True)

        self.investimentos_tab = InvestimentosTab(
            self.tabview.tab("Investimentos"), self.db, on_change=self._refresh_all
        )
        self.investimentos_tab.pack(fill="both", expand=True)

        self.metas_tab = MetasTab(
            self.tabview.tab("Metas / Orçamento"), self.db, on_change=self._refresh_all
        )
        self.metas_tab.pack(fill="both", expand=True)

        self.tabview.configure(command=self._on_tab_change)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_tab_change(self):
        aba = self.tabview.get()
        if aba == "Dashboard":
            self.dashboard_tab.refresh()
        elif aba == "Contas e Cartões":
            self.contas_tab.refresh()
        elif aba == "Receitas":
            self.receitas_tab.refresh()
        elif aba == "Despesas":
            self.despesas_tab.refresh()
        elif aba == "Investimentos":
            self.investimentos_tab.refresh()
        elif aba == "Metas / Orçamento":
            self.metas_tab.refresh()

    def _refresh_all(self):
        self.dashboard_tab.refresh()
        self.contas_tab.refresh()
        self.receitas_tab.refresh()
        self.despesas_tab.refresh()
        self.investimentos_tab.refresh()
        self.metas_tab.refresh()

    def _on_close(self):
        self.db.close()
        self.destroy()

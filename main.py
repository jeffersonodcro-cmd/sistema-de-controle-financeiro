"""Ponto de entrada do sistema de controle financeiro pessoal."""

from app.ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()

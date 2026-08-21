"""Ponto de entrada da versão web (Flask) do sistema de controle financeiro."""

import threading
import webbrowser

from webapp.app import criar_app


def main():
    app = criar_app()
    url = "http://127.0.0.1:5000/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(debug=False, port=5000)


if __name__ == "__main__":
    main()

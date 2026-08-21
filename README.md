# Sistema de Controle Financeiro Pessoal

Sistema para planejamento financeiro pessoal, inspirado no modelo de
orçamento **50/30/20** (necessidades / desejos / poupança e investimento).

Existem **duas versões** no repositório:

- **`app/` — versão desktop (Tkinter)**: um único usuário, roda 100% local,
  dados em `~/.controle_financeiro/financas.db`.
- **`webapp/` — versão web (Flask)**: visual mais moderno, com login e
  suporte a múltiplos usuários (cada um só vê seus próprios dados). Hoje ela
  roda localmente (você abre no navegador), mas o backend já está pronto para
  um dia ser publicado num servidor e acessado por outras pessoas, sem
  precisar reescrever o sistema. Dados em
  `~/.controle_financeiro/financas_web.db`.

Nas duas versões, nada é enviado para servidores externos — tudo fica no seu
computador.

## Funcionalidades

- **Saldo em Conta**: cadastro de contas e cartões, com saldo atualizado
  automaticamente sempre que uma receita é recebida ou uma despesa é paga.
- **Receitas**: planejamento de receitas fixas e variáveis para o ano todo,
  com opção de repetição mensal automática.
- **Despesas**: lançamento de despesas previstas para o ano, incluindo
  compras parceladas (gera as parcelas automaticamente mês a mês) e
  categorização por grupo de orçamento.
- **Investimentos**: registro de aportes e resgates, com gráfico de evolução
  do patrimônio investido ao longo do ano.
- **Metas / Orçamento (50/30/20)**: orçamento mensal por categoria, com
  barras de progresso e comparação do gasto real contra a divisão recomendada
  50% necessidades / 30% desejos / 20% poupança e investimento, com base na
  renda prevista do mês.
- **Dashboard**: visão geral com saldo total, receitas x despesas do mês,
  gráfico de gastos por categoria (pizza) e gráfico de receitas x despesas
  por mês ao longo do ano (barras).

## Como rodar

Requisitos: Python 3.10+ (para a versão desktop, com Tkinter disponível —
`python3-tk` no Linux).

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Versão desktop:**
```bash
python main.py
```
No Windows, dê duplo clique em `Abrir Controle Financeiro.bat`.

**Versão web:**
```bash
python run_web.py
```
Abre automaticamente `http://127.0.0.1:5000` no navegador. Na primeira vez,
crie uma conta (nome, e-mail, senha) — os dados dessa conta ficam isolados de
qualquer outra conta criada depois. No Windows, dê duplo clique em
`Abrir Controle Financeiro (Web).bat`. Para encerrar o servidor, feche a
janela do terminal/console associada a ele (o atalho `.bat` abre sem console
visível; use o Gerenciador de Tarefas e finalize o processo `pythonw.exe`
correspondente se precisar parar).

## Estrutura do projeto

```
main.py                     # ponto de entrada da versão desktop
run_web.py                   # ponto de entrada da versão web
app/                          # versão desktop (Tkinter)
  database.py                # acesso a dados (SQLite) e regras de negócio
  utils.py                    # formatação e constantes compartilhadas
  ui/
    main_window.py            # janela principal com as abas
    dashboard_tab.py          # visão geral e gráficos
    contas_tab.py             # contas e cartões
    receitas_tab.py           # receitas fixas/variáveis
    despesas_tab.py           # despesas previstas e parceladas
    investimentos_tab.py      # aportes/resgates e evolução do patrimônio
    metas_tab.py               # orçamento por categoria (50/30/20)
webapp/                        # versão web (Flask), multiusuário
  app.py                       # fábrica da aplicação Flask
  database.py                  # acesso a dados (SQLite), escopado por usuário
  auth.py                       # login, registro, logout
  financeiro.py                 # rotas: dashboard, contas, receitas, despesas, investimentos, metas
  templates/                    # páginas HTML (Jinja2)
  static/css/style.css          # visual (tema escuro, cards, sidebar)
  static/js/                    # Chart.js (vendorizado) + configuração dos gráficos
```

## Próximos passos sugeridos

- Exportação/backup dos dados (CSV ou cópia do arquivo `.db`).
- Suporte a múltiplos anos de planejamento na mesma tela (seletor de ano).
- Alertas quando uma categoria ultrapassa o orçamento definido.

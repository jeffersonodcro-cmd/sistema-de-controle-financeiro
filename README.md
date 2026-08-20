# Sistema de Controle Financeiro Pessoal

Aplicativo desktop (local) para planejamento financeiro pessoal, inspirado no
modelo de orçamento **50/30/20** (necessidades / desejos / poupança e
investimento).

Todos os dados ficam salvos localmente em um banco SQLite
(`~/.controle_financeiro/financas.db`) — nada é enviado para servidores externos.

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

Requisitos: Python 3.10+ com Tkinter disponível (`python3-tk` no Linux).

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Estrutura do projeto

```
main.py                     # ponto de entrada
app/
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
```

## Próximos passos sugeridos

- Exportação/backup dos dados (CSV ou cópia do arquivo `.db`).
- Suporte a múltiplos anos de planejamento na mesma tela (seletor de ano).
- Alertas quando uma categoria ultrapassa o orçamento definido.

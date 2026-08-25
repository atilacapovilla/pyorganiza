# apps/finance — Módulo de Finanças Pessoais

Aplicação Django para controle de finanças pessoais com suporte a contas, categorias hierárquicas, transações, transferências, cartões de crédito, planejamento mensal (com consulta realizado × planejado), balancete comparativo, extratos em HTML/PDF e importação/conciliação de arquivos OFX.

> **Nota:** esta documentação reflete o estado do código após a revisão de 2026-08-24
> (ver `docs/analise_finances.md`).

---

## Estrutura do App

```
apps/finance/
├── __init__.py
├── admin.py                     # 5 modelos registrados no admin
├── apps.py                      # FinanceConfig (BigAutoField)
├── signals.py                   # vazio (signals removidos)
├── fixtures/
│   └── category.json            # Categorias iniciais
├── forms/
│   ├── account_forms.py         # AccountForm (ModelForm)
│   ├── category_forms.py        # CategoryForm (hierarquia filtrada por usuário)
│   ├── import_forms.py          # ImportUploadForm (.ofx/.qfx + conta destino)
│   ├── planning_forms.py        # PlanningForm (mês/ano)
│   ├── transaction_forms.py     # TransactionForm (categorias agrupadas por tipo)
│   └── transfer_forms.py        # TransferForm (valida origem ≠ destino)
├── models/
│   ├── account.py               # Account + AccountQuerySet.with_current_balance()
│   ├── category.py              # Category (árvore, 50/30/20, transitória)
│   ├── imported_transaction.py  # ImportedTransaction (conciliação OFX)
│   ├── planning.py              # Planning (planejamento mensal por categoria)
│   └── transaction.py           # Transaction (receitas/despesas)
├── tests/
│   ├── base.py                  # BaseFinanceTestCase (fixtures compartilhadas)
│   ├── test_models.py           # defaults de data, current_balance
│   ├── test_transfer.py         # fluxo de transferência
│   ├── test_cards.py            # pagamento de fatura
│   ├── test_import.py           # upload OFX e reconciliação
│   ├── test_balancete.py        # balancete comparativo
│   └── test_views.py            # isolamento de usuário, extrato, dashboard
├── static/css/
│   ├── balancete_pdf.css
│   ├── extrato_pdf.css
│   └── planejamento_pdf.css
├── templates/
│   ├── account/ balancete/ cards/ category/ dashboard/
│   ├── extrato/ import/ planning/ transaction/ transfer/
├── urls/                        # um módulo por domínio (incluídos na raiz do projeto)
├── utils/
│   ├── finance_grafics.py       # dados dos gráficos (1 query/mês via TruncMonth)
│   ├── finance_metrics.py       # saldos, pendentes, método 50/30/20
│   ├── ofx_parser.py            # wrapper ofxparse
│   └── utils.py                 # cards_payment() — pagamento de fatura
└── views/                       # um módulo por domínio
```

---

## Modelos

### `Account`
| Campo | Tipo | Descrição |
|---|---|---|
| `name` | CharField(50) | Nome da conta |
| `type` | CharField(2) | CC, DN, CT ou IN |
| `logo` | ImageField | Redimensionado para 32×32 no `save()` |
| `opening_balance` | Decimal(10,2) | Saldo inicial |
| `user` | FK(User) CASCADE | Dono |
| `active` | Boolean | Conta ativa |

**Regra única de saldo** (`current_balance`, fonte de verdade no model):
- **CC/DN**: apenas transações **pagas** contam → `opening_balance + ΣC − ΣD`.
- **CT/IN**: todas as transações contam.
- Em listas, use `Account.objects.with_current_balance()` (1 query para todas as contas, disponível como `computed_balance`). A property `current_balance` reutiliza o valor anotado quando presente.

### `Category`
Hierárquica (`parent FK self`). Campos: `name(100)`, `color(7)`, `category_type ∈ {receita, despesa, investimento, transitoria}`, `essential(bool)`, `spending_type ∈ {fixa, variavel}` (default `variavel`), `metod_503020 ∈ {50,30,20,00}`.
Categorias `transitoria` são excluídas de métricas/gráficos/balancete/planejamento (usadas em transferências/pagamento de cartão).

**Ordenação padrão** (`utils/category_ordering.py`): primeiro por tipo na ordem das choices do model (Receitas → Despesas → Investimentos → Transitórias), depois alfabético (sem acento, case-insensitive) em cada nível. Aplicada nas árvores (categorias, balancete, planejamento) e nos dropdowns de transação, transferência e importação.

### `Transaction`
`transaction_date` e `due_date` com default `date.today()` (avaliado na criação), `is_paid`, `account FK PROTECT`, `category FK PROTECT`, `description(50)`, `transaction_value(10,2)`, `type ∈ {C, D}` (sempre positivo), `user FK`, `active`.

### `Planning`
`(user, month, year, category)` único; category FK CASCADE; `value(10,2)`.

### `ImportedTransaction`
Conciliação OFX: `bank_fit_id` (dedup), `status ∈ {pending, matched, ignored, imported}`, `matched_transaction FK SET_NULL`.

---

## Regras de Negócio

- **Transferência** (`transfer/`): cria par D (origem) + C (destino), ambos `is_paid=True`, dentro de `transaction.atomic`. Origem ≠ destino validada no form. Categoria deve ser filha (`parent__isnull=False`).
- **Pagamento de cartão** (`cards_payment`): marca como pagas as compras **não pagas** do vencimento informado e cria par "Pagamento Cartão de Crédito" (D na conta débito, C no cartão).
- **Balancete**: mês consultado vs mês anterior (janeiro volta para dezembro do ano anterior). Árvore agrega valores dos filhos nos pais.
- **Planejamento**: definido por categoria folha; consulta compara planejado × realizado com semáforo (% ≤80 verde / ≤100 amarelo / >100 vermelho para despesas; invertido para receitas/investimentos).
- **Isolamento multiusuário**: todos os querysets filtram por `request.user`; os forms recebem o usuário e nunca expõem objetos de terceiros.

---

## Rotas

| Rota | Nome | Descrição |
|---|---|---|
| `accounts/` `account/create\|update\|delete/` | CRUD de contas (CBV, paginação 10) |
| `categories/` `category/create\|update\|delete/` | CRUD de categorias (lista em árvore) |
| `transactions/` `transaction/create\|update\|delete/` | CRUD de transações (paginação 100, filtros período/conta) |
| `transfer/` | Transferência entre contas |
| `cards/` | Faturas e pagamento de cartões (tipo CT) |
| `dashboard/` | Métricas e gráficos (mês/ano selecionáveis) |
| `extrato/` + `extrato/pdf/` | Extrato com saldo corrido + PDF |
| `balancete/` + `balancete/pdf/` | Comparativo mensal por categoria + PDF |
| `planejamento/` | Definir planejamento do mês |
| `planejamento/consulta/` (+`pdf/`) | Realizado × planejado + PDF |
| `import/` | Upload OFX |
| `import/reconciliation/` | Conciliar (match/accept/ignore por `<pk>`) |

Todas as views exigem login.

---

## Utilitários

- **finance_metrics**: saldo do mês (com variação % vs anterior), últimos 6 meses, saldo por conta (via `with_current_balance()`), pendentes/projeção, método 50/30/20.
- **finance_grafics**: pizza essenciais × não essenciais (cores por categoria); receitas × despesas do ano (agregação única com `TruncMonth`).
- **ofx_parser.parse_ofx**: retorna `{bank_fit_id, transaction_date, description, transaction_value, type}` por transação.

---

## Testes

```bash
python manage.py test apps.finance.tests
```

34 testes cobrindo: defaults de data do model, semântica de `current_balance` (CC/DN × CT/IN, isolamento por usuário), transferências, pagamento de cartão (inclusive não recobrar fatura paga), upload/dedup OFX, reconciliação (match/accept/ignore, proteção entre usuários), balancete (totais, rollover janeiro→dezembro, agregação pai/filho), isolamento do CategoryForm, extrato e dashboard.

---

## Dependências Externas

- `Django` 5.x
- `Pillow` (redimensionamento de logo)
- `weasyprint` (PDFs)
- `sweetify` (toasts)
- `django-crispy-forms` + `crispy-bootstrap5`
- `ofxparse` (importação OFX/QFX)

---

## Observações Técnicas

- PDFs renderizados com WeasyPrint usando CSS em `static/css/` localizado via `django.contrib.staticfiles.finders`.
- `AccountQuerySet.with_current_balance()` usa agregação condicional em 1 query; o admin sobrescreve `get_queryset()` para usá-la.
- Migrações relevantes: `0008` removeu o campo `current_balance` (virou property), `0009` criou `ImportedTransaction`, `0010` corrigiu defaults de data de `Transaction`.

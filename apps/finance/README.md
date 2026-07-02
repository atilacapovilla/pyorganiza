# apps/finance — Módulo de Finanças Pessoais

Aplicação Django para controle de finanças pessoais com suporte a contas, categorias, transações, transferências, cartões de crédito, planejamento mensal, balancete comparativo e extratos.

---

## Estrutura do App

```
apps/finance/
├── __init__.py
├── admin.py
├── apps.py
├── fixtures/
│   └── category.json          # Dados iniciais de categorias
├── forms/
│   ├── __init__.py
│   ├── account_forms.py
│   ├── category_forms.py
│   ├── planning_forms.py
│   ├── transaction_forms.py
│   └── transfer_forms.py
├── migrations/
│   └── 0001_initial.py ... 0005_*.py
├── models/
│   ├── __init__.py
│   ├── account.py
│   ├── category.py
│   ├── planning.py
│   └── transaction.py
├── static/
│   └── css/
│       ├── balancete_pdf.css
│       └── extrato_pdf.css
├── templates/
│   ├── account/
│   ├── balancete/
│   ├── cards/
│   ├── category/
│   ├── dashboard/
│   ├── extrato/
│   ├── planning/
│   ├── transaction/
│   └── transfer/
├── urls/
│   ├── __init__.py
│   ├── account_urls.py
│   ├── balancete_urls.py
│   ├── cards_urls.py
│   ├── category_urls.py
│   ├── dashboard_urls.py
│   ├── extrato_urls.py
│   ├── planning_urls.py
│   ├── transaction_urls.py
│   └── transfer_urls.py
├── utils/
│   ├── finance_grafics.py      # Gráficos para dashboard
│   ├── finance_metrics.py      # Métricas financeiras
│   └── utils.py                # Utilitários (pagamento cartão)
├── views/
│   ├── __init__.py
│   ├── account_views.py
│   ├── balancete_views.py
│   ├── card_views.py
│   ├── category_views.py
│   ├── dashboard_views.py
│   ├── extrato_views.py
│   ├── planning_views.py
│   ├── transaction_views.py
│   └── transfer_views.py
└── README.md                   # Este arquivo
```

---

## Modelos (Models)

### `Account` (`models/account.py`)
Representa uma conta financeira do usuário.

| Campo | Tipo | Descrição |
|---|---|---|
| `name` | CharField(50) | Nome da conta |
| `type` | CharField(2) | Tipo: CC (Conta Corrente), DN (Dinheiro), CT (Cartão Crédito), IN (Investimentos) |
| `logo` | ImageField | Logotipo (redimensionado para 32x32 no `save()`) |
| `opening_balance` | DecimalField | Saldo inicial |
| `current_balance` | DecimalField | Saldo atual (atualizado via `get_finance_accounts_balance()`) |
| `user` | ForeignKey(User) | Usuário dono da conta |
| `active` | BooleanField | Conta ativa ou não |
| `created_at` / `updated_at` | DateTimeField | Timestamps |

### `Category` (`models/category.py`)
Categoriza receitas, despesas e investimentos.

| Campo | Tipo | Descrição |
|---|---|---|
| `user` | ForeignKey(User) | Usuário |
| `name` | CharField(100) | Nome |
| `color` | CharField(7) | Cor hexadecimal (ex: `#3498db`) |
| `category_type` | CharField(15) | `receita`, `despesa` ou `investimento` |
| `essential` | BooleanField | Se é despesa essencial |
| `metod_503020` | CharField(10) | Classificação 50/30/20: `50` (necessidades), `30` (desejos), `20` (poupança), `00` (N/A receitas) |
| `parent` | ForeignKey(self) | Categoria pai (para hierarquia) |

### `Transaction` (`models/transaction.py`)
Registro de receitas e despesas.

| Campo | Tipo | Descrição |
|---|---|---|
| `transaction_date` | DateField | Data da transação |
| `due_date` | DateField | Data de vencimento |
| `is_paid` | BooleanField | Se foi pago/recebido |
| `account` | ForeignKey(Account) | Conta vinculada |
| `category` | ForeignKey(Category) | Categoria |
| `description` | CharField(50) | Descrição |
| `transaction_value` | DecimalField | Valor |
| `type` | CharField(1) | `C` (Crédito/Receita) ou `D` (Débito/Despesa) |
| `user` | ForeignKey(User) | Usuário |
| `active` | BooleanField | Ativa ou não |

### `Planning` (`models/planning.py`)
Planejamento mensal por categoria.

| Campo | Tipo | Descrição |
|---|---|---|
| `user` | ForeignKey(User) | Usuário |
| `month` | IntegerField | Mês (1-12) |
| `year` | IntegerField | Ano |
| `category` | ForeignKey(Category) | Categoria (folha) |
| `value` | DecimalField | Valor planejado |

`unique_together = (user, month, year, category)`

---

## URLs e Views

| Rota | View | Descrição |
|---|---|---|
| `accounts/` | `AccountList` | Lista contas (com busca por nome) |
| `account/create/` | `AccountCreate` | Criar conta |
| `account/update/<pk>/` | `AccountUpdate` | Editar conta |
| `account/delete/<pk>/` | `AccountDelete` | Excluir conta |
| `categories/` | `CategoryList` | Lista categorias (árvore hierárquica) |
| `category/create/` | `CategoryCreate` | Criar categoria |
| `category/update/<pk>/` | `CategoryUpdate` | Editar categoria |
| `category/delete/<pk>/` | `CategoryDelete` | Excluir categoria |
| `transactions/` | `TransactionList` | Lista transações (filtro por data/conta, paginação 100) |
| `transaction/create/` | `TransactionCreate` | Criar transação |
| `transaction/update/<pk>/` | `TransactionUpdate` | Editar transação |
| `transaction/delete/<pk>/` | `TransactionDelete` | Excluir transação |
| `transfer/` | `Transfer` (function) | Transferência entre contas (cria 2 transações: débito na origem, crédito no destino) |
| `cards/` | `CardList` (function) | Gerenciamento de faturas de cartão de crédito |
| `dashboard/` | `dashboard` (function) | Dashboard com gráficos e métricas |
| `extrato/` | `extrato` (function) | Extrato detalhado (filtros por data, conta, status) |
| `extrato/pdf/` | `extrato_pdf` (function) | Extrato em PDF (via WeasyPrint) |
| `balancete/` | `balancete` (function) | Balancete mensal comparativo mês atual vs anterior |
| `balancete/pdf/` | `balancete_pdf` (function) | Balancete em PDF |
| `planejamento/` | `planning_definir` (function) | Definir planejamento mensal por categoria |

Todas as views exigem login (`LoginRequiredMixin` ou decorador `@login_required`).

---

## Funcionalidades Principais

### 1. **Contas** (CRUD)
Cadastro de contas correntes, dinheiro, cartão de crédito e investimentos. Redimensiona logo para 32x32 automaticamente.

### 2. **Categorias** (CRUD com hierarquia)
Categorias em árvore (pai/filho). Suporte ao método 50/30/20 e marcação de essencialidade. O form de categoria valida a hierarquia para evitar loops.

### 3. **Transações** (CRUD)
Registro de receitas (crédito) e despesas (débito) com data, vencimento, conta e categoria. Filtro por período e conta na listagem.

### 4. **Transferências**
Transferência entre contas do mesmo usuário. Cria automaticamente um débito na conta de origem e um crédito na conta de destino. Valida que origem e destino são diferentes.

### 5. **Cartão de Crédito**
Recupera transações não pagas de contas do tipo "CT" por data de vencimento. Gera o pagamento como uma despesa na conta débito e um crédito na conta cartão.

### 6. **Dashboard**
Métricas e gráficos por mês/ano:
- Saldo (receitas - despesas)
- Saldo por conta
- Pendências a pagar/receber
- Método 50/30/20 (desvio padrão)
- Gráfico de despesas essenciais vs não essenciais (pizza)
- Gráfico de receitas vs despesas por mês (barras)

### 7. **Extrato**
Extrato detalhado com filtros por período, conta e status (todos, pagos, abertos, vencidos). Exibe saldo corrente após cada transação. Geração de PDF.

### 8. **Balancete**
Comparativo de receitas, despesas e investimentos entre o mês atual e o anterior, organizado por árvore de categorias. Geração de PDF.

### 9. **Planejamento**
Define valores planejados para cada categoria folha (sem filhos) em um determinado mês/ano. Usa `update_or_create` para persistir.

---

## Utilitários

### `utils/utils.py`
- `cards_payment()`: Processa pagamento de fatura de cartão de crédito. Marca transações como pagas e cria transações de débito/crédito.

### `utils/finance_metrics.py`
- `get_finance_balance()`: Saldo do mês (receitas - despesas).
- `get_finance_accounts_balance()`: Saldo atual de cada conta (CC e DN calculados com transações pagas).
- `get_finance_pendents()`: Valores pendentes (não pagos) e saldo projetado.
- `get_finance_method()`: Análise do método 50/30/20 com desvios.

### `utils/finance_grafics.py`
- `get_finance_expense_month()`: Despesas do mês separadas por essenciais/não essenciais para gráfico de pizza.
- `get_finance_incomes_expense_year()`: Receitas e despesas por mês no ano para gráfico de barras.

---

## Observações Técnicas

- **Autenticação**: Todas as views filtram por `user=request.user`, garantindo isolamento de dados entre usuários.
- **PDF**: Geração de PDF usando `weasyprint` com folhas de estilo CSS dedicadas.
- **Notificações**: Uso da biblioteca `sweetify` para toasts de sucesso/erro.
- **Redimensionamento de Imagem**: No `save()` de `Account`, redimensiona o logo para 32x32 usando PIL.
- **Forms**: `TransactionForm` filtra contas e categorias por usuário e apenas categorias filhas (`parent__isnull=False`). `CategoryForm` constrói hierarquia com indentação e evita loops. `TransferForm` valida que origem ≠ destino.
- **Cascata de Deleção**: `Planning` usa `CASCADE`; `Transaction` usa `PROTECT` (não permite excluir conta/categoria com transações vinculadas).
- **Fixtures**: `category.json` contém dados iniciais para popular categorias.
- **Registro no Admin**: Todos os 4 modelos estão registrados no Django Admin.

---

## Dependências Externas (identificadas)

- `Django` (framework)
- `Pillow` / `PIL` (redimensionamento de imagem)
- `weasyprint` (geração de PDF)
- `sweetify` (toasts/notificações)
- `django-crispy-forms` (configurado com bootstrap5)

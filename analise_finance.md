# Análise do App `apps/finance`

## 1. Estrutura de Diretórios

```
apps/finance/
├── __init__.py
├── apps.py                              # FinanceConfig (BigAutoField, name="apps.finance")
├── admin.py                             # Registro de todos os 4 modelos no admin
├── README.md
├── fixtures/
│   └── category.json                    # 33 categorias iniciais (hierárquicas)
├── forms/
│   ├── __init__.py
│   ├── account_forms.py                 # AccountForm (ModelForm)
│   ├── category_forms.py                # CategoryForm (com escolha hierárquica)
│   ├── planning_forms.py                # PlanningForm (mês/ano)
│   ├── transaction_forms.py             # TransactionForm (querysets filtrados por user)
│   └── transfer_forms.py                # TransferForm (validação cruzada)
├── migrations/                          # 5 migrações (0001 a 0005)
├── models/
│   ├── __init__.py                      # Re-exporta os 4 modelos
│   ├── account.py                       # Account
│   ├── category.py                      # Category
│   ├── planning.py                      # Planning
│   └── transaction.py                   # Transaction
├── static/css/                          # 3 CSS para PDFs
├── templates/                           # Templates organizados por recurso
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
│   ├── finance_grafics.py               # Dados para gráficos do dashboard
│   ├── finance_metrics.py               # Métricas financeiras (saldo, pendentes, 50/30/20)
│   └── utils.py                         # Pagamento de cartão de crédito
└── views/
    ├── __init__.py
    ├── account_views.py                  # Account CRUD (class-based)
    ├── balancete_views.py                # Balancete + PDF (function views)
    ├── card_views.py                     # Cartão (function view)
    ├── category_views.py                 # Category CRUD (class-based)
    ├── dashboard_views.py                # Dashboard (function view)
    ├── extrato_views.py                  # Extrato + PDF (function views)
    ├── planning_views.py                 # Planejamento (function views)
    ├── transaction_views.py              # Transaction CRUD (class-based)
    └── transfer_views.py                 # Transferência (function view)
```

## 2. Modelos Principais

### Account
| Campo           | Tipo               | Detalhes                                                    |
| --------------- | ------------------ | ----------------------------------------------------------- |
| id              | BigAutoField       | PK                                                          |
| name            | CharField(50)      | Nome                                                        |
| type            | CharField(2)       | CC, DN, CT, IN                                              |
| logo            | ImageField         | upload_to="images/", default="sem_imagem.png"               |
| opening_balance | DecimalField(10,2) | Saldo inicial                                               |
| current_balance | DecimalField(10,2) | Saldo atual (atualizado por get_finance_accounts_balance()) |
| user            | FK(User)           | CASCADE                                                     |
| created_at      | DateTimeField      | auto_now_add                                                |
| updated_at      | DateTimeField      | auto_now                                                    |
| active          | BooleanField       | Default True                                                |

Observação: `save()` sobrescrito para redimensionar logo para 32x32 com Pillow.
Há um bug cosmético: `class Meta` duplicado (linhas 33-36 e 53-56).

### Category
| Campo         | Tipo                | Detalhes                                     |
| ------------- | ------------------- | -------------------------------------------- |
| id            | BigAutoField        | PK                                           |
| user          | FK(User)            | CASCADE, related_name="categories"           |
| name          | CharField(100)      | Nome                                         |
| color         | CharField(7)        | Hex, default "#3498db"                       |
| category_type | CharField(15)       | receita, despesa, investimento               |
| essential     | BooleanField        | Default False                                |
| metod_503020  | CharField(10, null) | 50, 30, 20, 00                               |
| parent        | FK('self')          | CASCADE, null/blank, related_name="children" |

### Transaction
| Campo             | Tipo                      | Detalhes                           |
| ----------------- | ------------------------- | ---------------------------------- |
| id                | BigAutoField              | PK                                 |
| transaction_date  | DateField                 | Default: datetime.now              |
| due_date          | DateField                 | Default: datetime.now              |
| is_paid           | BooleanField              | Default False                      |
| account           | FK(Account)               | PROTECT, related_name="accounts"   |
| category          | FK(Category)              | PROTECT, related_name="categories" |
| description       | CharField(50, null/blank) | Opcional                           |
| transaction_value | DecimalField(10,2)        | Valor                              |
| type              | CharField(1)              | C (Crédito), D (Débito)            |
| user              | FK(User)                  | CASCADE                            |
| created_at        | DateTimeField             | auto_now_add                       |
| updated_at        | DateTimeField             | auto_now                           |
| active            | BooleanField              | Default True                       |

### Planning
| Campo    | Tipo               | Detalhes  |
| -------- | ------------------ | --------- |
| id       | BigAutoField       | PK        |
| user     | FK(User)           | CASCADE   |
| month    | IntegerField       | 1-12      |
| year     | IntegerField       | Ano       |
| category | FK(Category)       | CASCADE   |
| value    | DecimalField(10,2) | Default 0 |

`unique_together = (user, month, year, category)`

## 3. Endpoints (URLs + Views)

| URL                          | View                             | Name                  |
| ---------------------------- | -------------------------------- | --------------------- |
| accounts/                    | AccountList (ListView)           | accounts              |
| account/create/              | AccountCreate (CreateView)       | account-create        |
| account/update/<int:pk>/     | AccountUpdate (UpdateView)       | account-update        |
| account/delete/<int:pk>/     | AccountDelete (DeleteView)       | account-delete        |
| categories/                  | CategoryList (ListView)          | categories            |
| category/create/             | CategoryCreate (CreateView)      | category-create       |
| category/update/<int:pk>/    | CategoryUpdate (UpdateView)      | category-update       |
| category/delete/<int:pk>/    | CategoryDelete (DeleteView)      | category-delete       |
| transactions/                | TransactionList (ListView)       | transactions          |
| transaction/create/          | TransactionCreate (CreateView)   | transaction-create    |
| transaction/update/<int:pk>/ | TransactionUpdate (UpdateView)   | transaction-update    |
| transaction/delete/<int:pk>/ | TransactionDelete (DeleteView)   | transaction-delete    |
| transfer/                    | Transfer (function)              | transfer              |
| cards/                       | CardList (function)              | cards                 |
| dashboard/                   | dashboard (function)             | dashboard             |
| extrato/                     | extrato (function)               | extrato               |
| extrato/pdf/                 | extrato_pdf (function)           | extrato-pdf           |
| balancete/                   | balancete (function)             | balancete             |
| balancete/pdf/               | balancete_pdf (function)         | balancete-pdf         |
| planejamento/                | planning_definir (function)      | planning-definir      |
| planejamento/consulta/       | planning_consulta (function)     | planning-consulta     |
| planejamento/consulta/pdf/   | planning_consulta_pdf (function) | planning-consulta-pdf |

Todas as views exigem login (LoginRequiredMixin ou @login_required).

## 4. Forms

- **AccountForm**: ModelForm para Account (name, type, opening_balance, logo, active)
- **CategoryForm**: ModelForm com `__init__` que adiciona color picker e árvore hierárquica para o campo `parent` (exclui self + descendentes)
- **TransactionForm**: ModelForm com querysets de account e category filtrados por user; category filtrada apenas para folhas (`parent__isnull=False`)
- **TransferForm**: Form padrão (não ModelForm). Campos: transaction_date, account_destination, account_origin, category, transaction_value, description. Valida que origem ≠ destino.
- **PlanningForm**: Form simples com campos month (choice) e year (choice, 2020-2035)

## 5. Signals

**Nenhum signal definido** no app.

## 6. Admin

- **CategoryAdmin**: list_display = (name, parent, color)
- **AccountAdmin**: list_display = (name, type, opening_balance, current_balance)
- **TransactionAdmin**: list_display = (transaction_date, due_date, account, description, transaction_value, is_paid, type)
- **PlanningAdmin**: list_display = (user, category, month, year, value); list_filter = (month, year, user)

## 7. Testes

**Nenhum teste** encontrado no app.

## 8. Integração com o Projeto

- Registrado em `INSTALLED_APPS` como `"apps.finance"` (core/settings)
- URLs incluídas via `include()` com prefixo vazio em core/urls.py
- Todas as consultas filtram por `user=request.user` (isolamento de dados)
- Dependências externas: Pillow, weasyprint, sweetify, django-crispy-forms

## 9. Lógica de Negócio Importante

### Account.save()
Redimensiona logo para 32x32 com PIL. Ignora silenciosamente erros.

### CategoryForm._build_hierarchical_choices()
Constrói lista de escolhas indentada para parent field. Exclui self + descendentes para evitar referência circular.

### Transfer (view)
Cria **duas** Transactions em uma transação atômica: 1 débito na origem + 1 crédito no destino (ambos is_paid=True).

### cards_payment() (utils/utils.py)
Processa pagamento de fatura de cartão de crédito:
1. Filtra débitos não pagos da conta de cartão
2. Soma total
3. Marca como pagos
4. Cria débito na conta corrente + crédito na conta cartão ("Pagamento Cartao de Credito")

### extrato / extrato_pdf
Filtra transações por período, conta e status. Calcula saldo corrente após cada transação. Gera PDF com weasyprint.

### balancete / balancete_pdf
Compara dois meses (selecionado vs anterior). Usa `_get_period_totals()` e `_build_tree()` para agregar por categoria.

### planning_definir
Salva/atualiza valores de planejamento para categorias folha via `update_or_create`.

### planning_consulta
Compara valores planejados vs reais. Usa `_percentage_status()` para classificar:
- Despesas: ≤80% = success, ≤100% = warning, >100% = danger
- Receitas/Investimentos: ≥100% = success, ≥80% = warning, <80% = danger

### get_finance_accounts_balance()
Contas CC/DN: apenas transações pagas. CT/IN: todas. Fórmula: opening_balance + receitas - despesas.

### get_finance_method()
Implementa regra 50/30/20: calcula renda total, classifica despesas por metod_503020, compara ideal vs real.

### get_finance_pendents()
Transações não pagas (separadas por tipo D/C). Calcula saldo projetado.

### Fixtures (category.json)
33 categorias pré-populadas em árvore (Receitas → 6 filhos, Despesas → 27 filhos com subcategorias).

## 10. Observações

- **Sem serializers REST** (DRF) — app é puramente server-side rendered.
- **Bug**: `class Meta` duplicado em `models/account.py`.
- **Bug potencial**: `Transaction.active` tem `verbose_name="Categoria Ativa"` (nome enganoso).
- Padrão consistente de isolamento de dados por usuário em todas as views/utils/forms.
- PDFs gerados com weasyprint usando CSS específico em static/css/.
- Notificações toast com sweetify.



Com base na sua analise no arquivo analise_finance.md. 

Tenho os seguintes fluxos para resolver, vou te passar os exemplos, analise e me indique as melhores 
alternativas :

1 - Despesa no valor de 2000, divido este valor com outra pessoa :

    Criamos dois campos ( Isso voce já fez ):

    Um que indica se a categoria altera o saldo das contas e um que indica se a categoria é um demonstrativo (Entra nos calculos de despesas e receitas mensais, anuais, graficos e outros indicativos para acompanhamento).
    Os lançamentos ficariam assim : 
    - Recebimento do pix de  1000   - altera saldo = True, demonstrativo = False
    - Lançamento da despesas 1000   - altera saldo = True, demonstrativo = True
    - Lançamento restante    1000   - altera saldo = True, demonstrativo = False

2 - Pagamento de cartão de crédito, as despesas já estão lançadas na conta do cartão.
    - Pagamento - altera saldo = True, demonstrativo = False. 
      Aqui tenho uma rotina especial, onde já faço a baixa dos lançamentos e altero o 
      saldo das contas de débito e a de crédito.

3 - Transferencia entre contas.
    - Tranferir - altera saldo = True, demonstrativo = False
      Aqui tambem tenho uma rotina especial os altero os saldos das contas de origem e destino.

#### Uma outra que estive pensando seria criar uma category type nova chamada transitorias ( o nome melhor voce sugere )
´´´python
category_type = models.CharField(
        max_length=15,
        choices=[
            ('receita', 'Receita'), 
            ('despesa', 'Despesa'),
            ('investimento', 'Investimentos'),
            ('transitoria', 'Transitoria')
        ],
        verbose_name="Tipo de Categoria"
    )
´´´
**analise e sugira a melhor, não faça nenhuma alteração ainda até eu dizer qual escolho**.
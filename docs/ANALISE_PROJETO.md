# Análise Completa do Projeto PyOrganiza (SGP)

**Data da análise:** 03/07/2026
**Versão analisada:** v1.0-Beta (commit `d8eda30`)
**Framework:** Django 5.2.5 / Python 3.10+

---

## 1. Visão Geral

O **PyOrganiza** é um sistema de gestão pessoal (SGP) que combina:

- **Anotações de cursos** (disciplinas, cursos e notas com suporte a Markdown)
- **Finanças pessoais** (contas, categorias, transações, transferências, planejamento, dashboards e relatórios PDF)
- **Módulo de tarefas** (planejado, não implementado)

**Stack tecnológica:**

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 5.2.5 |
| Frontend | Bootstrap 5, jQuery, DataTables, Bootstrap Icons |
| Notificações | SweetAlert2 (via `sweetify`) |
| PDF | WeasyPrint 66.0 |
| Banco (dev) | SQLite3 |
| Banco (prod) | MySQL ou PostgreSQL |
| Servidor (prod) | Gunicorn + Nginx (DigitalOcean) |
| Formulários | `django-crispy-forms` + `crispy-bootstrap5` |
| Markdown | `markdown` 3.8.2 |
| Imagens | `Pillow` 11.3.0 |

---

## 2. Estrutura do Projeto

```
pyorganiza/
+-- core/                      # Configuração do projeto Django
|   +-- settings.py            # Settings principais (BD, apps, middleware, etc.)
|   +-- urls.py                # Rotas raiz
|   +-- wsgi.py / asgi.py      # Entry points WSGI/ASGI
+-- apps/
|   +-- home/                  # Landing page e dashboard principal
|   |   +-- views.py           # home (pública) e principal (autenticada)
|   |   +-- course_metrics.py  # Métricas de curso (NUNCA utilizado)
|   |   +-- templates/home/    # home.html, principal.html, sidebar.html
|   +-- course/                # Módulo de cursos e anotações
|   |   +-- models/            # Subject, Course, Note
|   |   +-- views/             # CRUDs em CBV + PDF report
|   |   +-- forms/             # Formulários de Subject, Course, Note
|   |   +-- urls/              # Rotas separadas por entidade
|   |   +-- templates/         # course/, note/, subject/
|   +-- finance/               # Módulo financeiro (MAIOR)
|       +-- models/            # Account, Category, Transaction, Planning
|       +-- views/             # 24 rotas (CRUDs + dashboard + relatórios)
|       +-- forms/             # Formulários financeiros
|       +-- urls/              # Rotas separadas por funcionalidade
|       +-- utils/             # Gráficos, métricas, helpers
|       +-- fixtures/          # 27 categorias padrão (seed data)
|       +-- templates/         # account/, category/, transaction/, etc.
+-- users/                     # Autenticação e perfis
|   +-- models.py              # Profile (OneToOne com User)
|   +-- views.py               # Login, Register, Profile
|   +-- forms.py               # RegisterForm, UserUpdateForm, ProfileUpdateForm
|   +-- signals.py             # Auto-cria/salva Profile ao salvar User
|   +-- templates/users/       # register, profile, password_reset
+-- templates/                 # Templates globais
|   +-- base.html              # Layout principal (sidebar + navbar + content)
|   +-- base_home.html         # Layout simplificado (auth pages)
|   +-- partials/              # sidebar.html, navbar.html, footer.html (ATIVOS)
|   +-- components/            # sidebar.html, navbar.html (ANTIGOS, duplicados)
+-- static/                    # CSS (Bootstrap, custom, login), JS (Bootstrap, jQuery, DataTables)
+-- media/                     # Uploads: avatares, logos, imagens
+-- staticfiles/               # collectstatic output
```

### Status das Correções (03/07/2026)

| # | Problema | Status | Arquivos alterados |
|---|---------|--------|-------------------|
| 3.1 | `.env` exposto? | ✅ Já estava gitignorado | — |
| 3.2 | `SubjectDelete` sem filtro | ✅ Corrigido | `apps/course/views/subject_views.py` |
| 3.3 | `NoteDelete` redirect 404 | ✅ Corrigido | `apps/course/views/note_views.py` |
| 3.4 | Transferência sem atomic | ✅ Corrigido | `apps/finance/views/transfer_views.py` |
| 3.5 | `TransactionList` model errado | ✅ Corrigido | `apps/finance/views/transaction_views.py` |
| 4.2 | `finance_metrics` com `save()` | ✅ Corrigido | `apps/finance/utils/finance_metrics.py` |
| 4.3 | `Account.save()` quebra sem logo | ✅ Corrigido | `apps/finance/models/account.py` |
| 4.5 | Ano hardcoded em planning | ✅ Corrigido | `apps/finance/views/planning_views.py` |
| 5.1 | Typos (suceso, perfial, transction) | ✅ Corrigido | 4 arquivos de views |
| 5.2 | Imports não utilizados | ✅ Corrigido | `apps/home/views.py` |
| 5.3 | `pyproject.toml` sintaxe | ✅ Corrigido | `pyproject.toml` |
| 5.6 | `User` direto + imports circulares | ✅ Corrigido | 8 arquivos de models + users/ |
| — | `Profile.save()` quebra sem avatar | ✅ Corrigido | `users/models.py` |

### Estatísticas do Projeto

| Métrica | Quantidade |
|---------|-----------|
| Django apps | 4 (home, course, finance, users) |
| Modelos | 8 (Subject, Course, Note, Account, Category, Transaction, Planning, Profile) |
| Rotas URL | ~40 |
| Views (CBV) | ~18 |
| Views (FBV) | ~10 |
| Formulários | 11 |
| Templates HTML | ~50 |
| Migrations | 13 (course: 7, finance: 5, users: 1) |
| Relatórios PDF | 4 (nota, extrato, balancete, planejamento) |
| Testes escritos | **0** (arquivo vazio em users/) |
| Middleware customizado | 0 |
| Template tags customizadas | 0 |
| Context processors customizados | 0 |
| Management commands | 0 |
| Docker | Não |

---

## 3. Erros Críticos

### 3.1 Segurança: Permissões do `.env`

**Arquivo:** `.env` (raiz do projeto)
**Gravidade:** 🟡 BAIXA (monitoramento)

O arquivo `.env` **nunca foi commitado** no Git — o `.gitignore` o ignora corretamente desde o início. No entanto, recomenda-se restringir as permissões do arquivo local para `600` (apenas o dono lê) em ambientes compartilhados:

```bash
chmod 600 .env
```

---

### 3.2 Bug: `SubjectDelete` não filtra por usuário

**Arquivo:** `apps/course/views/subject_views.py:65-67`
**Gravidade:** 🔴 CRÍTICA

O método `get_queryset` que filtra por usuário está definido **fora da classe** `SubjectDelete`, no escopo do módulo. A classe `SubjectDelete` usa o queryset padrão (todos os registros), permitindo que qualquer usuário autenticado delete disciplinas de outros usuários.

```python
# CÓDIGO ATUAL (BUG):
class SubjectDelete(DeleteView):
    model = Subject
    success_url = reverse_lazy("subjects")
    # NÃO TEM get_queryset AQUI!

def get_queryset(self):  # <-- FORA da classe!
    return Subject.objects.filter(user=self.request.user)
```

**Correção:** Mover `get_queryset` para dentro da classe `SubjectDelete`.

---

### 3.3 Bug: `NoteDelete` redireciona para URL inválida após deletar

**Arquivo:** `apps/course/views/note_views.py:93`
**Gravidade:** 🔴 ALTA

O método `get_success_url()` retorna a URL de `note-detail` usando o `pk` da nota que está sendo deletada. Após a deleção, essa URL resulta em **404**.

```python
def get_success_url(self):
    return reverse("note-detail", kwargs={"pk": self.object.pk})  # 404 garantido!
```

**Correção:** Redirecionar para `note-list` ou para o curso associado à nota.

---

### 3.4 Bug: Transferência sem transação atômica

**Arquivo:** `apps/finance/views/transfer_views.py`
**Gravidade:** 🔴 ALTA

A view de transferência cria dois objetos `Transaction` (débito e crédito) sem usar `transaction.atomic()`. Se o segundo `save()` falhar, o primeiro persiste no banco, gerando inconsistência financeira.

**Correção:**
```python
from django.db import transaction

@transaction.atomic
def Transfer(request):
    ...
```

---

### 3.5 Bug: `TransactionList` usa modelo incorreto

**Arquivo:** `apps/finance/views/transaction_views.py:16`
**Gravidade:** 🟠 MODERADA

```python
class TransactionList(LoginRequiredMixin, ListView):
    model = TransactionForm  # BUG: deveria ser Transaction
```

Funciona porque `get_queryset` é sobrescrito, mas é semanticamente incorreto e pode causar problemas com metadados da view (nome do model, verbosity, etc.).

---

## 4. Erros Moderados

### 4.1 Dashboard principal com dados placeholder

**Arquivos:** `apps/home/views.py` + `apps/home/templates/home/principal.html`

A view `principal` passa apenas `{'pagina': 'Home'}` como contexto, mas o template referência variáveis que **nunca são populadas**:

- `cursos_recentes`
- `transacoes_recentes`
- `atividades_recentes`
- `tarefas_hoje_lista`
- `progresso`
- `saldo_mes`

O arquivo `course_metrics.py` existe com funções prontas (`get_course_metrics()`) mas **nunca é chamado** (apesar de importado em `views.py`).

---

### 4.2 Efeito colateral em função de leitura

**Arquivo:** `apps/finance/utils/finance_metrics.py:66,92`

A função `get_finance_accounts_balance()` chama `account.save()` dentro de uma operação que deveria ser apenas de leitura. Cada carregamento do dashboard modifica o banco (atualiza `current_balance`).

**Impacto:** Efeito colateral inesperado, dificulta debugging e pode causar race conditions.

---

### 4.3 `Account.save()` quebra sem logo

**Arquivo:** `apps/finance/models/account.py`

O método `save()` tenta abrir e redimensionar a imagem do logo **incondicionalmente**. Se o campo `logo` estiver vazio ou o arquivo não existir em disco, levanta exceção.

---

### 4.4 Landing page pública usa template de usuário logado

**Arquivo:** `apps/home/templates/home/home.html`

`home.html` estende `base.html`, que inclui sidebar e navbar que esperam um `user` autenticado com `user.profile`. Para visitantes não autenticados, pode causar erros de template (`AttributeError` ao acessar `user.profile`).

---

### 4.5 Ano hardcoded no planejamento

**Arquivo:** `apps/finance/views/planning_views.py:94`

```python
range(2020, 2036)  # Hardcoded
```

Enquanto `balancete_views.py` e `dashboard_views.py` usam intervalos dinâmicos baseados em `today.year`.

---

### 4.6 Categorias duplicadas por usuário

**Arquivo:** `apps/finance/fixtures/category.json`

O fixture de categorias cria registros associados a um `user` específico (provavelmente `pk=1`). Novos usuários não têm categorias padrão. A fixture foi pensada para seed inicial, mas não é executada automaticamente para novos registros.

---

## 5. Erros Menores

### 5.1 Typos em mensagens de sucesso

| Arquivo | Linha | Erro | Correto |
|---------|-------|------|---------|
| `apps/course/views/subject_views.py` | 35, 46, 61 | `"suceso"` | `"sucesso"` |
| `apps/course/views/course_views.py` | 56 | `"suceso"` | `"sucesso"` |
| `apps/course/views/note_views.py` | 69, 86 | `"suceso"` | `"sucesso"` |
| `apps/finance/views/transfer_views.py` | 25, 38 | `transction` | `transaction` |
| `users/views.py` | 68 | `"perfial"` | `"perfil"` |

### 5.2 Imports não utilizados

| Arquivo | Import | Observação |
|---------|--------|------------|
| `apps/home/views.py:1` | `json` | Nunca usado |
| `apps/home/views.py:7` | `from . import course_metrics` | Importado, função nunca chamada |
| `apps/course/views/subject_views.py:1` | `sweetify` | Nunca usado |
| `apps/course/views/note_views.py:1` | `sweetify` | Nunca usado |

### 5.3 Erro de sintaxe no `pyproject.toml`

```toml
target-version = ['py310]   # Falta aspas de fechamento
```

**Correto:**
```toml
target-version = ['py310']
```

### 5.4 Inconsistência no sistema de notificações

O projeto usa **dois sistemas simultaneamente**:
- `sweetify.toast()` (SweetAlert2)
- `messages.success()` / `messages.error()` (Django Messages)

Views diferentes usam sistemas diferentes. Não há um padrão definido.

### 5.5 Templates duplicados

Existem duas versões dos mesmos componentes:
- `templates/components/_sidebar.html` + `_navbar.html` (antigos, com seções extensas comentadas)
- `templates/partials/sidebar.html` + `navbar.html` (ativos, usados pelo `base.html`)

### 5.6 Ausência de `AUTH_USER_MODEL` customizado

O projeto importa `User` diretamente em múltiplos arquivos:

```python
from django.contrib.auth.models import User
```

Em vez de usar `settings.AUTH_USER_MODEL` ou `get_user_model()`. Se no futuro for necessário migrar para um Custom User Model, a refatoração será trabalhosa.

**Arquivos afetados:** `apps/course/models/`, `apps/finance/models/`, `apps/home/views.py`, `users/signals.py`

### 5.7 Import circular potencial em `course/models`

**Arquivo:** `apps/course/models/__init__.py`

O `__init__.py` importa de todos os submodulos, e cada submodulo importa `*` de volta do `__init__.py`. Funciona atualmente mas é frágil e pode causar problemas com ordenação de migrations.

---

## 6. Análise Detalhada dos Módulos

### 6.1 Módulo `apps.course` (Notas de Aula)

**Modelos:**

| Modelo | Campos | Relacionamentos |
|--------|--------|----------------|
| `Subject` | title, created_at, updated_at, active | FK → User |
| `Course` | title, created_at, updated_at, active | FK → Subject (PROTECT), FK → User |
| `Note` | title, order, content, created_at, updated_at, active | FK → Course (CASCADE), FK → User |

**Destaques positivos:**
- Uso consistente de Class-Based Views
- `LoginRequiredMixin` em todas as views protegidas
- Filtragem por `user=request.user` (exceto SubjectDelete)
- Método `formatted_content()` que renderiza Markdown com code blocks e tables
- Relatório PDF funcional via WeasyPrint

**Pontos de melhoria:**
- `Subject` e `Course` sem `unique_together` (pode ter duplicatas)
- `Note.order` não tem validação de unicidade por course
- `course_metrics.py` tem funções prontas mas não integradas

### 6.2 Módulo `apps.finance` (Finanças Pessoais)

**Modelos:**

| Modelo | Campos | Relacionamentos |
|--------|--------|----------------|
| `Account` | name, type (CC/DN/CT/IN), logo, opening_balance, current_balance, active | FK → User |
| `Category` | name, color, type (receita/despesa/investimento), essential, metod_503020 | FK → User, FK → self (hierárquica) |
| `Transaction` | transaction_date, due_date, is_paid, description, value, type (C/D), active | FK → Account (PROTECT), FK → Category (PROTECT), FK → User |
| `Planning` | month, year, value | FK → User, FK → Category |

**Destaques positivos:**
- Arquitetura bem modularizada (models, views, forms, urls separados por entidade)
- Relatórios PDF com CSS dedicado (extrato, balancete, planejamento)
- Dashboard com gráficos de despesas mensais e comparação anual
- Método 50/30/20 implementado
- Categorias hierárquicas (self-referential FK)
- Categorias seedáveis via fixture (27 categorias)
- Pagamento de cartão de crédito automatizado (cria débito/crédito pareados)

**Pontos de melhoria:**
- `TransactionList` com `model = TransactionForm` (já reportado)
- Transferência sem `transaction.atomic()` (já reportado)
- `Account.save()` sem tratamento de logo ausente (já reportado)
- `Planning` com ano hardcoded
- Categorias não associadas automaticamente a novos usuários
- Sem soft-delete consistente (alguns modelos têm `active`, outros não)

### 6.3 Módulo `users` (Autenticação)

**Funcionalidades:**
- Login/Logout customizados
- Registro com auto-login
- Perfil com avatar (auto-redimensionado para 300×300)
- Password reset completo
- Profile criado automaticamente via signal `post_save`

**Destaques positivos:**
- Signals para auto-criação de Profile
- Avatar com redimensionamento automático
- Redirecionamento de usuários já logados na tela de login

**Pontos de melhoria:**
- Testes vazios (`tests.py` só tem `from django.test import TestCase`)
- Typo: `"perfial"` ao invés de `"perfil"`
- Sem rate limiting nas views de login/registro
- `ProfileUpdateForm` recria o avatar mesmo se não houve alteração

### 6.4 Módulo `apps.home` (Landing + Dashboard)

**Funcionalidades:**
- `home()` → Landing page pública
- `principal()` → Dashboard autenticado (placeholder)

**Pontos de melhoria:**
- Dashboard não implementado (só placeholder)
- `course_metrics` importado mas nunca usado
- `principal.html` referencia variáveis que não existem no contexto
- `home.html` (público) estende `base.html` que espera usuário logado

---

## 7. Recomendações

### 7.1 Segurança (Prioridade Máxima)

- [ ] **Remover `.env` do Git** e gerar nova SECRET_KEY
- [ ] **Corrigir `SubjectDelete`** para filtrar por usuário
- [ ] Adicionar `SECURE_SSL_REDIRECT = True` em produção
- [ ] Adicionar `SESSION_COOKIE_SECURE = True` e `CSRF_COOKIE_SECURE = True` em produção
- [ ] Configurar `EMAIL_BACKEND` para password reset (atualmente comentado no settings.py)
- [ ] Adicionar rate limiting nas views de login e registro
- [ ] Verificar se `DEBUG=False` remove o debug-toolbar em produção
- [ ] Adicionar `SECURE_HSTS_SECONDS` em produção

### 7.2 Testes (Prioridade Alta)

- [ ] **Criar testes para modelos**: validações, métodos customizados, constraints
- [ ] **Criar testes de views**: acesso, permissões, CRUD, redirects
- [ ] **Testar isolamento de dados**: usuário A não pode acessar dados do usuário B (especialmente SubjectDelete)
- [ ] Testar geração de PDFs
- [ ] Testar transferência com `transaction.atomic()`
- [ ] Testar pagamento de cartão de crédito
- [ ] Testar dashboard com dados reais
- [ ] **Meta sugerida**: cobertura mínima de 70%

### 7.3 Correções de Bugs (Prioridade Alta)

- [ ] `NoteDelete.get_success_url()` → redirecionar para `note-list` ou course da nota
- [ ] Envolver transferência em `transaction.atomic()`
- [ ] `TransactionList.model = Transaction` (em vez de `TransactionForm`)
- [ ] Refatorar `get_finance_accounts_balance()` para não salvar durante leitura
- [ ] `Account.save()` → tratar ausência de logo
- [ ] `home.html` → usar `base_home.html` ou condicional para user anônimo

### 7.4 Qualidade de Código (Prioridade Média)

- [ ] Corrigir todos os typos (seção 5.1)
- [ ] Remover imports não utilizados (seção 5.2)
- [ ] Corrigir `pyproject.toml`
- [ ] Padronizar notificações: escolher `sweetify` ou `messages` e usar consistentemente
- [ ] Remover templates duplicados em `templates/components/`
- [ ] Usar `get_user_model()` em vez de `User` direto
- [ ] Adicionar `unique_together` em Subject (title + user) e Course (title + subject)
- [ ] Usar intervalo dinâmico em `planning_views.py`
- [ ] Adicionar `class Meta: ordering` nos models que não têm
- [ ] Configurar Black e Flake8 como hooks de pre-commit

### 7.5 Arquitetura (Prioridade Média)

- [ ] **Implementar o dashboard principal (`principal`)** com dados reais de cursos e finanças
- [ ] Adicionar custom template tags para lógica repetitiva (e.g., ícones de categoria, status de transação)
- [ ] Considerar context processors para dados de sidebar (saldo, notificações pendentes)
- [ ] Adicionar paginação consistente em todas as listagens
- [ ] Implementar soft-delete de forma consistente em todos os modelos
- [ ] Separar `apps/finance` em submódulos se continuar crescendo
- [ ] Adicionar `__str__` e `Meta.verbose_name` em todos os models (já existem na maioria)

### 7.6 Deploy e Infraestrutura

- [ ] Adicionar `Dockerfile` e `docker-compose.yml` para desenvolvimento
- [ ] Configurar CI/CD (GitHub Actions): lint → test → build
- [ ] Adicionar health check endpoint (`/health/`)
- [ ] Backup automático do banco de dados
- [ ] Monitoramento de erros (Sentry)
- [ ] Configurar logging em produção (arquivo + formato estruturado)
- [ ] Adicionar `SECURE_PROXY_SSL_HEADER` para funcionar atrás do Nginx

### 7.7 UX e Frontend

- [ ] Tratar carregamento do dashboard com dados reais ou mensagem "nenhum dado encontrado"
- [ ] Adicionar feedback visual para ações assíncronas
- [ ] Validar formulários com mensagens claras em português
- [ ] Responsividade: testar sidebar em dispositivos móveis
- [ ] Modo escuro (já existe suporte via CSS, verificar se está funcional em todas as páginas)
- [ ] DataTables: verificar conflito com Bootstrap 5 (já existe config personalizada)

---

## 8. Diagrama de Relacionamentos

```
┌─────────────────────────────────────────────────────────────┐
│                         User (Django)                        │
└────┬──────────┬──────────────┬──────────────────┬───────────┘
     │          │              │                  │
     │ 1:1      │ 1:N          │ 1:N              │ 1:N
     ▼          ▼              ▼                  ▼
┌─────────┐ ┌──────────┐ ┌────────────┐ ┌──────────────────┐
│ Profile  │ │ Subject  │ │ Account     │ │ Category          │
│ avatar   │ │ title    │ │ name, type  │ │ name, color, type │
│         │ │ active   │ │ balance    │ │ parent (self FK)  │
└─────────┘ └────┬─────┘ └──────┬─────┘ └────────┬─────────┘
                 │ 1:N          │ 1:N             │ 1:N
                 ▼              ▼                  ▼
           ┌──────────┐ ┌──────────────┐ ┌──────────────────┐
           │ Course    │ │ Transaction   │ │ Planning          │
           │ title     │ │ date, value,  │ │ month, year      │
           │ active    │ │ is_paid, type │ │ value             │
           └─────┬────┘ └──────────────┘ └──────────────────┘
                 │ 1:N
                 ▼
           ┌──────────┐
           │ Note      │
           │ title     │
           │ content   │
           │ order     │
           │ active    │
           └──────────┘
```

---

## 9. Checklist de Dependências

| Pacote | Versão | Finalidade |
|--------|--------|-----------|
| Django | 5.2.5 | Framework |
| django-crispy-forms | 2.4 | Renderização de forms |
| crispy-bootstrap5 | — | Tema Bootstrap 5 |
| sweetify | 2.3.1 | Notificações |
| django-decouple | 2.1 | Variáveis de ambiente |
| weasyprint | 66.0 | PDF |
| Markdown | 3.8.2 | Renderização de notas |
| Pillow | 11.3.0 | Imagens |
| gunicorn | 25.0.3 | Servidor WSGI |
| psycopg2-binary | 2.9.11 | Driver PostgreSQL |
| python-decouple | — | (dependência do django-decouple) |

**Dev:**
| Pacote | Versão | Finalidade |
|--------|--------|-----------|
| django-debug-toolbar | 6.0.0 | Debug |
| ipython | — | Shell interativo |
| black | — | Formatador |
| flake8 | — | Linter |

---

## 10. Roadmap Sugerido

### Fase 1 — Segurança e Estabilização (1-2 dias)
1. Remover `.env` do Git + nova SECRET_KEY
2. Corrigir `SubjectDelete`
3. Corrigir `NoteDelete.get_success_url()`
4. Adicionar `transaction.atomic()` na transferência
5. Corrigir `TransactionList.model`

### Fase 2 — Testes (3-5 dias)
1. Testes de modelos
2. Testes de views (CRUD, permissões)
3. Testes de isolamento de dados
4. Testes de PDF e transferência

### Fase 3 — Dashboard e Funcionalidades (5-7 dias)
1. Implementar dashboard principal com dados reais
2. Popular `principal.html` com KPIs
3. Integrar `course_metrics.py` com a view
4. Implementar módulo de tarefas (pendente)

### Fase 4 — Qualidade e Refatoração (3-5 dias)
1. Corrigir todos os typos e imports
2. Padronizar notificações
3. Remover templates duplicados
4. Refatorar imports de `User` para `get_user_model()`
5. Adicionar `unique_together` e constraints

### Fase 5 — Infraestrutura (2-3 dias)
1. Docker + docker-compose
2. CI/CD
3. Backup automático
4. Sentry

---

## 11. Resumo Executivo

O **PyOrganiza** é um projeto Django maduro e bem estruturado. O código é organizado, os módulos são bem separados, e o módulo financeiro é particularmente robusto com dashboards, relatórios PDF e múltiplas funcionalidades.

**Pontos fortes:**
- Arquitetura modular com separação clara de responsabilidades
- Uso consistente de CBVs com `LoginRequiredMixin`
- Relatórios PDF funcionais com WeasyPrint
- Suporte a Markdown nas notas
- Categorias hierárquicas no módulo financeiro
- Modo escuro via CSS
- Boa estrutura de templates com partials reutilizáveis

**Problemas que exigem ação imediata:**
1. 🔴 **Acesso indevido**: `SubjectDelete` permite deletar dados de outros usuários
2. 🔴 **404 garantido**: `NoteDelete` redireciona para URL inválida
3. 🔴 **Inconsistência de dados**: transferência sem `transaction.atomic()`
4. 🟠 **Modelo incorreto**: `TransactionList` usa `TransactionForm` como `model`

**Métricas finais:**

| Indicador | Status |
|-----------|--------|
| Erros críticos de segurança | 0 (`.env` já está gitignorado) |
| Bugs de lógica (alta gravidade) | 3 |
| Bugs de lógica (média gravidade) | 1 |
| Erros moderados | 6 |
| Erros menores (typos, imports) | 10+ |
| Cobertura de testes | **0%** |
| Cobertura de testes recomendada | **70%+** |
| Docker / containerização | ❌ |
| CI/CD | ❌ |
| Documentação de API | ❌ (sem REST API) |

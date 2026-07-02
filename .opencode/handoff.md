# Handoff - PyOrganiza (01/07/2026)

## Estrutura do Projeto
- Django project: `core/`
- App financeiro: `apps/finance/` (models, views, urls, templates, forms separados por módulo)
- Sidebar em `templates/partials/sidebar.html`

## O que foi feito hoje

### 1. PDF do Balancete
- `apps/finance/views/balancete_views.py` — view `balancete_pdf` (linha 131)
- `apps/finance/templates/balancete/balancete_pdf.html` — template PDF
- `apps/finance/templates/balancete/_balancete_pdf_row.html` — partial recursivo
- `apps/finance/static/css/balancete_pdf.css` — estilo A4 paisagem
- `apps/finance/urls/balancete_urls.py` — rota `balancete/pdf/` (name: `balancete-pdf`)
- `apps/finance/templates/balancete/balancete_list.html` — botão "Imprimir" adicionado

### 2. Planejamento (tela de definição)
- `apps/finance/models/planning.py` — model `Planning` (user, month, year, category, value)
- `apps/finance/views/planning_views.py` — view `planning_definir` com upsert
- `apps/finance/templates/planning/planning_definir.html` — template principal
- `apps/finance/templates/planning/_planning_row.html` — partial recursivo (árvore)
- `apps/finance/urls/planning_urls.py` — rota `planejamento/` (name: `planning-definir`)
- `apps/finance/forms/planning_forms.py` — form (não usado no momento)
- `core/urls.py` — incluído `planning_urls`
- `templates/partials/sidebar.html` — links "Definir" e "Visualizar" atualizados
- Migration `0005` aplicada

### 3. Correções
- `core/settings.py` — `THOUSAND_SEPARATOR` corrigido de `(".",)` para `"."`
- `planning_views.py` — parsing robusto com `re.sub(r"\D", "")`

## Pendências / Ideias
- **Visualizar planejamento**: sidebar tem link "Visualizar" apontando para `planning-definir` — criar view separada para exibir sem edição
- **Comparativo planejado vs realizado**: usar dados do `Planning` vs `Transaction` agregado por categoria/mês
- **PDF do planejamento**: seguir padrão do extrato/balancete

## Como continuar
Basta dizer "continue de onde parou" ou citar um dos tópicos acima.

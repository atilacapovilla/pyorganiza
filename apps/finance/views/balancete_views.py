import re
from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from apps.finance.models.category import Category
from apps.finance.models.transaction import Transaction
from apps.finance.utils.category_ordering import sort_categories

MONTH_NAMES = ["Janeiro", "Fevereiro", "Março", "Abril",
               "Maio", "Junho", "Julho", "Agosto",
               "Setembro", "Outubro", "Novembro", "Dezembro"]


def _parse_month_year(request):
    today = date.today()
    month_str = re.sub(r"\D", "", request.GET.get("month", str(today.month)))
    year_str = re.sub(r"\D", "", request.GET.get("year", str(today.year)))
    month = int(month_str) if month_str else today.month
    year = int(year_str) if year_str else today.year
    if not 1 <= month <= 12:
        month = today.month
    return month, year, today


def _previous_period(month, year):
    if month == 1:
        return 12, year - 1
    return month - 1, year


def _get_period_totals(user, month, year):
    qs = (
        Transaction.objects.filter(
            user=user,
            transaction_date__month=month,
            transaction_date__year=year,
            is_paid=True,
        )
        .exclude(category__category_type="transitoria")
        .values("category")
        .annotate(total=Sum("transaction_value"))
    )
    return {row["category"]: float(row["total"] or 0) for row in qs}


def _group_by_parent(category_list):
    children_map = {}
    for cat in category_list:
        children_map.setdefault(cat.parent_id, []).append(cat)
    return children_map


def _build_tree(children_map, parent_id, curr_totals, prev_totals):
    nodes = []
    for cat in children_map.get(parent_id, []):
        curr = curr_totals.get(cat.id, 0)
        prev = prev_totals.get(cat.id, 0)
        children = _build_tree(children_map, cat.id, curr_totals, prev_totals)
        for child in children:
            curr += child["curr_total"]
            prev += child["prev_total"]
        nodes.append(
            {
                "category": cat,
                "curr_total": curr,
                "prev_total": prev,
                "children": children,
            }
        )
    return nodes


def _get_balancete_context(user, month, year):
    prev_month, prev_year = _previous_period(month, year)

    category_list = sort_categories(
        list(
            Category.objects.filter(user=user).exclude(
                category_type="transitoria"
            )
        )
    )
    categories_by_id = {cat.id: cat for cat in category_list}

    curr_totals = _get_period_totals(user, month, year)
    prev_totals = _get_period_totals(user, prev_month, prev_year)

    children_map = _group_by_parent(category_list)
    tree = _build_tree(children_map, None, curr_totals, prev_totals)

    totals_by_type = {
        "curr": {"receita": 0, "despesa": 0, "investimento": 0},
        "prev": {"receita": 0, "despesa": 0, "investimento": 0},
    }
    for period, totals in (("curr", curr_totals), ("prev", prev_totals)):
        for cat_id, val in totals.items():
            cat = categories_by_id.get(cat_id)
            if cat is not None and cat.category_type in totals_by_type[period]:
                totals_by_type[period][cat.category_type] += val

    months_list = [(i + 1, name) for i, name in enumerate(MONTH_NAMES)]

    return {
        "tree": tree,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": MONTH_NAMES[month - 1],
        "prev_month": prev_month,
        "prev_year": prev_year,
        "prev_month_name": MONTH_NAMES[prev_month - 1],
        "months": months_list,
        "total_receitas_curr": totals_by_type["curr"]["receita"],
        "total_despesas_curr": totals_by_type["curr"]["despesa"],
        "total_investimentos_curr": totals_by_type["curr"]["investimento"],
        "total_receitas_prev": totals_by_type["prev"]["receita"],
        "total_despesas_prev": totals_by_type["prev"]["despesa"],
        "total_investimentos_prev": totals_by_type["prev"]["investimento"],
        "saldo_curr": totals_by_type["curr"]["receita"] - totals_by_type["curr"]["despesa"],
        "saldo_prev": totals_by_type["prev"]["receita"] - totals_by_type["prev"]["despesa"],
    }


@login_required
def balancete(request):
    month, year, today = _parse_month_year(request)
    context = _get_balancete_context(request.user, month, year)
    context["year_range"] = range(today.year - 5, today.year + 2)
    return render(request, "balancete/balancete_list.html", context)


@login_required
def balancete_pdf(request):
    month, year, today = _parse_month_year(request)
    context = _get_balancete_context(request.user, month, year)
    context["data_emissao"] = today

    html_string = render_to_string("balancete/balancete_pdf.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="balancete_{month:02d}{year}_comparativo.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/balancete_pdf.css"))]
    )
    return response

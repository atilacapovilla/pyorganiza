import re
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS

from apps.finance.models.category import Category
from apps.finance.models.transaction import Transaction


def _get_period_totals(request, month, year):
    qs = (
        Transaction.objects.filter(
            user=request.user,
            transaction_date__month=month,
            transaction_date__year=year,
        )
        .values("category")
        .annotate(total=Sum("transaction_value"))
    )
    return {row["category"]: float(row["total"] or 0) for row in qs}


def _build_tree(categories, parent, curr_totals, prev_totals):
    nodes = []
    for cat in categories.filter(parent=parent):
        curr = curr_totals.get(cat.id, 0)
        prev = prev_totals.get(cat.id, 0)
        children = _build_tree(categories, cat, curr_totals, prev_totals)
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


@login_required
def balancete(request):
    today = date.today()
    month_str = re.sub(r"\D", "", request.GET.get("month", str(today.month)))
    year_str = re.sub(r"\D", "", request.GET.get("year", str(today.year)))
    month = int(month_str) if month_str else today.month
    year = int(year_str) if year_str else today.year

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    categories = Category.objects.filter(user=request.user)
    curr_totals = _get_period_totals(request, month, year)
    prev_totals = _get_period_totals(request, prev_month, prev_year)

    tree = _build_tree(categories, None, curr_totals, prev_totals)

    total_receitas_curr = 0
    total_despesas_curr = 0
    total_investimentos_curr = 0
    total_receitas_prev = 0
    total_despesas_prev = 0
    total_investimentos_prev = 0

    for cat_id, val in curr_totals.items():
        try:
            cat = categories.get(pk=cat_id)
            if cat.category_type == "receita":
                total_receitas_curr += val
            elif cat.category_type == "despesa":
                total_despesas_curr += val
            elif cat.category_type == "investimento":
                total_investimentos_curr += val
        except Category.DoesNotExist:
            pass

    for cat_id, val in prev_totals.items():
        try:
            cat = categories.get(pk=cat_id)
            if cat.category_type == "receita":
                total_receitas_prev += val
            elif cat.category_type == "despesa":
                total_despesas_prev += val
            elif cat.category_type == "investimento":
                total_investimentos_prev += val
        except Category.DoesNotExist:
            pass

    month_names = ["Janeiro", "Fevereiro", "Março", "Abril",
                   "Maio", "Junho", "Julho", "Agosto",
                   "Setembro", "Outubro", "Novembro", "Dezembro"]

    months_list = [(i + 1, name) for i, name in enumerate(month_names)]
    year_range = range(today.year - 5, today.year + 2)

    context = {
        "tree": tree,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": month_names[month - 1],
        "prev_month": prev_month,
        "prev_year": prev_year,
        "prev_month_name": month_names[prev_month - 1],
        "months": months_list,
        "year_range": year_range,
        "total_receitas_curr": total_receitas_curr,
        "total_despesas_curr": total_despesas_curr,
        "total_investimentos_curr": total_investimentos_curr,
        "total_receitas_prev": total_receitas_prev,
        "total_despesas_prev": total_despesas_prev,
        "total_investimentos_prev": total_investimentos_prev,
        "saldo_curr": total_receitas_curr - total_despesas_curr,
        "saldo_prev": total_receitas_prev - total_despesas_prev,
    }

    return render(request, "balancete/balancete_list.html", context)


@login_required
def balancete_pdf(request):
    today = date.today()
    month_str = re.sub(r"\D", "", request.GET.get("month", str(today.month)))
    year_str = re.sub(r"\D", "", request.GET.get("year", str(today.year)))
    month = int(month_str) if month_str else today.month
    year = int(year_str) if year_str else today.year

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    categories = Category.objects.filter(user=request.user)
    curr_totals = _get_period_totals(request, month, year)
    prev_totals = _get_period_totals(request, prev_month, prev_year)

    tree = _build_tree(categories, None, curr_totals, prev_totals)

    total_receitas_curr = 0
    total_despesas_curr = 0
    total_investimentos_curr = 0
    total_receitas_prev = 0
    total_despesas_prev = 0
    total_investimentos_prev = 0

    for cat_id, val in curr_totals.items():
        try:
            cat = categories.get(pk=cat_id)
            if cat.category_type == "receita":
                total_receitas_curr += val
            elif cat.category_type == "despesa":
                total_despesas_curr += val
            elif cat.category_type == "investimento":
                total_investimentos_curr += val
        except Category.DoesNotExist:
            pass

    for cat_id, val in prev_totals.items():
        try:
            cat = categories.get(pk=cat_id)
            if cat.category_type == "receita":
                total_receitas_prev += val
            elif cat.category_type == "despesa":
                total_despesas_prev += val
            elif cat.category_type == "investimento":
                total_investimentos_prev += val
        except Category.DoesNotExist:
            pass

    month_names = ["Janeiro", "Fevereiro", "Março", "Abril",
                   "Maio", "Junho", "Julho", "Agosto",
                   "Setembro", "Outubro", "Novembro", "Dezembro"]

    context = {
        "tree": tree,
        "selected_month_name": month_names[month - 1],
        "prev_month_name": month_names[prev_month - 1],
        "total_receitas_curr": total_receitas_curr,
        "total_despesas_curr": total_despesas_curr,
        "total_investimentos_curr": total_investimentos_curr,
        "total_receitas_prev": total_receitas_prev,
        "total_despesas_prev": total_despesas_prev,
        "total_investimentos_prev": total_investimentos_prev,
        "saldo_curr": total_receitas_curr - total_despesas_curr,
        "saldo_prev": total_receitas_prev - total_despesas_prev,
        "data_emissao": today,
    }

    html_string = render_to_string("balancete/balancete_pdf.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="balancete_{month:02d}{year}_comparativo.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/balancete_pdf.css"))]
    )
    return response

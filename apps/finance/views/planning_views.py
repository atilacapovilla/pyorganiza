import re
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from apps.finance.models.category import Category
from apps.finance.models.planning import Planning
from apps.finance.models.transaction import Transaction


def _get_leaf_categories(user):
    all_cats = Category.objects.filter(user=user)
    leaf_ids = []
    for cat in all_cats:
        has_children = all_cats.filter(parent=cat).exists()
        if not has_children:
            leaf_ids.append(cat.id)
    return Category.objects.filter(pk__in=leaf_ids)


def _build_tree(categories, parent, existing):
    nodes = []
    for cat in categories.filter(parent=parent):
        children = _build_tree(categories, cat, existing)
        is_leaf = len(children) == 0
        nodes.append({
            "category": cat,
            "is_leaf": is_leaf,
            "value": existing.get(cat.id, 0) if is_leaf else None,
            "children": children,
        })
    return nodes


@login_required
def planning_definir(request):
    today = date.today()

    if request.method == "POST":
        month = int(re.sub(r"\D", "", request.POST.get("month", str(today.month))) or today.month)
        year = int(re.sub(r"\D", "", request.POST.get("year", str(today.year))) or today.year)

        leaf_categories = _get_leaf_categories(request.user)

        for cat in leaf_categories:
            field_name = f"value_{cat.id}"
            raw_value = request.POST.get(field_name, "").strip()
            if raw_value == "":
                value = 0
            else:
                try:
                    value = float(raw_value.replace(",", "."))
                except ValueError:
                    value = 0

            Planning.objects.update_or_create(
                user=request.user,
                month=month,
                year=year,
                category=cat,
                defaults={"value": value},
            )

        messages.success(request, "Planejamento salvo com sucesso!")
        return redirect(f"{request.path}?month={month}&year={year}")

    month = int(re.sub(r"\D", "", request.GET.get("month", str(today.month))) or today.month)
    year = int(re.sub(r"\D", "", request.GET.get("year", str(today.year))) or today.year)

    categories = Category.objects.filter(user=request.user)

    existing = {}
    for p in Planning.objects.filter(
        user=request.user, month=month, year=year
    ):
        existing[p.category_id] = p.value

    tree = _build_tree(categories, None, existing)

    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro",
    ]

    months_list = [(i + 1, name) for i, name in enumerate(month_names)]
    today = date.today()
    year_range = range(today.year - 5, today.year + 6)

    context = {
        "tree": tree,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": month_names[month - 1],
        "months": months_list,
        "year_range": year_range,
    }

    return render(request, "planning/planning_definir.html", context)


def _percentage_status(percentage, category_type):
    if percentage is None:
        return "secondary"
    if category_type == "despesa":
        if percentage <= 80:
            return "success"
        elif percentage <= 100:
            return "warning"
        else:
            return "danger"
    else:
        if percentage >= 100:
            return "success"
        elif percentage >= 80:
            return "warning"
        else:
            return "danger"


def _build_consulta_tree(categories, parent, planned, actual):
    nodes = []
    for cat in categories.filter(parent=parent):
        children = _build_consulta_tree(categories, cat, planned, actual)
        is_leaf = len(children) == 0
        planned_val = float(planned.get(cat.id, 0))
        actual_val = float(actual.get(cat.id, 0))
        for child in children:
            planned_val += child["planned"]
            actual_val += child["actual"]
        pct = (actual_val / planned_val * 100) if planned_val > 0 else None
        nodes.append({
            "category": cat,
            "is_leaf": is_leaf,
            "planned": planned_val,
            "actual": actual_val,
            "percentage": pct,
            "status": _percentage_status(pct, cat.category_type),
            "diff": planned_val - actual_val,
            "children": children,
        })
    return nodes


def _sum_totals_by_type(nodes):
    totals = {
        "receita": {"planned": 0, "actual": 0},
        "despesa": {"planned": 0, "actual": 0},
        "investimento": {"planned": 0, "actual": 0},
    }
    def walk(items):
        for item in items:
            if item["is_leaf"]:
                t = item["category"].category_type
                totals[t]["planned"] += item["planned"]
                totals[t]["actual"] += item["actual"]
            walk(item["children"])
    walk(nodes)
    return totals


@login_required
def planning_consulta(request):
    today = date.today()
    month = int(re.sub(r"\D", "", request.GET.get("month", str(today.month))) or today.month)
    year = int(re.sub(r"\D", "", request.GET.get("year", str(today.year))) or today.year)

    categories = Category.objects.filter(user=request.user)

    planned = {}
    for p in Planning.objects.filter(user=request.user, month=month, year=year):
        planned[p.category_id] = float(p.value)

    actual_qs = (
        Transaction.objects
        .filter(user=request.user, transaction_date__year=year, transaction_date__month=month)
        .values("category_id")
        .annotate(total=Sum("transaction_value"))
    )
    actual = {row["category_id"]: float(row["total"]) for row in actual_qs}

    tree = _build_consulta_tree(categories, None, planned, actual)
    totals = _sum_totals_by_type(tree)

    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro",
    ]
    months_list = [(i + 1, name) for i, name in enumerate(month_names)]
    year_range = range(today.year - 5, today.year + 6)

    for tname in totals:
        p = totals[tname]["planned"]
        a = totals[tname]["actual"]
        totals[tname]["percentage"] = (a / p * 100) if p > 0 else None
        totals[tname]["diff"] = p - a
        totals[tname]["diff_abs"] = abs(totals[tname]["diff"])

    totals["receita"]["status"] = _percentage_status(totals["receita"]["percentage"], "receita")
    totals["despesa"]["status"] = _percentage_status(totals["despesa"]["percentage"], "despesa")
    totals["investimento"]["status"] = _percentage_status(totals["investimento"]["percentage"], "investimento")

    context = {
        "tree": tree,
        "totals": totals,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": month_names[month - 1],
        "months": months_list,
        "year_range": year_range,
    }
    return render(request, "planning/planning_consulta.html", context)


@login_required
def planning_consulta_pdf(request):
    today = date.today()
    month = int(re.sub(r"\D", "", request.GET.get("month", str(today.month))) or today.month)
    year = int(re.sub(r"\D", "", request.GET.get("year", str(today.year))) or today.year)

    categories = Category.objects.filter(user=request.user)

    planned = {}
    for p in Planning.objects.filter(user=request.user, month=month, year=year):
        planned[p.category_id] = float(p.value)

    actual_qs = (
        Transaction.objects
        .filter(user=request.user, transaction_date__year=year, transaction_date__month=month)
        .values("category_id")
        .annotate(total=Sum("transaction_value"))
    )
    actual = {row["category_id"]: float(row["total"]) for row in actual_qs}

    tree = _build_consulta_tree(categories, None, planned, actual)
    totals = _sum_totals_by_type(tree)

    for tname in totals:
        p = totals[tname]["planned"]
        a = totals[tname]["actual"]
        totals[tname]["percentage"] = (a / p * 100) if p > 0 else None
        totals[tname]["diff"] = p - a

    totals["receita"]["status"] = _percentage_status(totals["receita"]["percentage"], "receita")
    totals["despesa"]["status"] = _percentage_status(totals["despesa"]["percentage"], "despesa")
    totals["investimento"]["status"] = _percentage_status(totals["investimento"]["percentage"], "investimento")

    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro",
    ]

    context = {
        "tree": tree,
        "totals": totals,
        "selected_month_name": month_names[month - 1],
        "data_emissao": today,
        "usuario": request.user.get_full_name() or request.user.username,
    }

    html_string = render_to_string("planning/planning_consulta_pdf.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="planejamento_{month:02d}{year}.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/planejamento_pdf.css"))]
    )
    return response

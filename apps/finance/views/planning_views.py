import re
from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from apps.finance.models.category import Category
from apps.finance.models.planning import Planning
from apps.finance.models.transaction import Transaction
from apps.finance.utils.category_ordering import sort_categories

MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro",
]

MONTHS_LIST = [(i + 1, name) for i, name in enumerate(MONTH_NAMES)]


def _parse_month_year(request, source):
    today = date.today()
    raw_month = re.sub(r"\D", "", source.get("month", str(today.month)))
    raw_year = re.sub(r"\D", "", source.get("year", str(today.year)))
    month = int(raw_month) if raw_month else today.month
    year = int(raw_year) if raw_year else today.year
    if not 1 <= month <= 12:
        month = today.month
    return month, year


def _get_leaf_categories(user):
    return (
        Category.objects.filter(user=user)
        .exclude(category_type="transitoria")
        .annotate(
            children_count=Count(
                "children",
                filter=Q(children__user=user)
                & ~Q(children__category_type="transitoria"),
            )
        )
        .filter(children_count=0)
    )


def _group_by_parent(category_list):
    children_map = {}
    for cat in category_list:
        children_map.setdefault(cat.parent_id, []).append(cat)
    return children_map


def _build_tree(children_map, parent_id, existing):
    nodes = []
    for cat in children_map.get(parent_id, []):
        children = _build_tree(children_map, cat.id, existing)
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
        month, year = _parse_month_year(request, request.POST)

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

    month, year = _parse_month_year(request, request.GET)

    category_list = sort_categories(
        list(
            Category.objects.filter(user=request.user).exclude(
                category_type="transitoria"
            )
        )
    )

    existing = {
        p.category_id: p.value
        for p in Planning.objects.filter(user=request.user, month=month, year=year)
    }

    tree = _build_tree(_group_by_parent(category_list), None, existing)

    context = {
        "tree": tree,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": MONTH_NAMES[month - 1],
        "months": MONTHS_LIST,
        "year_range": range(today.year - 5, today.year + 6),
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


def _build_consulta_tree(children_map, parent_id, planned, actual):
    nodes = []
    for cat in children_map.get(parent_id, []):
        children = _build_consulta_tree(children_map, cat.id, planned, actual)
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
        "transitoria": {"planned": 0, "actual": 0},
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


def _finalize_totals(totals):
    for tname in totals:
        p = totals[tname]["planned"]
        a = totals[tname]["actual"]
        totals[tname]["percentage"] = (a / p * 100) if p > 0 else None
        totals[tname]["diff"] = p - a
        totals[tname]["diff_abs"] = abs(totals[tname]["diff"])

    for tname in ("receita", "despesa", "investimento"):
        totals[tname]["status"] = _percentage_status(totals[tname]["percentage"], tname)


def _get_consulta_context(user, month, year):
    category_list = sort_categories(
        list(
            Category.objects.filter(user=user).exclude(category_type="transitoria")
        )
    )

    planned = {
        p.category_id: float(p.value)
        for p in Planning.objects.filter(user=user, month=month, year=year)
    }

    actual_qs = (
        Transaction.objects
        .filter(user=user, transaction_date__year=year, transaction_date__month=month)
        .values("category_id")
        .annotate(total=Sum("transaction_value"))
    )
    actual = {row["category_id"]: float(row["total"]) for row in actual_qs}

    tree = _build_consulta_tree(_group_by_parent(category_list), None, planned, actual)
    totals = _sum_totals_by_type(tree)
    _finalize_totals(totals)

    return {
        "tree": tree,
        "totals": totals,
        "selected_month": month,
        "selected_year": year,
        "selected_month_name": MONTH_NAMES[month - 1],
        "months": MONTHS_LIST,
    }


@login_required
def planning_consulta(request):
    today = date.today()
    month, year = _parse_month_year(request, request.GET)

    context = _get_consulta_context(request.user, month, year)
    context["year_range"] = range(today.year - 5, today.year + 6)

    return render(request, "planning/planning_consulta.html", context)


@login_required
def planning_consulta_pdf(request):
    today = date.today()
    month, year = _parse_month_year(request, request.GET)

    context = _get_consulta_context(request.user, month, year)
    context["data_emissao"] = today
    context["usuario"] = request.user.get_full_name() or request.user.username

    html_string = render_to_string("planning/planning_consulta_pdf.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="planejamento_{month:02d}{year}.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/planejamento_pdf.css"))]
    )
    return response

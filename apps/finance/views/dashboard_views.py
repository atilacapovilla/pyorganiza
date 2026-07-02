import json
import re
from datetime import date

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.finance.utils import finance_metrics
from apps.finance.utils import finance_grafics


@login_required
def dashboard(request):
    today = date.today()

    month_str = re.sub(r"\D", "", request.GET.get("month", str(today.month)))
    year_str = re.sub(r"\D", "", request.GET.get("year", str(today.year)))
    month = int(month_str) if month_str else today.month
    year = int(year_str) if year_str else today.year

    labels_essential, data_essential, colors_essential, labels_non_essential, data_non_essential, colors_non_essential = (
        finance_grafics.get_finance_expense_month(request, month, year)
    )

    labels_year, data_expenses_year, data_incomes_year = (
        finance_grafics.get_finance_incomes_expense_year(request, year)
    )

    finance_balance = finance_metrics.get_finance_balance(
        request, month, year
    )

    finance_accounts_balance = finance_metrics.get_finance_accounts_balance(request)

    total_balance = finance_accounts_balance["balance_total"]

    finance_pendents = finance_metrics.get_finance_pendents(total_balance, request)

    finance_method = finance_metrics.get_finance_method(request, month, year)

    months_list = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro"),
    ]

    year_range = range(today.year - 5, today.year + 2)

    context = {
        "finance_balance": finance_balance,
        "labels_essential": json.dumps(labels_essential),
        "data_essential": json.dumps(data_essential),
        "colors_essential": json.dumps(colors_essential),
        "labels_non_essential": json.dumps(labels_non_essential),
        "data_non_essential": json.dumps(data_non_essential),
        "colors_non_essential": json.dumps(colors_non_essential),
        "labels_year": json.dumps(labels_year),
        "data_expenses_year": json.dumps(data_expenses_year),
        "data_incomes_year": json.dumps(data_incomes_year),
        "finance_accounts_balance": finance_accounts_balance,
        "finance_pendents": finance_pendents,
        "finance_method": finance_method,
        "selected_month": month,
        "selected_year": year,
        "months": months_list,
        "year_range": year_range,
    }

    return render(request, "dashboard/dashboard.html", context)

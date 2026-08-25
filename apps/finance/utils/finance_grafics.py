from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth

from apps.finance.models.transaction import Transaction


def get_finance_expense_month(request, month, year):
    labels_essential = []
    data_essential = []
    colors_essential = []
    labels_non_essential = []
    data_non_essential = []
    colors_non_essential = []

    queryset = (
        Transaction.objects.values("category__name", "category__color")
        .annotate(total_expenses=Sum("transaction_value"))
        .filter(
            user=request.user,
            category__category_type="despesa",
            transaction_date__year=year,
            transaction_date__month=month,
        )
        .order_by("-total_expenses")
    )

    expenses_essential = queryset.filter(category__essential=True)
    for entry in expenses_essential:
        labels_essential.append(entry["category__name"])
        data_essential.append(int(entry["total_expenses"]))
        colors_essential.append(entry["category__color"])

    expenses_non_essential = queryset.filter(category__essential=False)
    for entry in expenses_non_essential:
        labels_non_essential.append(entry["category__name"])
        data_non_essential.append(int(entry["total_expenses"]))
        colors_non_essential.append(entry["category__color"])

    return (
        labels_essential,
        data_essential,
        colors_essential,
        labels_non_essential,
        data_non_essential,
        colors_non_essential,
    )


def get_finance_incomes_expense_year(request, year):
    labels_year = [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ]
    data_expenses_year = [0] * 12
    data_incomes_year = [0] * 12

    monthly_totals = (
        Transaction.objects.filter(user=request.user, transaction_date__year=year)
        .exclude(category__category_type="transitoria")
        .annotate(month=TruncMonth("transaction_date"))
        .values("month")
        .annotate(
            expenses=Sum(
                "transaction_value",
                filter=Q(category__category_type="despesa"),
            ),
            incomes=Sum(
                "transaction_value",
                filter=Q(category__category_type="receita"),
            ),
        )
    )

    for row in monthly_totals:
        month_index = row["month"].month - 1
        data_expenses_year[month_index] = int(row["expenses"] or 0)
        data_incomes_year[month_index] = int(row["incomes"] or 0)

    return labels_year, data_expenses_year, data_incomes_year


def get_finance_expense_spending_type(request, month, year):
    labels_fixed = []
    data_fixed = []
    colors_fixed = []
    labels_variable = []
    data_variable = []
    colors_variable = []

    queryset = (
        Transaction.objects.values(
            "category__name", "category__color", "category__spending_type"
        )
        .annotate(total_expenses=Sum("transaction_value"))
        .filter(
            user=request.user,
            category__category_type="despesa",
            transaction_date__year=year,
            transaction_date__month=month,
        )
        .order_by("-total_expenses")
    )

    for entry in queryset:
        name = entry["category__name"]
        color = entry["category__color"]
        total = int(entry["total_expenses"])
        if entry["category__spending_type"] == "fixa":
            labels_fixed.append(name)
            data_fixed.append(total)
            colors_fixed.append(color)
        else:
            labels_variable.append(name)
            data_variable.append(total)
            colors_variable.append(color)

    return (
        labels_fixed,
        data_fixed,
        colors_fixed,
        labels_variable,
        data_variable,
        colors_variable,
    )

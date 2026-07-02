from django.db.models import Sum

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
            type="D",
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

    return labels_essential, data_essential, colors_essential, labels_non_essential, data_non_essential, colors_non_essential


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
    data_expenses_year = []
    data_incomes_year = []
    dates = [i for i in range(1, 13, 1)]

    transactions = Transaction.objects.filter(
        user=request.user, transaction_date__year=year
    )

    for date in dates:
        expense = (
            transactions.filter(transaction_date__month=date, type="D").aggregate(
                Sum("transaction_value")
            )["transaction_value__sum"]
            or 0
        )

        data_expenses_year.append(int(expense))

        income = (
            transactions.filter(transaction_date__month=date, type="C").aggregate(
                Sum("transaction_value")
            )["transaction_value__sum"]
            or 0
        )

        data_incomes_year.append(int(income))

    return labels_year, data_expenses_year, data_incomes_year

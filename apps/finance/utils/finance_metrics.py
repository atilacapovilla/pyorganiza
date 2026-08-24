from datetime import date
from django.db.models import Q, Sum

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


def _get_month_totals(request, month, year):
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__year=year,
        transaction_date__month=month,
    ).exclude(category__category_type="transitoria")

    expenses = (
        transactions.filter(type="D").aggregate(Sum("transaction_value"))[
            "transaction_value__sum"
        ]
        or 0
    )

    incomes = (
        transactions.filter(type="C").aggregate(Sum("transaction_value"))[
            "transaction_value__sum"
        ]
        or 0
    )

    return expenses, incomes


def _previous_month(month, year):
    if month == 1:
        return 12, year - 1
    return month - 1, year


def get_finance_balance(request, month, year):
    expenses, incomes = _get_month_totals(request, month, year)
    balance = incomes - expenses

    prev_month, prev_year = _previous_month(month, year)
    prev_expenses, prev_incomes = _get_month_totals(request, prev_month, prev_year)
    prev_balance = prev_incomes - prev_expenses

    def _pct_change(current, previous):
        if not previous:
            return 0.0
        return ((current - previous) / abs(previous)) * 100

    incomes_change = _pct_change(incomes, prev_incomes)
    expenses_change = _pct_change(expenses, prev_expenses)
    balance_change = _pct_change(balance, prev_balance)

    return dict(
        expenses=expenses,
        incomes=incomes,
        balance=balance,
        prev_expenses=prev_expenses,
        prev_incomes=prev_incomes,
        prev_balance=prev_balance,
        incomes_change=incomes_change,
        expenses_change=expenses_change,
        balance_change=balance_change,
        incomes_change_abs=abs(incomes_change),
        expenses_change_abs=abs(expenses_change),
        balance_change_abs=abs(balance_change),
    )


def get_finance_last_months(request, month, year):
    months_data = []
    m, y = month, year
    for _ in range(6):
        expenses, incomes = _get_month_totals(request, m, y)
        balance = incomes - expenses
        months_data.append(dict(
            month=m,
            year=y,
            incomes=float(incomes),
            expenses=float(expenses),
            balance=float(balance),
        ))
        m, y = _previous_month(m, y)

    months_data = list(reversed(months_data))

    def _pct_change(current, previous):
        if not previous:
            return 0.0
        return ((current - previous) / abs(previous)) * 100

    for index, item in enumerate(months_data):
        if index == 0:
            item["incomes_change"] = 0.0
            item["expenses_change"] = 0.0
            item["balance_change"] = 0.0
        else:
            prev = months_data[index - 1]
            item["incomes_change"] = _pct_change(item["incomes"], prev["incomes"])
            item["expenses_change"] = _pct_change(item["expenses"], prev["expenses"])
            item["balance_change"] = _pct_change(item["balance"], prev["balance"])

    return months_data


def get_finance_accounts_balance(request):
    today = date.today()
    balance_total = 0

    accounts = Account.objects.filter(
        Q(user=request.user),
        Q(type="CC") | Q(type="DN"),
    )

    for account in accounts:
        transactions = Transaction.objects.filter(
            account=account, is_paid=True)
        expenses = (
            transactions.filter(type="D").aggregate(Sum("transaction_value"))[
                "transaction_value__sum"
            ]
            or 0
        )
        incomes = (
            transactions.filter(type="C").aggregate(Sum("transaction_value"))[
                "transaction_value__sum"
            ]
            or 0
        )
        balance = account.opening_balance + incomes - expenses
        account.__dict__["current_balance"] = balance
        balance_total += balance

    accounts_other = (
        Account.objects.filter(user=request.user)
        .exclude(type="CC")
        .exclude(type="DN")
        .order_by("type", "name")
    )

    for account in accounts_other:
        transactions = Transaction.objects.filter(account=account)
        expenses = (
            transactions.filter(type="D").aggregate(Sum("transaction_value"))[
                "transaction_value__sum"
            ]
            or 0
        )
        incomes = (
            transactions.filter(type="C").aggregate(Sum("transaction_value"))[
                "transaction_value__sum"
            ]
            or 0
        )
        balance = account.opening_balance + incomes - expenses
        account.__dict__["current_balance"] = balance

    finance_accounts_balance = dict(
        accounts=accounts,
        accounts_other=accounts_other,
        balance_total=balance_total,
    )
    return finance_accounts_balance


def get_finance_pendents(total_balance, request):
    today = date.today()

    expenses_pendents = Transaction.objects.filter(
        user=request.user,
        type="D",
        is_paid=False,
    ).order_by("due_date")

    incomes_pendents = Transaction.objects.filter(
        user=request.user,
        type="C",
        is_paid=False,
    ).order_by("due_date")

    expenses_due = (
        expenses_pendents.aggregate(Sum("transaction_value"))[
            "transaction_value__sum"]
        or 0
    )

    incomes_due = (
        incomes_pendents.aggregate(Sum("transaction_value"))[
            "transaction_value__sum"]
        or 0
    )

    balance_pendent = total_balance + incomes_due - expenses_due

    finance_pendents = dict(
        expenses_pendents=expenses_pendents,
        incomes_pendents=incomes_pendents,
        expenses_due=expenses_due,
        incomes_due=incomes_due,
        balance_pendent=balance_pendent,
    )
    return finance_pendents


def get_finance_method(request, month=None, year=None):
    today = date.today()
    month = month or today.month
    year = year or today.year

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__year=year,
        transaction_date__month=month,
    ).exclude(category__category_type="transitoria")

    total_incomes = float(
        transactions.filter(type="C")
        .aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    expenses_essentials = float(
        transactions.filter(
            type="D", category__metod_503020="50"
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    expenses_superfluous = float(
        transactions.filter(
            type="D", category__metod_503020="30"
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    reserves = float(
        transactions.filter(type="D", category__metod_503020="20").aggregate(
            Sum("transaction_value")
        )["transaction_value__sum"]
        or 0
    )

    essentials_provided = (total_incomes * 50) / 100
    superfluous_provided = (total_incomes * 30) / 100
    reserves_provided = (total_incomes * 20) / 100

    essential_deviation = essentials_provided - expenses_essentials
    superfluous_deviation = superfluous_provided - expenses_superfluous
    reserves_deviation = reserves - reserves_provided

    return dict(
        total_incomes=total_incomes,
        expenses_essentials=expenses_essentials,
        expenses_superfluous=expenses_superfluous,
        reserves=reserves,
        essentials_provided=essentials_provided,
        superfluous_provided=superfluous_provided,
        reserves_provided=reserves_provided,
        essential_deviation=essential_deviation,
        superfluous_deviation=superfluous_deviation,
        reserves_deviation=reserves_deviation,
    )

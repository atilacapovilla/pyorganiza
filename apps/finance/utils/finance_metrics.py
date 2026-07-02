from datetime import date
from django.db.models import Q, Sum

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


def get_finance_balance(request, month, year):
    today = date.today()

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__year=year,
        transaction_date__month=month,
    )

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

    balance = incomes - expenses

    return dict(
        expenses=expenses,
        incomes=incomes,
        balance=balance,
    )


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
        account.current_balance = balance
        account.save()
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
        account.current_balance = balance
        account.save()

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
    )

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

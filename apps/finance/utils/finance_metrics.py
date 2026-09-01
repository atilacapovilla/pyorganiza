from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


def _get_month_totals(request, month, year):
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__year=year,
        transaction_date__month=month,
        is_paid=True,
    ).exclude(category__category_type="transitoria")

    expenses = (
        transactions.filter(category__category_type="despesa").aggregate(
            Sum("transaction_value")
        )["transaction_value__sum"]
        or 0
    )

    incomes = (
        transactions.filter(category__category_type="receita").aggregate(
            Sum("transaction_value")
        )["transaction_value__sum"]
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
    accounts = (
        Account.objects.filter(user=request.user, type__in=("CC", "DN"))
        .with_current_balance()
    )
    balance_total = sum(
        account.computed_balance for account in accounts
    )

    accounts_other = (
        Account.objects.filter(user=request.user)
        .exclude(type__in=("CC", "DN", "CT"))
        .order_by("type", "name")
        .with_current_balance()
    )

    cards_other = (
        Transaction.objects.filter(
            user=request.user,
            account__type="CT",
            type="D",
            is_paid=False,
        )
        .values("due_date")
        .annotate(total=Sum("transaction_value"))
        .order_by("due_date")
    )

    cards_balance_total = sum(
        (card_other.get("total") or 0) for card_other in cards_other
    )

    finance_accounts_balance = dict(
        accounts=accounts,
        accounts_other=accounts_other,
        cards_other=cards_other,
        cards_balance_total=cards_balance_total,
        balance_total=balance_total,
    )
    return finance_accounts_balance


def get_finance_pendents(total_balance, request):
    pendents = Transaction.objects.filter(
        user=request.user,
        is_paid=False,
    ).order_by("due_date")

    expenses_due = (
        pendents.filter(type="D").aggregate(Sum("transaction_value"))[
            "transaction_value__sum"]
        or 0
    )

    incomes_due = (
        pendents.filter(type="C").aggregate(Sum("transaction_value"))[
            "transaction_value__sum"]
        or 0
    )

    balance_pendent = total_balance + incomes_due - expenses_due

    cash_flow_groups = []
    for transaction in pendents:
        if not cash_flow_groups or (
            cash_flow_groups[-1]["due_date"] != transaction.due_date
        ):
            cash_flow_groups.append(
                {
                    "due_date": transaction.due_date,
                    "debit": Decimal("0"),
                    "credit": Decimal("0"),
                }
            )
        group = cash_flow_groups[-1]
        if transaction.type == "D":
            group["debit"] += transaction.transaction_value
        else:
            group["credit"] += transaction.transaction_value

    balance = Decimal(str(total_balance))
    for group in cash_flow_groups:
        balance += group["credit"] - group["debit"]
        group["balance"] = balance

    finance_pendents = dict(
        cash_flow_groups=cash_flow_groups,
        cash_flow_initial=Decimal(str(total_balance)),
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
        is_paid=True,
    ).exclude(category__category_type="transitoria")

    total_incomes = float(
        transactions.filter(category__category_type="receita")
        .aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    expenses_essentials = float(
        transactions.filter(
            category__category_type="despesa", category__metod_503020="50"
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    expenses_superfluous = float(
        transactions.filter(
            category__category_type="despesa", category__metod_503020="30"
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or 0
    )

    reserves = float(
        transactions.filter(
            category__category_type="investimento", category__metod_503020="20"
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
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


MONTH_NAMES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _essential_expenses_breakdown(user, reference_date):
    """Retorna lista dos 6 meses e a média de despesas essenciais."""
    month = reference_date.month
    year = reference_date.year

    rows = []
    for _ in range(6):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        total = (
            Transaction.objects.filter(
                user=user,
                transaction_date__year=year,
                transaction_date__month=month,
                category__category_type="despesa",
                category__essential=True,
                is_paid=True,
            ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
            or Decimal("0")
        )
        rows.append({
            "month": month,
            "year": year,
            "label": f"{MONTH_NAMES_PT[month - 1]}/{year}",
            "total": total,
        })

    rows.reverse()
    count = len(rows)
    grand_total = sum(r["total"] for r in rows)
    average = grand_total / count if count else Decimal("0")
    return rows, grand_total, average


def get_finance_indicators(user):
    """Reserva de emergência, patrimônio líquido e liquidez disponível."""
    all_accounts = (
        Account.objects.filter(user=user, active=True)
        .with_current_balance()
    )

    reserve_value = sum(
        a.computed_balance
        for a in all_accounts
        if a.include_in_emergency_reserve
    )

    liquidity_value = sum(
        a.computed_balance
        for a in all_accounts
        if a.include_in_liquidity
    )

    assets_value = sum(a.computed_balance for a in all_accounts)

    pending_receives = (
        Transaction.objects.filter(
            user=user, type="C", is_paid=False,
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or Decimal("0")
    )

    pending_pays = (
        Transaction.objects.filter(
            user=user, type="D", is_paid=False,
        ).aggregate(Sum("transaction_value"))["transaction_value__sum"]
        or Decimal("0")
    )

    net_worth = assets_value + pending_receives - pending_pays

    essential_rows, essential_total, avg_essential = (
        _essential_expenses_breakdown(user, date.today())
    )
    reserve_months = (
        reserve_value / avg_essential if avg_essential > 0 else None
    )

    return dict(
        reserve_value=reserve_value,
        reserve_months=reserve_months,
        avg_essential_expenses=avg_essential,
        essential_rows=essential_rows,
        essential_total=essential_total,
        net_worth=net_worth,
        assets_value=assets_value,
        pending_receives=pending_receives,
        pending_pays=pending_pays,
        liquidity_value=liquidity_value,
    )

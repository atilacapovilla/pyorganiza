import sweetify
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect
from django.shortcuts import render

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction
from apps.finance.utils.utils import cards_payment


@login_required
def CardList(request):
    template_name = "cards/card_list.html"
    cards = []
    total_card = 0

    accounts = Account.objects.filter(user=request.user, type="CT").order_by("name")
    accounts_debit = Account.objects.filter(user=request.user, type="CC").order_by(
        "name"
    )
    categories = Category.objects.filter(user=request.user)

    if request.method == "GET":
        due_date = request.GET.get("due_date")
        account_id = request.GET.get("account")

        if due_date and account_id:
            cards = Transaction.objects.filter(
                user=request.user, account__id=account_id, due_date=due_date, type="D"
            )
            total_card = (
                cards.filter(is_paid=False).aggregate(Sum("transaction_value"))[
                    "transaction_value__sum"
                ]
                or 0
            )

        context = {
            "accounts": accounts,
            "cards": cards,
            "total_card": total_card,
            "accounts_debit": accounts_debit,
            "categories": categories,
        }
        return render(request, template_name, context)

    if request.method == "POST":
        account_debit = request.POST.get("account_debit")
        category = request.POST.get("category")
        account_id = request.POST.get("account")
        due_date = request.POST.get("due_date")

        if account_debit and category:
            cards, total_card = cards_payment(
                request.user, account_debit, category, account_id, due_date
            )

        sweetify.toast(
            request,
            "Pagamento concluido com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )

        context = {
            "accounts": accounts,
            "cards": cards,
            "total_card": total_card,
            "accounts_debit": accounts_debit,
            "categories": categories,
        }
        return render(request, template_name, context)

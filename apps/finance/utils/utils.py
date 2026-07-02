from django.db.models import Sum

from apps.finance.models.transaction import Transaction


def cards_payment(user, account_debit, category, account_id, due_date):
    cards = Transaction.objects.filter(
        user=user, account__id=account_id, due_date=due_date, type="D"
    )
    total_card = (
        cards.aggregate(Sum("transaction_value"))["transaction_value__sum"] or 0
    )

    for card in cards:
        card.is_paid = True
        card.save()

    transaction = Transaction(
        due_date=due_date,
        is_paid=True,
        account_id=account_debit,
        category_id=category,
        transaction_value=total_card,
        type="D",
        description="Pagamento Cartão de Crédito",
        user=user,
    )
    transaction.save()

    transaction = Transaction(
        due_date=due_date,
        is_paid=True,
        account_id=account_id,
        category_id=category,
        transaction_value=total_card,
        type="C",
        description="Pagamento Cartão de Crédito",
        user=user,
    )
    transaction.save()

    return cards, total_card

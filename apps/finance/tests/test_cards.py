from decimal import Decimal

from django.urls import reverse

from apps.finance.models.transaction import Transaction
from apps.finance.tests.base import BaseFinanceTestCase
from apps.finance.utils.utils import cards_payment


class CardsPaymentTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.card = self._create_account(name="Cartão", type="CT")
        self.due_date = "2026-08-15"

    def _create_card_purchase(self, value, is_paid=False):
        return self._create_transaction(
            value=value,
            type="D",
            account=self.card,
            is_paid=is_paid,
            description="Compra",
            due_date=self.due_date,
        )

    def test_payment_marks_purchases_paid_and_creates_pair(self):
        purchase1 = self._create_card_purchase("120.00")
        purchase2 = self._create_card_purchase("80.00")

        cards, total_card = cards_payment(
            self.user,
            self.checking_account.pk,
            self.expense_category.pk,
            self.card.pk,
            self.due_date,
        )

        self.assertEqual(total_card, Decimal("200.00"))
        purchase1.refresh_from_db()
        purchase2.refresh_from_db()
        self.assertTrue(purchase1.is_paid)
        self.assertTrue(purchase2.is_paid)

        payments = Transaction.objects.filter(
            description="Pagamento Cartão de Crédito"
        ).order_by("type")
        self.assertEqual(payments.count(), 2)
        self.assertEqual(payments.get(type="D").account_id, self.checking_account.pk)
        self.assertEqual(payments.get(type="C").account_id, self.card.pk)
        for payment in payments:
            self.assertEqual(payment.transaction_value, Decimal("200.00"))

    def test_paid_purchase_is_not_charged_again(self):
        already_paid = self._create_card_purchase("50.00", is_paid=True)

        cards, total_card = cards_payment(
            self.user,
            self.checking_account.pk,
            self.expense_category.pk,
            self.card.pk,
            self.due_date,
        )

        self.assertEqual(total_card, 0)
        self.assertEqual(len(cards), 0)
        already_paid.refresh_from_db()
        self.assertTrue(already_paid.is_paid)


class CardViewTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.card = self._create_account(name="Cartão", type="CT")
        self.url = reverse("cards")

    def test_cards_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_list_shows_only_requested_card_transactions(self):
        self._create_transaction(
            value="10.00", type="D", account=self.card,
            description="No cartão", due_date="2026-08-15",
        )
        other_card = self._create_account(name="Outro Cartão", type="CT")
        self._create_transaction(
            value="99.00", type="D", account=other_card,
            description="Em outro cartão", due_date="2026-08-15",
        )

        response = self.client.get(
            self.url, {"account": self.card.pk, "due_date": "2026-08-15"}
        )

        cards = list(response.context["cards"])
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].description, "No cartão")

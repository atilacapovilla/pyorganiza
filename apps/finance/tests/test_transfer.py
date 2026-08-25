from decimal import Decimal

from django.urls import reverse

from apps.finance.models.transaction import Transaction
from apps.finance.tests.base import BaseFinanceTestCase


class TransferViewTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.destination = self._create_account(name="Destino", type="DN")
        self.url = reverse("transfer")

    def _post_transfer(self, origin=None, destination=None, value="100.00"):
        return self.client.post(
            self.url,
            {
                "transaction_date": "2026-08-01",
                "account_origin": (origin or self.checking_account).pk,
                "account_destination": (destination or self.destination).pk,
                "category": self.child_expense_category.pk,
                "transaction_value": value,
                "description": "Transferência teste",
            },
        )

    def test_transfer_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_transfer_creates_debit_and_credit_pair(self):
        self._post_transfer()

        transactions = Transaction.objects.order_by("type")
        self.assertEqual(transactions.count(), 2)

        debit = transactions.get(type="D")
        credit = transactions.get(type="C")
        self.assertEqual(debit.account_id, self.checking_account.pk)
        self.assertEqual(credit.account_id, self.destination.pk)
        self.assertTrue(debit.is_paid and credit.is_paid)
        self.assertEqual(debit.transaction_value, Decimal("100.00"))
        self.assertEqual(credit.transaction_value, Decimal("100.00"))

    def test_transfer_rejects_same_origin_and_destination(self):
        response = self._post_transfer(
            origin=self.checking_account, destination=self.checking_account
        )
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertEqual(Transaction.objects.count(), 0)

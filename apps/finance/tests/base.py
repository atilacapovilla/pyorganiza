from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.finance.models.account import Account
from apps.finance.models.category import Category


class BaseFinanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("owner", password="secret123")
        cls.other_user = User.objects.create_user("other", password="secret123")
        cls.expense_category = Category.objects.create(
            user=cls.user, name="Alimentação", category_type="despesa"
        )
        cls.child_expense_category = Category.objects.create(
            user=cls.user,
            name="Supermercado",
            category_type="despesa",
            parent=cls.expense_category,
        )
        cls.income_category = Category.objects.create(
            user=cls.user, name="Salário", category_type="receita"
        )
        cls.checking_account = Account.objects.create(
            user=cls.user, name="Corrente", type="CC",
            opening_balance=Decimal("100.00"),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _create_account(self, name="Conta", type="CC", opening_balance="0.00", user=None):
        return Account.objects.create(
            user=user or self.user,
            name=name,
            type=type,
            opening_balance=Decimal(opening_balance),
        )

    def _create_category(self, name, category_type="despesa", parent=None, user=None, **kwargs):
        return Category.objects.create(
            user=user or self.user,
            name=name,
            category_type=category_type,
            parent=parent,
            **kwargs,
        )

    def _create_transaction(self, value="10.00", type="D", account=None,
                            category=None, is_paid=False, **kwargs):
        from apps.finance.models.transaction import Transaction

        return Transaction.objects.create(
            user=self.user,
            account=account or self.checking_account,
            category=category or self.expense_category,
            transaction_value=Decimal(value),
            type=type,
            is_paid=is_paid,
            **kwargs,
        )

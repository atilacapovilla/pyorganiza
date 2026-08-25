from datetime import date
from decimal import Decimal

from apps.finance.models.account import Account
from apps.finance.tests.base import BaseFinanceTestCase


class TransactionModelTests(BaseFinanceTestCase):
    def test_default_dates_are_today_not_frozen_at_import(self):
        transaction = self._create_transaction()
        self.assertEqual(transaction.transaction_date, date.today())
        self.assertEqual(transaction.due_date, date.today())


class CategorySpendingTypeTests(BaseFinanceTestCase):
    def test_default_spending_type_is_variavel(self):
        category = self._create_category("Streaming")
        self.assertEqual(category.spending_type, "variavel")
        self.assertEqual(category.get_spending_type_display(), "Variável")

    def test_explicit_fixed_spending_type(self):
        category = self._create_category("Aluguel", spending_type="fixa")
        self.assertEqual(category.get_spending_type_display(), "Fixa")

    def test_form_includes_spending_type_field(self):
        from apps.finance.forms.category_forms import CategoryForm

        form = CategoryForm(user=self.user)
        self.assertIn("spending_type", form.fields)


class CurrentBalanceTests(BaseFinanceTestCase):
    def test_checking_account_counts_only_paid_transactions(self):
        self._create_transaction(value="50.00", type="C", is_paid=True)
        self._create_transaction(value="20.00", type="D", is_paid=False)

        account = Account.objects.get(pk=self.checking_account.pk)
        self.assertEqual(
            account.current_balance, Decimal("150.00")
        )  # 100 inicial + 50 pago; débito de 20 não pago não conta

    def test_credit_card_account_counts_all_transactions(self):
        card = self._create_account(name="Cartão", type="CT")
        self._create_transaction(value="30.00", type="D", account=card, is_paid=False)

        account = Account.objects.get(pk=card.pk)
        self.assertEqual(account.current_balance, Decimal("-30.00"))

    def test_annotated_queryset_matches_property(self):
        card = self._create_account(name="Cartão", type="CT")
        self._create_transaction(value="50.00", type="C", is_paid=True)
        self._create_transaction(value="20.00", type="D", is_paid=False)
        self._create_transaction(value="30.00", type="D", account=card, is_paid=False)

        annotated = {
            account.name: account.computed_balance
            for account in Account.objects.filter(user=self.user).with_current_balance()
        }
        by_name = {a.name: a for a in Account.objects.filter(user=self.user)}
        for name, computed in annotated.items():
            self.assertEqual(computed, by_name[name].current_balance)

    def test_balance_is_isolated_per_user(self):
        other_account = self._create_account(
            name="Outro", user=self.other_user
        )
        from apps.finance.models.transaction import Transaction

        Transaction.objects.create(
            user=self.other_user,
            account=other_account,
            category=self.expense_category,
            transaction_value=Decimal("999.00"),
            type="C",
            is_paid=True,
        )

        account = Account.objects.get(pk=self.checking_account.pk)
        self.assertEqual(account.current_balance, Decimal("100.00"))

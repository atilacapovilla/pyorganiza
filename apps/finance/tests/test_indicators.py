from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction
from apps.finance.tests.base import BaseFinanceTestCase
from apps.finance.utils.finance_metrics import get_finance_indicators


class EmergencyReserveTests(BaseFinanceTestCase):
    """Cenarios 1-5, 10-11: Reserva de emergencia."""

    def _make_essential_category(self, name="Moradia"):
        return self._create_category(
            name, category_type="despesa", essential=True
        )

    def test_account_marked_enters_reserve(self):
        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["reserve_value"], Decimal("100.00")
        )

    def test_account_not_marked_does_not_enter_reserve(self):
        self.checking_account.include_in_emergency_reserve = False
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(indicators["reserve_value"], Decimal("0"))

    def test_savings_marked_enters_reserve(self):
        savings = self._create_account(
            name="Poupanca", type="IN",
            opening_balance="5000.00",
        )
        savings.include_in_emergency_reserve = True
        savings.save()

        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["reserve_value"], Decimal("5100.00")
        )

    def test_investment_not_marked_not_in_reserve_but_in_net_worth(self):
        inv = self._create_account(
            name="CDB", type="IN",
            opening_balance="10000.00",
        )
        inv.include_in_emergency_reserve = False
        inv.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(indicators["reserve_value"], Decimal("0"))
        self.assertEqual(
            indicators["net_worth"],
            Decimal("10000.00") + Decimal("100.00"),
        )

    def test_investment_marked_enters_both(self):
        inv = self._create_account(
            name="CDB", type="IN",
            opening_balance="15000.00",
        )
        inv.include_in_emergency_reserve = True
        inv.save()

        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["reserve_value"], Decimal("15100.00")
        )
        self.assertGreaterEqual(indicators["net_worth"], Decimal("15100.00"))

    def test_reserve_zero_essential_no_division_by_zero(self):
        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertIsNone(indicators["reserve_months"])

    def test_non_essential_expenses_not_in_denominator(self):
        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        expense_account = self._create_account(
            name="Despesas", type="CC", opening_balance="0.00"
        )

        essential = self._make_essential_category("Aluguel")
        non_essential = self._create_category("Cinema", category_type="despesa")

        today = date.today()
        for i in range(6):
            m = today.month - (6 - i)
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            Transaction.objects.create(
                user=self.user,
                account=expense_account,
                category=essential,
                transaction_value=Decimal("1000.00"),
                type="D",
                is_paid=True,
                transaction_date=date(y, m, 5),
            )
            Transaction.objects.create(
                user=self.user,
                account=expense_account,
                category=non_essential,
                transaction_value=Decimal("500.00"),
                type="D",
                is_paid=True,
                transaction_date=date(y, m, 5),
            )

        indicators = get_finance_indicators(self.user)
        self.assertEqual(indicators["reserve_months"], Decimal("0.1"))


class NetWorthTests(BaseFinanceTestCase):
    """Cenarios 6-8: Patrimonio liquido."""

    def test_receivables_increase_net_worth(self):
        Transaction.objects.create(
            user=self.user,
            account=self.checking_account,
            category=self.income_category,
            transaction_value=Decimal("4000.00"),
            type="C",
            is_paid=False,
        )

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["pending_receives"], Decimal("4000.00")
        )
        self.assertEqual(
            indicators["net_worth"],
            Decimal("100.00") + Decimal("4000.00"),
        )

    def test_pays_reduce_net_worth(self):
        Transaction.objects.create(
            user=self.user,
            account=self.checking_account,
            category=self.expense_category,
            transaction_value=Decimal("13500.00"),
            type="D",
            is_paid=False,
        )

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["pending_pays"], Decimal("13500.00")
        )
        self.assertEqual(
            indicators["net_worth"],
            Decimal("100.00") - Decimal("13500.00"),
        )

    def test_transfer_between_own_accounts_does_not_change_net_worth(self):
        savings = self._create_account(
            name="Poupanca", type="IN",
            opening_balance="0.00",
        )

        net_worth_before = get_finance_indicators(self.user)["net_worth"]

        Transaction.objects.create(
            user=self.user,
            account=self.checking_account,
            category=self.expense_category,
            transaction_value=Decimal("1000.00"),
            type="D",
            is_paid=True,
        )
        Transaction.objects.create(
            user=self.user,
            account=savings,
            category=self.income_category,
            transaction_value=Decimal("1000.00"),
            type="C",
            is_paid=True,
        )

        net_worth_after = get_finance_indicators(self.user)["net_worth"]
        self.assertEqual(net_worth_before, net_worth_after)


class TransitoriaTests(BaseFinanceTestCase):
    """Cenario 9: Categoria transitoria nao e receita/despesa."""

    def test_transitoria_not_in_indicators(self):
        cat_trans = self._create_category(
            "Transferencia", category_type="transitoria"
        )
        Transaction.objects.create(
            user=self.user,
            account=self.checking_account,
            category=cat_trans,
            transaction_value=Decimal("500.00"),
            type="D",
            is_paid=True,
        )

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["net_worth"],
            Decimal("100.00") - Decimal("500.00"),
        )


class AverageEssentialExpensesTests(BaseFinanceTestCase):
    """Cenario 12: Media das despesas essenciais."""

    def _make_essential_category(self, name="Moradia"):
        return self._create_category(
            name, category_type="despesa", essential=True
        )

    def test_average_considers_last_6_complete_months(self):
        essential = self._make_essential_category("Moradia")
        today = date.today()

        expense_account = self._create_account(
            name="Despesas", type="CC", opening_balance="0.00"
        )

        for i in range(6):
            m = today.month - (5 - i)
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            Transaction.objects.create(
                user=self.user,
                account=expense_account,
                category=essential,
                transaction_value=Decimal("600.00"),
                type="D",
                is_paid=True,
                transaction_date=date(y, m, 10),
            )

        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(indicators["reserve_months"], Decimal("0.2"))


class NoDoubleCountingTests(BaseFinanceTestCase):
    """Cenario 13: Nao ocorre dupla contabilizacao."""

    def test_investment_in_net_worth_only_once(self):
        inv = self._create_account(
            name="Acoes", type="IN",
            opening_balance="25000.00",
        )
        inv.include_in_emergency_reserve = True
        inv.save()

        self.checking_account.include_in_emergency_reserve = True
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        total_from_accounts = (
            Decimal("100.00") + Decimal("25000.00")
        )
        self.assertEqual(
            indicators["assets_value"], total_from_accounts
        )
        self.assertEqual(
            indicators["reserve_value"], total_from_accounts
        )
        self.assertEqual(
            indicators["net_worth"], total_from_accounts
        )


class LiquidityTests(BaseFinanceTestCase):
    """Cenario adicional: Liquidez disponivel."""

    def test_liquidity_includes_marked_accounts(self):
        self.checking_account.include_in_liquidity = True
        self.checking_account.save()

        inv = self._create_account(
            name="CDB Liquido", type="IN",
            opening_balance="10000.00",
        )
        inv.include_in_liquidity = True
        inv.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(
            indicators["liquidity_value"], Decimal("10100.00")
        )

    def test_liquidity_excludes_unmarked_accounts(self):
        self.checking_account.include_in_liquidity = False
        self.checking_account.save()

        indicators = get_finance_indicators(self.user)
        self.assertEqual(indicators["liquidity_value"], Decimal("0"))


class MigrationDataTests(BaseFinanceTestCase):
    """Verifica que os campos existem e funcionam."""

    def test_form_includes_new_fields(self):
        from apps.finance.forms.account_forms import AccountForm

        form = AccountForm()
        self.assertIn("include_in_emergency_reserve", form.fields)
        self.assertIn("include_in_liquidity", form.fields)

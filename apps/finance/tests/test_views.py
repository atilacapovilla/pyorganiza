from datetime import date
from decimal import Decimal

from django.urls import reverse

from apps.finance.forms.category_forms import CategoryForm
from apps.finance.models.transaction import Transaction
from apps.finance.tests.base import BaseFinanceTestCase


class CategoryFormIsolationTests(BaseFinanceTestCase):
    def test_parent_choices_do_not_leak_other_users_categories(self):
        foreign_category = self._create_category(
            "Categoria Alheia", user=self.other_user
        )

        form = CategoryForm(user=self.user)

        choice_ids = [
            value for value, _ in form.fields["parent"].choices if value
        ]
        self.assertNotIn(foreign_category.pk, choice_ids)

    def test_form_without_user_shows_no_choices(self):
        form = CategoryForm()
        choice_ids = [value for value, _ in form.fields["parent"].choices if value]
        self.assertEqual(choice_ids, [])

    def test_update_view_does_not_offer_foreign_parents(self):
        foreign_category = self._create_category(
            "Outra Categoria", user=self.other_user
        )

        response = self.client.get(
            reverse("category-update", args=[self.expense_category.pk])
        )
        form = response.context["form"]
        choice_ids = [value for value, _ in form.fields["parent"].choices if value]
        self.assertNotIn(foreign_category.pk, choice_ids)


class ExtratoTests(BaseFinanceTestCase):
    def test_extrato_running_balance_per_user(self):
        self._create_transaction(value="1000.00", type="C", is_paid=True)
        self._create_transaction(value="150.00", type="D", is_paid=True)
        # transação de outro usuário não pode aparecer
        from apps.finance.models.transaction import Transaction

        other_account = self._create_account(user=self.other_user)
        Transaction.objects.create(
            user=self.other_user,
            account=other_account,
            category=self.expense_category,
            transaction_value=Decimal("777.00"),
            type="D",
            is_paid=True,
        )

        response = self.client.get(reverse("extrato"))

        rows = response.context["extrato_rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(response.context["saldo_final"], Decimal("950.00"))

    def test_status_filter_vencidos(self):
        self._create_transaction(
            value="100.00", type="D", is_paid=False,
            due_date=date(2026, 1, 10),
        )
        self._create_transaction(value="50.00", type="D", is_paid=False)

        response = self.client.get(
            reverse("extrato"),
            {
                "start_date": "2025-01-01",
                "end_date": "2027-12-31",
                "status": "vencidos",
            },
        )
        rows = response.context["extrato_rows"]
        self.assertEqual(len(rows), 1)

    def test_extrato_pdf_returns_pdf(self):
        response = self.client.get(
            reverse("extrato-pdf"),
            {"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_extrato_pdf_invalid_account_returns_404(self):
        response = self.client.get(
            reverse("extrato-pdf"), {"account": 999999}
        )
        self.assertEqual(response.status_code, 404)


class DashboardTests(BaseFinanceTestCase):
    def test_dashboard_renders_with_data(self):
        self._create_transaction(value="2000.00", type="C", is_paid=True)
        self._create_transaction(value="500.00", type="D", is_paid=True)

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


class InstallmentTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.credit_account = self._create_account(
            name="Cartão Nubank", type="CT",
        )

    def _post_create(self, **kwargs):
        data = {
            "transaction_date": "2026-08-25",
            "due_date": "2026-09-10",
            "account": self.credit_account.pk,
            "category": self.child_expense_category.pk,
            "description": "Compra TV",
            "transaction_value": "1200.00",
            "type": "D",
        }
        data.update(kwargs)
        return self.client.post(reverse("transaction-create"), data)

    def test_divide_creates_correct_number_of_installments(self):
        response = self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        self.assertEqual(response.status_code, 302)
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        self.assertEqual(txns.count(), 3)

    def test_divide_splits_value_equally(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        values = [t.transaction_value for t in txns]
        self.assertEqual(values[0], Decimal("400.00"))
        self.assertEqual(values[1], Decimal("400.00"))
        self.assertEqual(values[2], Decimal("400.00"))
        self.assertEqual(sum(values), Decimal("1200.00"))

    def test_divide_handles_remainder(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
            transaction_value="1000.00",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        values = [t.transaction_value for t in txns]
        self.assertEqual(values[0], Decimal("333.33"))
        self.assertEqual(values[1], Decimal("333.33"))
        self.assertEqual(values[2], Decimal("333.34"))
        self.assertEqual(sum(values), Decimal("1000.00"))

    def test_repeat_keeps_same_value(self):
        self._post_create(
            installment_count="12",
            first_due_date="2026-09-10",
            installment_mode="repeat",
            transaction_value="100.00",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        self.assertEqual(txns.count(), 12)
        for t in txns:
            self.assertEqual(t.transaction_value, Decimal("100.00"))

    def test_only_first_installment_is_paid(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
            is_paid="on",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        self.assertTrue(txns[0].is_paid)
        self.assertFalse(txns[1].is_paid)
        self.assertFalse(txns[2].is_paid)

    def test_due_dates_are_monthly(self):
        self._post_create(
            installment_count="4",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        self.assertEqual(txns[0].due_date, date(2026, 9, 10))
        self.assertEqual(txns[1].due_date, date(2026, 10, 10))
        self.assertEqual(txns[2].due_date, date(2026, 11, 10))
        self.assertEqual(txns[3].due_date, date(2026, 12, 10))

    def test_descriptions_include_installment_number(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).order_by("installment_number")
        self.assertEqual(txns[0].description, "Compra TV (1/3)")
        self.assertEqual(txns[1].description, "Compra TV (2/3)")
        self.assertEqual(txns[2].description, "Compra TV (3/3)")

    def test_all_installments_share_same_group(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        )
        groups = set(t.installment_group for t in txns)
        self.assertEqual(len(groups), 1)
        for t in txns:
            self.assertEqual(t.installment_number is not None, True)
            self.assertEqual(t.total_installments, 3)

    def test_no_installment_fields_creates_single_transaction(self):
        response = self._post_create()
        self.assertEqual(response.status_code, 302)
        txns = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        )
        self.assertEqual(txns.count(), 1)
        self.assertIsNone(txns[0].installment_group)

    def test_delete_removes_all_installments(self):
        self._post_create(
            installment_count="3",
            first_due_date="2026-09-10",
            installment_mode="divide",
        )
        group = Transaction.objects.filter(
            user=self.user, account=self.credit_account,
        ).first().installment_group

        first = Transaction.objects.filter(
            installment_group=group, installment_number=1,
        ).first()
        self.client.post(
            reverse("transaction-delete", args=[first.pk]),
        )
        self.assertEqual(
            Transaction.objects.filter(installment_group=group).count(), 0
        )

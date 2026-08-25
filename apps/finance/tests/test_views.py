from datetime import date
from decimal import Decimal

from django.urls import reverse

from apps.finance.forms.category_forms import CategoryForm
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

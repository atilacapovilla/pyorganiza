from datetime import date

from django.urls import reverse

from apps.finance.tests.base import BaseFinanceTestCase


class BalanceteTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("balancete")

    def _create_category(self, name, category_type, parent=None):
        return super()._create_category(name, category_type, parent=parent)

    def test_balancete_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_totals_by_category_type_for_current_month(self):
        food = self.expense_category

        self._create_transaction(
            value="300.00", type="D", category=food, is_paid=True,
            description="Mercado",
        )
        # transação fora do mês consultado não deve entrar
        self._create_transaction(
            value="500.00", type="D", category=food, is_paid=True,
            description="Mês passado",
        )
        from apps.finance.models.transaction import Transaction

        Transaction.objects.filter(description="Mês passado").update(
            transaction_date=date(2026, 7, 10)
        )

        response = self.client.get(self.url, {"month": 8, "year": 2026})

        self.assertEqual(response.context["total_despesas_curr"], 300.0)
        self.assertEqual(
            response.context["total_receitas_curr"], 0.0
        )  # nenhuma receita criada
        self.assertEqual(response.context["total_investimentos_curr"], 0.0)
        self.assertEqual(response.context["saldo_curr"], -300.0)

    def test_january_rolls_back_to_december_previous_year(self):
        self._create_transaction(value="100.00", type="D", is_paid=True)
        from apps.finance.models.transaction import Transaction

        Transaction.objects.all().update(transaction_date=date(2025, 12, 20))

        response = self.client.get(self.url, {"month": 1, "year": 2026})

        self.assertEqual(response.context["prev_month"], 12)
        self.assertEqual(response.context["prev_year"], 2025)
        self.assertEqual(response.context["total_despesas_prev"], 100.0)
        self.assertEqual(response.context["total_despesas_curr"], 0.0)

    def test_tree_aggregates_child_values_into_parent(self):
        parent = self._create_category("Moradia", "despesa")
        child = self._create_category("Aluguel", "despesa", parent=parent)

        self._create_transaction(
            value="1200.00", type="D", category=child, is_paid=True,
            description="Aluguel agosto",
        )
        self._create_transaction(
            value="100.00", type="D", category=self.expense_category, is_paid=True,
            description="Outra despesa",
        )

        response = self.client.get(self.url, {"month": 8, "year": 2026})

        tree = response.context["tree"]
        parent_node = next(n for n in tree if n["category"].pk == parent.pk)
        self.assertEqual(parent_node["curr_total"], 1200.0)
        self.assertEqual(len(parent_node["children"]), 1)

    def test_invalid_month_falls_back_to_current_month(self):
        today = date.today()
        response = self.client.get(self.url, {"month": 99, "year": 2026})
        self.assertEqual(response.context["selected_month"], today.month)

    def test_balancete_pdf_returns_pdf(self):
        self._create_transaction(value="50.00", type="D", is_paid=True)

        response = self.client.get(
            reverse("balancete-pdf"), {"month": 8, "year": 2026}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

from django.urls import reverse

from apps.finance.tests.base import BaseFinanceTestCase
from apps.finance.utils.category_ordering import (
    sort_categories,
    type_priority_annotation,
)


class CategoryOrderingTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        # inserção proposital fora de ordem
        self.invest_root = self._create_category("Fundos", "investimento")
        self.despesa_z = self._create_category("Zona Leste", "despesa")
        self.receita_b = self._create_category("Bônus", "receita")
        self.transitoria = self._create_category("Pix", "transitoria")
        self.receita_a = self._create_category("Aluguel Recebido", "receita")
        self.despesa_a = self._create_category("Água", "despesa")

        self.child_mercado = self._create_category(
            "Mercado", parent=self.despesa_a
        )
        self.child_acougue = self._create_category(
            "Açougue", parent=self.despesa_a
        )

    def test_sort_categories_type_then_alphabetical(self):
        ordered = sort_categories(
            [
                self.despesa_z,
                self.transitoria,
                self.receita_b,
                self.invest_root,
                self.receita_a,
                self.despesa_a,
            ]
        )
        # receitas primeiro (alfa), depois despesas, investimento, transitoria
        expected = [
            self.receita_a,
            self.receita_b,
            self.despesa_a,  # "Agua" antes de "Zona Leste" (sem acento)
            self.despesa_z,
            self.invest_root,
            self.transitoria,
        ]
        self.assertEqual(ordered, expected)

    def test_list_tree_orders_types_parents_and_children(self):
        response = self.client.get(reverse("categories"))
        tree = response.context["tree"]
        root_names = [node["category"].name for node in tree]

        # raízes agrupadas por tipo e alfa dentro do tipo;
        # filhos de Água em ordem alfa
        agua_node = next(
            node for node in tree if node["category"].name == "Água"
        )
        child_names = [child["category"].name for child in agua_node["children"]]

        self.assertEqual(child_names, ["Açougue", "Mercado"])
        self.assertLess(
            root_names.index("Aluguel Recebido"), root_names.index("Bônus")
        )
        self.assertLess(root_names.index("Bônus"), root_names.index("Zona Leste"))

    def test_queryset_annotation_matches_python_order(self):
        from apps.finance.models.category import Category
        from apps.finance.utils.category_ordering import CATEGORY_TYPE_PRIORITY

        qs = (
            Category.objects.filter(user=self.user)
            .annotate(type_order=type_priority_annotation())
            .order_by("type_order", "name")
        )
        # agrupamento por prioridade de tipo deve bater com o helper;
        # dentro do tipo vale a ordenação do banco
        expected = sorted(
            Category.objects.filter(user=self.user),
            key=lambda c: (CATEGORY_TYPE_PRIORITY[c.category_type], c.name),
        )
        self.assertEqual(list(qs), expected)

    def test_transaction_form_orders_receitas_first(self):
        from apps.finance.forms.transaction_forms import TransactionForm

        form = TransactionForm(initial={"user": self.user})
        categories = list(form.fields["category"].queryset)
        type_sequence = [c.category_type for c in categories]
        first_despesa = type_sequence.index("despesa")
        self.assertNotIn("receita", type_sequence[first_despesa:])

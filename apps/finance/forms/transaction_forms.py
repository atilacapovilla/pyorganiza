from django import forms
from django.forms.models import ModelChoiceField

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


class HierarchicalCategoryField(ModelChoiceField):
    def label_from_instance(self, obj):
        parts = []
        p = obj
        while p:
            parts.append(p.name)
            p = p.parent
        return " \u2192 ".join(reversed(parts))


class TransactionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        user = kwargs["initial"]["user"]
        self.fields["account"].queryset = Account.objects.filter(user=user)
        self.fields["category"] = HierarchicalCategoryField(
            queryset=Category.objects.filter(
                user=user, parent__isnull=False
            ).select_related("parent").order_by("category_type", "parent__name", "name"),
            widget=self.fields["category"].widget,
            required=self.fields["category"].required,
            label=self.fields["category"].label,
        )

    transaction_date = forms.DateField(
        widget=forms.TextInput(attrs={"type": "date"}), label="Data da Transação"
    )
    due_date = forms.DateField(
        widget=forms.TextInput(attrs={"type": "date"}), label="Data de Vencimento"
    )

    class Meta:
        model = Transaction
        fields = [
            "transaction_date",
            "due_date",
            "is_paid",
            "account",
            "category",
            "description",
            "transaction_value",
            "type",
        ]

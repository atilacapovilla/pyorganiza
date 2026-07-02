from django import forms

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


class TransactionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        user = kwargs["initial"]["user"]
        self.fields["account"].queryset = Account.objects.filter(user=user)
        self.fields["category"].queryset = Category.objects.filter(
            user=user, parent__isnull=False
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

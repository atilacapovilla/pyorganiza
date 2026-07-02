from django import forms

from apps.finance.models.category import Category
from apps.finance.models.account import Account


class TransferForm(forms.Form):
    transaction_date = forms.DateField(
        label="Data da Transferencia",
        widget=forms.TextInput(attrs={"type": "date"}),
        required=True,
    )

    account_destination = forms.ChoiceField(
        label="Conta de Destino",
        required=True,
    )
    account_origin = forms.ChoiceField(
        label="Conta de Origem",
        required=True,
    )
    category = forms.ChoiceField(
        label="Categoria",
        required=True,
    )

    transaction_value = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Valor da Transferencia",
        required=True,
    )

    description = forms.CharField(
        max_length=50,
        label="Descrição",
        required=False,
    )

    def __init__(self, user=None, *args, **kwargs):
        super(TransferForm, self).__init__(*args, **kwargs)

        ACCOUNT_OPTIONS = [
            (account.id, account) for account in Account.objects.filter(user=user)
        ]

        CATEGORY_OPTIONS = [
            (category.id, category)
            for category in Category.objects.filter(user=user)
        ]

        self.fields["account_origin"].choices = ACCOUNT_OPTIONS
        self.fields["account_destination"].choices = ACCOUNT_OPTIONS
        self.fields["category"].choices = CATEGORY_OPTIONS

    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get("account_origin")
        destination = cleaned_data.get("account_destination")

        if origin == destination:
            msg = "Contas Origem e Destino não podem ser iguais."
            self.add_error("account_origin", msg)
            self.add_error("account_destination", msg)

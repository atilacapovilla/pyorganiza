from django import forms

from apps.finance.models.account import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["name", "type", "opening_balance", "logo", "active"]

        labels = {
            "name": ("Nome"),
            "type": ("Tipo de Conta"),
            "opening_balance": ("Saldo Inicial"),
            "logo": ("Logotipo"),
            "active": ("Conta Ativa"),
        }

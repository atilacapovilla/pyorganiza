from django import forms

from apps.finance.models.account import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            "name", "type", "opening_balance", "logo", "active",
            "include_in_emergency_reserve", "include_in_liquidity",
        ]

        labels = {
            "name": ("Nome"),
            "type": ("Tipo de Conta"),
            "opening_balance": ("Saldo Inicial"),
            "logo": ("Logotipo"),
            "active": ("Conta Ativa"),
            "include_in_emergency_reserve": ("Reserva de Emergência"),
            "include_in_liquidity": ("Liquidez Disponível"),
        }

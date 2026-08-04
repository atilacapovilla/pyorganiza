from django import forms

from apps.finance.models.account import Account


class ImportUploadForm(forms.Form):
    file = forms.FileField(
        label="Arquivo OFX",
        widget=forms.FileInput(attrs={"accept": ".ofx,.qfx"}),
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label="Conta destino",
        required=True,
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["account"].queryset = Account.objects.filter(user=user)

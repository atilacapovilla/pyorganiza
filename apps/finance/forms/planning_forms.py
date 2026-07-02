from django import forms


class PlanningForm(forms.Form):
    month = forms.ChoiceField(label="Mês")
    year = forms.ChoiceField(label="Ano")

    def __init__(self, *args, **kwargs):
        month_names = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        super().__init__(*args, **kwargs)
        self.fields["month"].choices = [(i + 1, name) for i, name in enumerate(month_names)]
        self.fields["year"].choices = [(y, str(y)) for y in range(2020, 2036)]

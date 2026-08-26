from django import forms
from django.forms.models import ModelChoiceField, ModelChoiceIterator

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction
from apps.finance.utils.category_ordering import type_priority_annotation


class HierarchicalCategoryField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class CategoryByTypeIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset.all()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        groups = {}
        for obj in queryset:
            type_display = obj.get_category_type_display()
            groups.setdefault(type_display, []).append(self.choice(obj))
        type_choices = Category._meta.get_field("category_type").choices
        type_order = {label: idx for idx, (key, label) in enumerate(type_choices)}
        for group_label, group_choices in sorted(
            groups.items(), key=lambda item: type_order.get(item[0], len(type_choices))
        ):
            yield (group_label, group_choices)


class HierarchicalCategoryByTypeField(HierarchicalCategoryField):
    iterator = CategoryByTypeIterator


INSTALLMENT_MODE_CHOICES = (
    ("divide", "Dividir valor total"),
    ("repeat", "Repetir valor por lançamento"),
)

DATE_BEHAVIOR_CHOICES = (
    ("keep", "Manter data da compra original"),
    ("increment", "Incrementar data da compra"),
)


class TransactionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        user = kwargs["initial"]["user"]
        self.fields["account"].queryset = Account.objects.filter(user=user)
        self.fields["category"] = HierarchicalCategoryByTypeField(
            queryset=Category.objects.filter(
                user=user, parent__isnull=False
            ).select_related("parent").annotate(
                type_order=type_priority_annotation()
            ).order_by("type_order", "parent__name", "name"),
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
    installment_count = forms.IntegerField(
        required=False,
        min_value=2,
        max_value=48,
        widget=forms.NumberInput(attrs={"min": "2", "max": "48", "placeholder": "Ex: 12"}),
        label="Nº de Lançamentos",
    )

    first_due_date = forms.DateField(
        required=False,
        widget=forms.TextInput(attrs={"type": "date"}),
        label="1º Vencimento",
    )

    installment_mode = forms.ChoiceField(
        required=False,
        choices=INSTALLMENT_MODE_CHOICES,
        initial="divide",
        label="Como dividir?",
        widget=forms.RadioSelect,
    )

    date_behavior = forms.ChoiceField(
        required=False,
        choices=DATE_BEHAVIOR_CHOICES,
        initial="keep",
        label="Data da compra nas parcelas",
        widget=forms.RadioSelect,
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

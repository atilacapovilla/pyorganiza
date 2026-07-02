from django import forms

from apps.finance.models.category import Category


class CategoryForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.TextInput(attrs={"type": "color"}),
        label="Cor",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].required = False
        self.fields["parent"].choices = self._build_hierarchical_choices()

    def _build_hierarchical_choices(self):
        categories = list(Category.objects.all().select_related("parent"))

        exclude_ids = set()
        if self.instance and self.instance.pk:
            exclude_ids.add(self.instance.pk)
            for c in categories:
                p = c.parent
                while p:
                    if p.pk == self.instance.pk:
                        exclude_ids.add(c.pk)
                        break
                    p = p.parent

        choices = [("", "---------")]

        def add_children(parent, depth):
            for c in categories:
                if c.parent == parent and c.pk not in exclude_ids:
                    choices.append((c.pk, "\u00A0\u00A0\u00A0\u00A0" * depth + c.name))
                    add_children(c, depth + 1)

        for c in categories:
            if c.parent is None and c.pk not in exclude_ids:
                choices.append((c.pk, c.name))
                add_children(c, 1)

        return choices

    class Meta:
        model = Category
        fields = ["name", "color", "category_type",
                  "essential", "metod_503020", "parent"]

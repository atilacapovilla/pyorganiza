import unicodedata

from django.db.models import Case, IntegerField, Value, When

from apps.finance.models.category import Category


def _build_type_priority():
    choices = Category._meta.get_field("category_type").choices
    return {
        value: index
        for index, (value, _) in enumerate(choices)
    }


CATEGORY_TYPE_PRIORITY = _build_type_priority()


def _name_sort_key(name):
    normalized = unicodedata.normalize("NFKD", name)
    return normalized.encode("ascii", "ignore").decode("ascii").lower().strip()


def category_sort_key(category):
    return (
        CATEGORY_TYPE_PRIORITY.get(category.category_type, len(CATEGORY_TYPE_PRIORITY)),
        _name_sort_key(category.name),
    )


def sort_categories(categories):
    """Ordena por tipo (receita, despesa, demais) e nome alfabético."""
    return sorted(categories, key=category_sort_key)


def type_priority_annotation():
    """Annotation para ordenar querysets de Category pela prioridade de tipo."""
    whens = [
        When(category_type=value, then=Value(index))
        for index, (value, _) in enumerate(
            Category._meta.get_field("category_type").choices
        )
    ]
    return Case(*whens, default=Value(len(whens)), output_field=IntegerField())

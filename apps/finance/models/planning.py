from django.conf import settings
from django.db import models

from apps.finance.models.category import Category


class Planning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField(verbose_name="Mês")
    year = models.IntegerField(verbose_name="Ano")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, verbose_name="Categoria"
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Valor"
    )

    class Meta:
        unique_together = ("user", "month", "year", "category")
        ordering = ["year", "month", "category__name"]
        verbose_name = "Planejamento"
        verbose_name_plural = "Planejamentos"

    def __str__(self):
        return f"{self.category.name} ({self.month}/{self.year}): {self.value}"

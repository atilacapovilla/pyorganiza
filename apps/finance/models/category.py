from django.conf import settings
from django.db import models


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100, verbose_name="Nome")

    color = models.CharField(
        max_length=7,
        default="#3498db",
        verbose_name="Cor",
    )

    category_type = models.CharField(
        max_length=15,
        choices=[('receita', 'Receita'), ('despesa', 'Despesa'),
                 ('investimento', 'Investimentos')],
        verbose_name="Tipo de Categoria"
    )

    essential = models.BooleanField(default=False, verbose_name="Essencial")

    metod_503020 = models.CharField(
        max_length=10,
        choices=[
            ('50', '50% - Necessidades'),
            ('30', '30% - Desejos'),
            ('20', '20% - Poupança / Investimentos'),
            ('00', 'Não se aplica em receitas')
        ],
        null=True, blank=True,
        verbose_name="Método 50/30/20"
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Pai"
    )

    def __str__(self):
        return self.name

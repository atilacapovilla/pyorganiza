from django.conf import settings
from django.db import models

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


class ImportedTransaction(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendente"),
        ("matched", "Conciliada"),
        ("ignored", "Ignorada"),
        ("imported", "Importada"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuário"
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, verbose_name="Conta"
    )
    import_batch = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da Importação"
    )
    bank_fit_id = models.CharField(max_length=255, verbose_name="ID do Banco")
    transaction_date = models.DateField(verbose_name="Data")
    description = models.TextField(verbose_name="Descrição")
    transaction_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor"
    )
    type = models.CharField(
        max_length=1,
        choices=[("C", "Crédito"), ("D", "Débito")],
        verbose_name="Tipo",
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="Status"
    )
    matched_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Transação Conciliada",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transação Importada"
        verbose_name_plural = "Transações Importadas"
        ordering = ["transaction_date"]

    def __str__(self):
        return f"{self.transaction_date} - {self.description} - {self.transaction_value}"

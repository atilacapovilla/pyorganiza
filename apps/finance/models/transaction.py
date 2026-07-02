from apps.finance.models import *


class Transaction(models.Model):
    TYPE_CHOICE = (
        ("C", "Credito"),
        ("D", "Debito"),
    )
    transaction_date = models.DateField(
        default=datetime.now, verbose_name="Data da Transação"
    )
    due_date = models.DateField(default=datetime.now, verbose_name="Data de Vencimento")
    is_paid = models.BooleanField(default=False, verbose_name="Pago ou Recebido")
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="accounts", verbose_name="Conta"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="categories",
        verbose_name="categoria",
    )
    description = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Descrição"
    )
    transaction_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor"
    )
    type = models.CharField(
        max_length=1, choices=TYPE_CHOICE, default="D", verbose_name="Tipo"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Alterado em")
    active = models.BooleanField("Categoria Ativa", default=True)

    def __str__(self):
        return f"{self.description} - {self.transaction_date} - {self.due_date} - {self.transaction_value}"

    class Meta:
        ordering = ["-transaction_date", "due_date", "type"]
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

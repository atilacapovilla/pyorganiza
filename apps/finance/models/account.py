from apps.finance.models import *
from PIL import Image


class Account(models.Model):
    TYPE_CHOICE = (
        ("CC", "Conta Corrente"),
        ("DN", "Dinheiro"),
        ("CT", "Cartão Crédito"),
        ("IN", "Investimentos"),
    )
    name = models.CharField(max_length=50, verbose_name="Nome")
    type = models.CharField(
        max_length=2, choices=TYPE_CHOICE, default="CC", verbose_name="Tipo"
    )
    logo = models.ImageField(
        upload_to="images/", default="sem_imagem.png", verbose_name="Logotipo"
    )
    opening_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default="0.00", verbose_name="Saldo Inicial"
    )
    current_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default="0.00", verbose_name="Saldo Atual"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Alterado em")
    active = models.BooleanField("Conta Ativa", default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.logo.path)
        if img.height > 32 or img.width > 32:
            output_size = (32, 32)
            img.thumbnail(output_size)
            img.save(self.logo.path)

    class Meta:
        ordering = ["name"]
        verbose_name = "Conta"
        verbose_name_plural = "Contas"

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from PIL import Image

BALANCE_OUTPUT_FIELD = DecimalField(max_digits=14, decimal_places=2)


class AccountQuerySet(models.QuerySet):
    def with_current_balance(self):
        counts_all = ~Q(type__in=self.model.PAID_ONLY_TYPES)
        return self.annotate(
            computed_balance=ExpressionWrapper(
                F("opening_balance")
                + Coalesce(
                    Sum(
                        "accounts__transaction_value",
                        filter=Q(accounts__type="C")
                        & (counts_all | Q(accounts__is_paid=True)),
                    ),
                    models.Value(0),
                    output_field=BALANCE_OUTPUT_FIELD,
                )
                - Coalesce(
                    Sum(
                        "accounts__transaction_value",
                        filter=Q(accounts__type="D")
                        & (counts_all | Q(accounts__is_paid=True)),
                    ),
                    models.Value(0),
                    output_field=BALANCE_OUTPUT_FIELD,
                ),
                output_field=BALANCE_OUTPUT_FIELD,
            )
        )


class Account(models.Model):
    TYPE_CHOICE = (
        ("CC", "Conta Corrente"),
        ("DN", "Dinheiro"),
        ("CT", "Cartão Crédito"),
        ("IN", "Investimentos"),
    )

    PAID_ONLY_TYPES = ("CC", "DN")

    objects = AccountQuerySet.as_manager()

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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuário"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Alterado em")
    active = models.BooleanField("Conta Ativa", default=True)
    include_in_emergency_reserve = models.BooleanField(
        default=False,
        verbose_name="Considerar na reserva de emergência",
    )
    include_in_liquidity = models.BooleanField(
        default=False,
        verbose_name="Considerar na liquidez disponível",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Conta"
        verbose_name_plural = "Contas"

    def __str__(self):
        return self.name

    @property
    def current_balance(self):
        if hasattr(self, "computed_balance"):
            return self.computed_balance
        qs = self.accounts.all()
        if self.type in self.PAID_ONLY_TYPES:
            qs = qs.filter(is_paid=True)
        totals = qs.aggregate(
            incomes=Sum("transaction_value", filter=Q(type="C")),
            expenses=Sum("transaction_value", filter=Q(type="D")),
        )
        incomes = totals["incomes"] or 0
        expenses = totals["expenses"] or 0
        return self.opening_balance + incomes - expenses

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.logo and not self.logo.name.endswith("sem_imagem.png"):
            try:
                img = Image.open(self.logo.path)
                if img.height > 32 or img.width > 32:
                    output_size = (32, 32)
                    img.thumbnail(output_size)
                    img.save(self.logo.path)
            except (FileNotFoundError, ValueError):
                pass

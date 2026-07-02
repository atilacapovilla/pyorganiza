from django.contrib import admin

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction
from apps.finance.models.planning import Planning


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "parent",
        "color",
    )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "opening_balance", "current_balance")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_date",
        "due_date",
        "account",
        "description",
        "transaction_value",
        "is_paid",
        "type",
    )


@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "month", "year", "value")
    list_filter = ("month", "year", "user")

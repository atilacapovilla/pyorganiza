from django.contrib import admin

from apps.finance.models.category import Category
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction
from apps.finance.models.planning import Planning
from apps.finance.models.imported_transaction import ImportedTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "parent",
        "color",
        "category_type",
        "spending_type",
    )
    list_filter = ("category_type", "spending_type")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "name", "type", "opening_balance", "account_current_balance",
        "include_in_emergency_reserve", "include_in_liquidity",
    )
    list_filter = ("type", "include_in_emergency_reserve", "include_in_liquidity")

    def get_queryset(self, request):
        return super().get_queryset(request).with_current_balance()

    @admin.display(description="Saldo Atual")
    def account_current_balance(self, obj):
        return obj.current_balance


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


@admin.register(ImportedTransaction)
class ImportedTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "description", "transaction_value", "type", "status", "account")
    list_filter = ("status",)

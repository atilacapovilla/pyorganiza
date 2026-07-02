from django.urls import path

from apps.finance.views.transaction_views import (
    TransactionList,
    TransactionCreate,
    TransactionUpdate,
    TransactionDelete,
)

urlpatterns = [
    path("transactions/", TransactionList.as_view(), name="transactions"),
    path("transaction/create/", TransactionCreate.as_view(), name="transaction-create"),
    path(
        "transaction/update/<int:pk>/",
        TransactionUpdate.as_view(),
        name="transaction-update",
    ),
    path(
        "transaction/delete/<int:pk>/",
        TransactionDelete.as_view(),
        name="transaction-delete",
    ),
]

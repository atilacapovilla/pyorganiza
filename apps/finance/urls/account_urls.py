from django.urls import path

from apps.finance.views.account_views import (
    AccountList,
    AccountCreate,
    AccountUpdate,
    AccountDelete,
)


urlpatterns = [
    path("accounts/", AccountList.as_view(), name="accounts"),
    path("account/create/", AccountCreate.as_view(), name="account-create"),
    path("account/update/<int:pk>/", AccountUpdate.as_view(), name="account-update"),
    path("account/delete/<int:pk>/", AccountDelete.as_view(), name="account-delete"),
]

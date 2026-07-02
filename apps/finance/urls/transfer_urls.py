from django.urls import path

from apps.finance.views.transfer_views import Transfer


urlpatterns = [
    path("transfer/", Transfer, name="transfer"),
]

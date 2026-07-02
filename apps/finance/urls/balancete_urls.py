from django.urls import path

from apps.finance.views.balancete_views import balancete, balancete_pdf


urlpatterns = [
    path("balancete/", balancete, name="balancete"),
    path("balancete/pdf/", balancete_pdf, name="balancete-pdf"),
]

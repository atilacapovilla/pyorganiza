from django.urls import path

from apps.finance.views.extrato_views import extrato, extrato_pdf


urlpatterns = [
    path("extrato/", extrato, name="extrato"),
    path("extrato/pdf/", extrato_pdf, name="extrato-pdf"),
]

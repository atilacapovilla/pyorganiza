from django.urls import path

from apps.finance.views.planning_views import planning_definir, planning_consulta, planning_consulta_pdf


urlpatterns = [
    path("planejamento/", planning_definir, name="planning-definir"),
    path("planejamento/consulta/", planning_consulta, name="planning-consulta"),
    path("planejamento/consulta/pdf/", planning_consulta_pdf, name="planning-consulta-pdf"),
]

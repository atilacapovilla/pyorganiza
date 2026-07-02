from django.urls import path

from apps.finance.views.dashboard_views import dashboard


urlpatterns = [path("dashboard/", dashboard, name="dashboard")]

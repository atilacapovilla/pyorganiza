from django.urls import path

from apps.finance.views.import_views import (
    import_upload,
    import_reconciliation,
    import_match,
    import_accept,
    import_ignore,
)

urlpatterns = [
    path("import/", import_upload, name="import-upload"),
    path("import/reconciliation/", import_reconciliation, name="import-reconciliation"),
    path("import/match/<int:pk>/", import_match, name="import-match"),
    path("import/accept/<int:pk>/", import_accept, name="import-accept"),
    path("import/ignore/<int:pk>/", import_ignore, name="import-ignore"),
]

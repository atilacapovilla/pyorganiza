from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    # home
    path("", include("apps.home.urls")),
    # course
    path("", include("apps.course.urls.subject_urls")),
    path("", include("apps.course.urls.course_urls")),
    path("", include("apps.course.urls.note_urls")),
    # finance
    path("", include("apps.finance.urls.category_urls")),
    path("", include("apps.finance.urls.account_urls")),
    path("", include("apps.finance.urls.transaction_urls")),
    path("", include("apps.finance.urls.transfer_urls")),
    path("", include("apps.finance.urls.cards_urls")),
    path("", include("apps.finance.urls.dashboard_urls")),
    path("", include("apps.finance.urls.extrato_urls")),
    path("", include("apps.finance.urls.balancete_urls")),
    path("", include("apps.finance.urls.planning_urls")),
    path("", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

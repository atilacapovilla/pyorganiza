from django.urls import path

from apps.course.views.subject_views import (
    SubjectList,
    SubjectCreate,
    SubjectUpdate,
    SubjectDelete,
)

urlpatterns = [
    path("subjects/", SubjectList.as_view(), name="subjects"),
    path("subject/create/", SubjectCreate.as_view(), name="subject-create"),
    path("subject/update/<int:pk>/", SubjectUpdate.as_view(), name="subject-update"),
    path("subject/delete/<int:pk>/", SubjectDelete.as_view(), name="subject-delete"),
]

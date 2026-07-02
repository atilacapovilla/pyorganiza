from django.urls import path

from apps.course.views.note_views import (
    NoteList,
    NoteCreate,
    NoteUpdate,
    NoteDelete,
    NoteDetail,
    note_report,
)

urlpatterns = [
    path("notes/", NoteList.as_view(), name="note-list"),
    path("note/create/", NoteCreate.as_view(), name="note-create"),
    path(
        "note/update/<int:pk>/",
        NoteUpdate.as_view(),
        name="note-update",
    ),
    path(
        "note/delete/<int:pk>/",
        NoteDelete.as_view(),
        name="note-delete",
    ),
    path("note/detail/<int:pk>/", NoteDetail.as_view(), name="note-detail"),
    # path("notes/<int:course_id>/", NoteList.as_view(), name="note-list"),
    # Reports
    path("note/report/<int:id>", note_report, name="note_report"),
]

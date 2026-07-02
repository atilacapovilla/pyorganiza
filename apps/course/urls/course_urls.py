from django.urls import path

from apps.course.views.course_views import (
    CourseList,
    CourseCreate,
    CourseUpdate,
    CourseDelete,
)

urlpatterns = [
    path("courses/", CourseList.as_view(), name="courses"),
    path("course/create/", CourseCreate.as_view(), name="course-create"),
    path("course/update/<int:pk>/", CourseUpdate.as_view(), name="course-update"),
    path("course/delete/<int:pk>/", CourseDelete.as_view(), name="course-delete"),
]

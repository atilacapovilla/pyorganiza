from django.contrib import admin

from apps.course.models.course import Course
from apps.course.models.note import Note
from apps.course.models.subject import Subject

admin.site.register(Subject)
admin.site.register(Course)
admin.site.register(Note)

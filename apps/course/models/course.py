from django.conf import settings
from django.db import models

from apps.course.models.subject import Subject


class Course(models.Model):
    title = models.CharField(max_length=100)
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='courses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["title"]

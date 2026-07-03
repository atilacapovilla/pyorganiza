import markdown
from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe

from apps.course.models.course import Course


class Note(models.Model):
    title = models.CharField(max_length=100)
    order = models.IntegerField()
    content = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="notes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def formatted_content(self):
        return mark_safe(
            markdown.markdown(self.content, extensions=["fenced_code", "tables"])
        )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Anotação"
        verbose_name_plural = "Anotações"
        ordering = ["created_at", "title"]

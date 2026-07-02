from django import forms
from apps.course.models import Subject


class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = ["title", "active"]
        labels = {
            "title": ("Título"),
            "active": ("Assunto Ativo"),
        }

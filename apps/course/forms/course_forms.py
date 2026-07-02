from django import forms
from apps.course.models import Course
from apps.course.models import Subject


class CourseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        usuario = kwargs["initial"]["usuario"]
        self.fields["subject"].queryset = Subject.objects.filter(user=usuario)

    class Meta:
        model = Course
        fields = ["title", "subject", "active"]

        labels = {
            "title": ("Título"),
            "description": ("Descrição"),
            "subject": ("Assunto"),
            "active": ("Curso Ativo"),
        }

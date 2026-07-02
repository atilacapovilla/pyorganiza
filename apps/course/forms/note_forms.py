from django import forms

from apps.course.models import Note


class NoteForm(forms.ModelForm):

    class Meta:
        model = Note
        fields = ["title", "order", "course", "content", "active"]
        widgets = {
            "content": forms.Textarea(
                attrs={"id": "id_content", "rows": 20, "cols": 80}
            )
        }
        labels = {
            "title": ("Título"),
            "course": ("Curso"),
            "content": ("Conteúdo"),
            "active": ("Anotação Ativa"),
            "order": ("Ordem"),
        }

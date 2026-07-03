from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

from apps.course.models.course import Course
from apps.course.models.note import Note
from apps.course.forms.note_forms import NoteForm

# weasyprint
from django.core.files.storage import FileSystemStorage
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML, CSS


class NoteList(LoginRequiredMixin, ListView):
    model = Note
    context_object_name = "notes"
    template_name = "note/note_list.html"
    paginate_by = 12

    def get_queryset(self):
        notes = Note.objects.filter(
            user=self.request.user).order_by("course", "order")

        course_id = self.request.GET.get("course")
        if course_id:
            notes = notes.filter(course_id=course_id)

        query = self.request.GET.get("search")
        if query:
            notes = notes.filter(title__icontains=query)
        return notes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = Course.objects.all()
        return context


class NoteCreate(LoginRequiredMixin, CreateView):
    model = Note
    template_name = "note/note_form.html"
    form_class = NoteForm
    paginate_by = 10

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "A Anotação foi criada com sucesso.")
        return super(NoteCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("note-detail", kwargs={"pk": self.object.pk})


class NoteUpdate(LoginRequiredMixin, UpdateView):
    model = Note
    template_name = "note/note_form.html"
    form_class = NoteForm

    def form_valid(self, form):
        messages.success(self.request, 'A Anotação foi alterada com sucesso.')
        return super(NoteUpdate, self).form_valid(form)

    def get_queryset(self):
        base_qs = super(NoteUpdate, self).get_queryset()
        return base_qs.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy("note-detail", kwargs={"pk": self.object.pk})


class NoteDelete(LoginRequiredMixin, DeleteView):
    model = Note
    context_object_name = "note"
    template_name = "note/note_confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, 'A Anotação foi excluida com sucesso.')
        return super().form_valid(form)

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy("note-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["course_id"] = self.object.course_id
        context["back_url"] = reverse_lazy("note-list")
        context["page_title"] = "Editar Anotação"
        context["submit_label"] = "Atualizar"

        return context


class NoteDetail(LoginRequiredMixin, DetailView):
    model = Note
    context_object_name = "note"
    template_name = "note/note_detail.html"

    def get_queryset(self):
        base_qs = super(NoteDetail, self).get_queryset()
        return base_qs.filter(user=self.request.user)


def note_report(request, id):
    note = get_object_or_404(Note, pk=id)
    html_string = render_to_string(
        "note/reports/note_report.html", {"note": note})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="aula_{note.course}_{note.title}.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/note_pdf.css"))]
    )
    return response

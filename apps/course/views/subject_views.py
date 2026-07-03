from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, CreateView, UpdateView

from apps.course.models.subject import Subject
from apps.course.forms.subject_forms import SubjectForm


class SubjectList(LoginRequiredMixin, ListView):
    model = Subject
    context_object_name = "subjects"
    template_name = "subject/subject_list.html"
    paginate_by = 20

    def get_queryset(self):
        subjects = Subject.objects.filter(user=self.request.user)
        query = self.request.GET.get("search")
        if query:
            subjects = subjects.filter(title__icontains=query)
        return subjects


class SubjectCreate(LoginRequiredMixin, CreateView):
    model = Subject
    template_name = "subject/subject_form.html"
    form_class = SubjectForm
    success_url = reverse_lazy("subjects")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'O Assunto foi criado com sucesso.')
        return super(SubjectCreate, self).form_valid(form)


class SubjectUpdate(LoginRequiredMixin, UpdateView):
    model = Subject
    template_name = "subject/subject_form.html"
    form_class = SubjectForm
    success_url = reverse_lazy("subjects")

    def form_valid(self, form):
        messages.success(self.request, 'O Assunto foi alterado com sucesso.')
        return super(SubjectUpdate, self).form_valid(form)

    def get_queryset(self):
        base_qs = super(SubjectUpdate, self).get_queryset()
        return base_qs.filter(user=self.request.user)


class SubjectDelete(LoginRequiredMixin, DeleteView):
    model = Subject
    context_object_name = "subject"
    template_name = "subject/subject_confirm_delete.html"
    success_url = reverse_lazy("subjects")

    def get_queryset(self):
        base_qs = super(SubjectDelete, self).get_queryset()
        return base_qs.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'O Assunto foi excluido com sucesso.')
        return super(SubjectDelete, self).form_valid(form)

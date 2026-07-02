import sweetify

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, CreateView, UpdateView

from apps.finance.models.category import Category
from apps.finance.forms.category_forms import CategoryForm


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    context_object_name = "categories"
    template_name = "category/category_list.html"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).select_related("parent")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self.get_queryset()
        context["tree"] = self.build_tree(categories)
        return context

    def build_tree(self, categories, parent=None):
        nodes = []
        for category in categories.filter(parent=parent):
            nodes.append({
                "category": category,
                "children": self.build_tree(categories, category),
            })
        return nodes


class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    template_name = "category/category_form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("category-create")

    def form_valid(self, form):
        form.instance.user = self.request.user
        sweetify.toast(
            self.request,
            "Categoria incluida com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super(CategoryCreate, self).form_valid(form)


class CategoryUpdate(LoginRequiredMixin, UpdateView):
    model = Category
    template_name = "category/category_form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("categories")

    def form_valid(self, form):
        sweetify.toast(
            self.request,
            "Categoria alterada com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super().form_valid(form)

    def get_queryset(self):
        base_qs = super(CategoryUpdate, self).get_queryset()
        return base_qs.filter(user=self.request.user)


class CategoryDelete(LoginRequiredMixin, DeleteView):
    model = Category
    context_object_name = "category"
    template_name = "category/category_confirm_delete.html"
    success_url = reverse_lazy("categories")

    def form_valid(self, form):
        sweetify.toast(
            self.request,
            "Categoria excluida com sucesso",
            icon="error",
            button="OK",
            timer=2000,
        )
        return super(CategoryDelete, self).form_valid(form)

    def get_queryset(self):
        base_qs = super(CategoryDelete, self).get_queryset()
        return base_qs.filter(user=self.request.user)


# def category_list_method(request):
#     categories = Category.objects.values_list(
#         'method', 'name').filter(user=request).order_by('method')

#     categories_method = {}
#     method_ant = 0
#     for method, name in categories:
#         if method != method_ant:
#             categories_method[method] = {}
#             method_ant == method
#         categories_method[method] = {'name': name, }

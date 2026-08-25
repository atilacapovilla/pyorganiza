import sweetify

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, CreateView, UpdateView

from apps.finance.models.category import Category
from apps.finance.forms.category_forms import CategoryForm
from apps.finance.utils.category_ordering import sort_categories


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    context_object_name = "categories"
    template_name = "category/category_list.html"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).select_related("parent")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tree"] = self.build_tree(
            sort_categories(list(self.get_queryset()))
        )
        return context

    @staticmethod
    def build_tree(categories):
        children_map = {}
        for category in categories:
            children_map.setdefault(category.parent_id, []).append(category)

        def recurse(parent_id):
            return [
                {"category": category, "children": recurse(category.id)}
                for category in children_map.get(parent_id, [])
            ]

        return recurse(None)


class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    template_name = "category/category_form.html"
    form_class = CategoryForm
    success_url = reverse_lazy("category-create")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

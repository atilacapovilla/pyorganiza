import sweetify

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm


class MyloginView(LoginView):
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("principal")

    def form_invalid(self, form):
        messages.error(self.request, "Usuário ou Senha inválidos.")
        return self.render_to_response(self.get_context_data(form=form))


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = RegisterForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save()

        if user:
            login(self.request, user)

        return super(RegisterView, self).form_valid(form)


class MyProfile(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

        context = {"user_form": user_form, "profile_form": profile_form}

        return render(request, "users/profile.html", context)

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            sweetify.toast(
                self.request,
                "Seu Perfil foi atualizado com sucesso",
                icon="success",
                button="OK",
                timer=2000,
            )
            return redirect("profile")
        else:
            context = {"user_form": user_form, "profile_form": profile_form}
            messages.error(request, "Erro atualizando seu perfial")
            return render(request, "users/profile.html", context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    return render(request, "home/home.html")


@login_required
def principal(request):
    context = {
        'pagina': 'Home',
    }
    return render(request, "home/principal.html", context)

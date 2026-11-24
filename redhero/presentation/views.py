from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import DonorRegistrationForm, LoginForm


def home(request):
    """Strona startowa dla gości. Zalogowanego od razu kierujemy do jego panelu."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def register(request):
    """Rejestracja dawcy. Po sukcesie od razu logujemy i przekierowujemy."""
    if request.user.is_authenticated:
        messages.info(request, f"Jesteś już zalogowany jako {request.user.email}.")
        return redirect("dashboard")

    form = DonorRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Witaj, {user.first_name}! Konto zostało założone.")
        return redirect("dashboard")

    return render(request, "accounts/register.html", {"form": form})


class DonorLoginView(LoginView):
    """Logowanie e-mailem i hasłem; parametr ?next= wraca na stronę, z której przyszedł gość."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_POST  # wylogowanie tylko formularzem z tokenem CSRF, nie zwykłym linkiem
def logout_view(request):
    logout(request)
    messages.info(request, "Wylogowano. Do zobaczenia!")
    return redirect("login")


@login_required
def dashboard(request):
    """Panel dawcy. Liczniki, odznaki i termin kolejnej donacji dojdą w #40."""
    return render(request, "dashboard.html")

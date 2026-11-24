from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import DonorRegistrationForm


def home(request):
    """Strona startowa. Docelowo: dashboard dawcy po zalogowaniu (#40)."""
    return render(request, "home.html")


def register(request):
    """Rejestracja dawcy. Po sukcesie od razu logujemy i przekierowujemy."""
    if request.user.is_authenticated:
        messages.info(request, f"Jesteś już zalogowany jako {request.user.email}.")
        return redirect("home")

    form = DonorRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Witaj, {user.first_name}! Konto zostało założone.")
        # TODO(#40): przekierować na dashboard dawcy, gdy powstanie
        return redirect("home")

    return render(request, "accounts/register.html", {"form": form})

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from redhero.services import donations

from .forms import DonationForm, DonorRegistrationForm, LoginForm

DONATIONS_PER_PAGE = 20


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


@login_required
def donation_list(request):
    """Dziennik donacji zalogowanego dawcy, od najnowszej, po 20 na stronę."""
    page = Paginator(donations.donations_for(request.user), DONATIONS_PER_PAGE).get_page(
        request.GET.get("strona")
    )
    return render(request, "donations/list.html", {"page": page})


@login_required
def donation_create(request):
    """Formularz „Zarejestruj donację” dla zalogowanego dawcy."""
    form = DonationForm(request.POST or None, initial={"donation_date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        donation = form.save(commit=False)
        # ostrzeżenie liczymy przed zapisem, żeby nie porównywać donacji z nią samą
        warning = donations.interval_warning(
            request.user, donation.donation_type, donation.donation_date
        )
        donations.create_donation(request.user, donation)
        messages.success(request, f"Zapisano donację: {donation}.")
        if warning:
            messages.warning(request, warning)
        return redirect("donation_list")

    return _render_donation_form(request, form, title="Zarejestruj donację")


@login_required
def donation_update(request, pk):
    """Edycja donacji. Cudza donacja daje 404 (serwis filtruje po dawcy)."""
    donation = donations.get_donation_for(request.user, pk)
    form = DonationForm(request.POST or None, instance=donation)
    if request.method == "POST" and form.is_valid():
        donation = form.save(commit=False)
        warning = donations.interval_warning(
            request.user, donation.donation_type, donation.donation_date, exclude_pk=donation.pk
        )
        donations.update_donation(request.user, donation)
        messages.success(request, f"Zapisano zmiany: {donation}.")
        if warning:
            messages.warning(request, warning)
        return redirect("donation_list")

    return _render_donation_form(request, form, title="Edytuj donację")


@login_required
def donation_delete(request, pk):
    """GET pokazuje stronę z potwierdzeniem, POST usuwa donację."""
    donation = donations.get_donation_for(request.user, pk)
    if request.method == "POST":
        donations.delete_donation(request.user, donation)
        messages.success(request, f"Usunięto donację: {donation}.")
        return redirect("donation_list")
    return render(request, "donations/confirm_delete.html", {"donation": donation})


def _render_donation_form(request, form, *, title):
    return render(
        request,
        "donations/form.html",
        {"form": form, "title": title, "default_volumes": _default_volumes()},
    )


def _default_volumes():
    """Typowa objętość każdego rodzaju: skrypt w formularzu podpowiada ją po wyborze rodzaju."""
    return {
        str(t.pk): {"default": t.default_volume_ml, "min": t.min_volume_ml, "max": t.max_volume_ml}
        for t in donations.active_donation_types()
    }

"""Logowanie i wylogowanie (#43): backend e-mailowy i przepływ HTTP."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from redhero.services.auth import EmailBackend

User = get_user_model()
PASSWORD = "Krwiodawca-2026"


@pytest.fixture
def donor(db):
    return User.objects.create_user(email="Jan.Nowak@example.com", password=PASSWORD)


def post_login(client, email, password=PASSWORD, **extra):
    return client.post(reverse("login"), {"username": email, "password": password, **extra})


# --- backend: testy jednostkowe ---


@pytest.mark.parametrize(
    "email", ["Jan.Nowak@example.com", "jan.nowak@EXAMPLE.com", " jan.nowak@example.com "]
)
def test_backend_finds_user_regardless_of_email_case(donor, email):
    assert EmailBackend().authenticate(None, username=email, password=PASSWORD) == donor


def test_backend_rejects_wrong_password(donor):
    assert EmailBackend().authenticate(None, username=donor.email, password="zle") is None


def test_backend_rejects_unknown_email(db):
    assert EmailBackend().authenticate(None, username="nikt@example.com", password="x") is None


def test_backend_rejects_inactive_user(donor):
    donor.is_active = False
    donor.save()

    assert EmailBackend().authenticate(None, username=donor.email, password=PASSWORD) is None


def test_backend_requires_credentials(db):
    assert EmailBackend().authenticate(None, username=None, password=None) is None


# --- przepływ HTTP: testy integracyjne ---


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert "Zaloguj się" in response.content.decode()


def test_successful_login_redirects_to_dashboard(client, donor):
    response = post_login(client, "jan.nowak@example.com")

    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    assert int(client.session["_auth_user_id"]) == donor.pk


def test_login_returns_to_requested_page(client, donor):
    response = post_login(client, donor.email, next=reverse("dashboard"))

    assert response.url == reverse("dashboard")


def test_login_ignores_external_next_url(client, donor):
    # ochrona przed open redirect: nie przekierowujemy na obce strony
    response = post_login(client, donor.email, next="https://zla-strona.example")

    assert response.url == reverse("dashboard")


@pytest.mark.parametrize(
    ("email", "password"),
    [("Jan.Nowak@example.com", "zle-haslo"), ("nie-ma-takiego@example.com", PASSWORD)],
)
def test_failed_login_shows_same_generic_message(client, donor, email, password):
    response = post_login(client, email, password)

    assert response.status_code == 200
    content = response.content.decode()
    # ten sam komunikat dla złego hasła i nieistniejącego konta
    assert "Nieprawidłowy e-mail lub hasło." in content
    assert "_auth_user_id" not in client.session


def test_anonymous_user_is_redirected_to_login(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={reverse('dashboard')}"


def test_logged_in_user_sees_dashboard_and_logout_button(client, donor):
    client.force_login(donor)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "Wyloguj" in response.content.decode()


def test_logged_in_user_is_redirected_from_login_and_home(client, donor):
    client.force_login(donor)

    assert client.get(reverse("login")).url == reverse("dashboard")
    assert client.get(reverse("home")).url == reverse("dashboard")


def test_logout_requires_post(client, donor):
    client.force_login(donor)

    response = client.get(reverse("logout"))

    assert response.status_code == 405
    assert "_auth_user_id" in client.session  # dalej zalogowany


def test_after_logout_donor_pages_are_not_accessible(client, donor):
    client.force_login(donor)

    response = client.post(reverse("logout"), follow=True)

    assert "Wylogowano" in response.content.decode()
    assert "_auth_user_id" not in client.session
    assert client.get(reverse("dashboard")).url.startswith(reverse("login"))


def test_admin_panel_login_still_works_with_email_backend(client, db):
    User.objects.create_superuser(email="admin@example.com", password=PASSWORD)

    response = client.post(
        reverse("admin:login"),
        {"username": "ADMIN@example.com", "password": PASSWORD, "next": reverse("admin:index")},
    )

    assert response.status_code == 302
    assert response.url == reverse("admin:index")

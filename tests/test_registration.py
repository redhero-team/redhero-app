"""Rejestracja dawcy (#37): reguły w serwisie (testy jednostkowe) i cały przepływ HTTP."""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from redhero.services import accounts

User = get_user_model()

VALID_DATA = {
    "first_name": "Anna",
    "last_name": "Kowalska",
    "email": "anna@example.com",
    "date_of_birth": "1995-04-12",
    "sex": "K",
    "password1": "Krwiodawczyni-2026",
    "password2": "Krwiodawczyni-2026",
}


def post_register(client, **overrides):
    return client.post(reverse("register"), {**VALID_DATA, **overrides})


# --- serwis: testy jednostkowe ---


@pytest.mark.parametrize(
    ("born", "today", "expected"),
    [
        (date(2000, 5, 10), date(2018, 5, 10), 18),  # w dniu urodzin
        (date(2000, 5, 10), date(2018, 5, 9), 17),  # dzień przed
        (date(2000, 2, 29), date(2019, 2, 28), 18),  # urodzeni 29 lutego
    ],
)
def test_age_on(born, today, expected):
    assert accounts.age_on(born, today) == expected


def test_adult_birth_date_is_accepted():
    accounts.validate_donor_birth_date(date(2000, 5, 10), today=date(2018, 5, 10))


@pytest.mark.parametrize(
    ("born", "message"),
    [
        (date(2030, 1, 1), "przyszłości"),
        (date(2010, 1, 1), "18 lat"),
        (date(1890, 1, 1), "rok urodzenia"),
    ],
)
def test_invalid_birth_dates_are_rejected(born, message):
    with pytest.raises(ValidationError) as error:
        accounts.validate_donor_birth_date(born, today=date(2026, 11, 24))

    assert message in error.value.messages[0]


@pytest.mark.django_db
def test_email_is_taken_ignores_case():
    User.objects.create_user(email="anna@example.com", password="x")

    assert accounts.email_is_taken("ANNA@example.com")
    assert not accounts.email_is_taken("inna@example.com")


# --- przepływ HTTP: testy integracyjne ---


@pytest.mark.django_db
def test_registration_page_renders(client):
    response = client.get(reverse("register"))

    assert response.status_code == 200
    assert "Zarejestruj się jako dawca" in response.content.decode()


@pytest.mark.django_db
def test_successful_registration_creates_user_and_logs_in(client):
    response = post_register(client)

    assert response.status_code == 302
    user = User.objects.get(email="anna@example.com")
    assert user.first_name == "Anna"
    assert user.date_of_birth == date(1995, 4, 12)
    assert user.sex == "K"
    assert user.password.startswith("argon2")  # hash, nie jawne hasło (W10)
    assert not user.is_staff
    # użytkownik jest od razu zalogowany
    assert int(client.session["_auth_user_id"]) == user.pk


@pytest.mark.django_db
def test_duplicate_email_is_rejected(client):
    User.objects.create_user(email="anna@example.com", password="x")

    response = post_register(client, email="Anna@Example.com")

    assert response.status_code == 200
    assert "email" in response.context["form"].errors
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"password2": "Inne-haslo-2026"}, "password2"),
        ({"password1": "12345678", "password2": "12345678"}, "password1"),
        ({"password1": "krótkie", "password2": "krótkie"}, "password1"),
        ({"date_of_birth": str(timezone.localdate() + timedelta(days=1))}, "date_of_birth"),
        ({"sex": ""}, "sex"),
        ({"first_name": ""}, "first_name"),
        ({"email": "to-nie-jest-email"}, "email"),
    ],
)
def test_invalid_data_shows_error_at_field(client, overrides, field):
    response = post_register(client, **overrides)

    assert response.status_code == 200
    form = response.context["form"]
    assert field in form.errors
    # pole z błędem jest podświetlone, a komunikat jest w HTML-u
    assert "is-invalid" in form.fields[field].widget.attrs["class"]
    assert form.errors[field][0] in response.content.decode()
    assert not User.objects.filter(email=VALID_DATA["email"]).exists()


@pytest.mark.django_db
def test_logged_in_user_is_redirected_from_registration(client):
    user = User.objects.create_user(email="jan@example.com", password="x")
    client.force_login(user)

    response = client.get(reverse("register"), follow=True)

    assert response.redirect_chain[-1] == (reverse("home"), 302)
    assert "Jesteś już zalogowany jako jan@example.com" in response.content.decode()

"""Dodawanie donacji (#44): serwis (testy jednostkowe) i formularz przez HTTP."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from redhero.data.models import Donation, DonationType, Facility
from redhero.services import donations

User = get_user_model()


@pytest.fixture
def donor(db):
    return User.objects.create_user(email="dawca@example.com", password="Krwiodawca-2026")


@pytest.fixture
def other_donor(db):
    return User.objects.create_user(email="inny@example.com", password="Krwiodawca-2026")


@pytest.fixture
def whole_blood(db):
    return DonationType.objects.get(code="whole_blood")


@pytest.fixture
def facility(db):
    return Facility.objects.filter(is_active=True).first()


@pytest.fixture
def logged_client(client, donor):
    client.force_login(donor)
    return client


def form_data(dtype, place, **overrides):
    data = {
        "donation_type": dtype.pk,
        "donation_date": timezone.localdate().isoformat(),
        "volume_ml": 450,
        "facility": place.pk,
        "location_text": "",
        "notes": "Bez problemów",
    }
    data.update(overrides)
    return data


def save_donation(user, donation_type, days_ago):
    return Donation.objects.create(
        user=user,
        donation_type=donation_type,
        donation_date=timezone.localdate() - timedelta(days=days_ago),
        volume_ml=450,
        location_text="Punkt mobilny",
    )


# --- serwis: testy jednostkowe ---


def test_create_donation_sets_owner(donor, other_donor, whole_blood, facility):
    donation = Donation(
        user=other_donor,  # nawet jeśli ktoś podstawi innego właściciela...
        donation_type=whole_blood,
        donation_date=timezone.localdate(),
        volume_ml=450,
        facility=facility,
    )

    donations.create_donation(donor, donation)

    assert donation.user == donor  # ...serwis ustawia zalogowanego dawcę


def test_no_warning_for_first_donation(donor, whole_blood):
    assert donations.interval_warning(donor, whole_blood, timezone.localdate()) is None


def test_warning_when_interval_too_short(donor, whole_blood):
    save_donation(donor, whole_blood, days_ago=30)  # minimum dla krwi pełnej to 56 dni

    warning = donations.interval_warning(donor, whole_blood, timezone.localdate())

    assert "minęło 30 dni" in warning
    assert "56 dni" in warning


def test_no_warning_when_interval_long_enough(donor, whole_blood):
    save_donation(donor, whole_blood, days_ago=whole_blood.min_interval_days)

    assert donations.interval_warning(donor, whole_blood, timezone.localdate()) is None


def test_other_users_donations_do_not_trigger_warning(donor, other_donor, whole_blood):
    save_donation(other_donor, whole_blood, days_ago=1)

    assert donations.interval_warning(donor, whole_blood, timezone.localdate()) is None


def test_only_active_types_and_facilities_are_offered(db):
    DonationType.objects.filter(code="white_cells").update(is_active=False)
    Facility.objects.create(name="Zamknięta", city="X", is_active=False)

    assert not donations.active_donation_types().filter(code="white_cells").exists()
    assert not donations.active_facilities().filter(name="Zamknięta").exists()


# --- przepływ HTTP: testy integracyjne ---


@pytest.mark.django_db
def test_anonymous_user_cannot_add_donation(client):
    response = client.get(reverse("donation_create"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_form_renders_with_today_as_default(logged_client):
    response = logged_client.get(reverse("donation_create"))

    assert response.status_code == 200
    assert timezone.localdate().isoformat() in response.content.decode()
    assert 'id="default-volumes"' in response.content.decode()


def test_valid_donation_is_saved_for_logged_in_user(logged_client, donor, whole_blood, facility):
    response = logged_client.post(
        reverse("donation_create"), form_data(whole_blood, facility), follow=True
    )

    donation = Donation.objects.get()
    assert donation.user == donor
    assert donation.facility == facility
    assert donation.notes == "Bez problemów"
    assert "Zapisano donację" in response.content.decode()


def test_cannot_add_donation_for_another_user(
    logged_client, donor, other_donor, whole_blood, facility
):
    # pole `user` nie jest częścią formularza, więc jest ignorowane
    data = form_data(whole_blood, facility, user=other_donor.pk)

    logged_client.post(reverse("donation_create"), data)

    assert Donation.objects.get().user == donor
    assert not other_donor.donations.exists()


def test_location_text_instead_of_facility(logged_client, whole_blood, facility):
    data = form_data(whole_blood, facility, facility="", location_text="Akcja w szkole")

    logged_client.post(reverse("donation_create"), data)

    assert Donation.objects.get().place == "Akcja w szkole"


def test_too_short_interval_saves_with_warning(logged_client, donor, whole_blood, facility):
    save_donation(donor, whole_blood, days_ago=10)

    response = logged_client.post(
        reverse("donation_create"), form_data(whole_blood, facility), follow=True
    )

    assert donor.donations.count() == 2  # zapisane mimo ostrzeżenia
    assert "minęło 10 dni" in response.content.decode()


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        (
            {"donation_date": (timezone.localdate() + timedelta(days=1)).isoformat()},
            "donation_date",
        ),
        ({"volume_ml": 0}, "volume_ml"),
        ({"volume_ml": -100}, "volume_ml"),
        ({"volume_ml": 1000}, "volume_ml"),
        ({"facility": "", "location_text": ""}, "facility"),
        ({"donation_type": ""}, "donation_type"),
    ],
)
def test_invalid_donation_shows_error_at_field(
    logged_client, whole_blood, facility, overrides, field
):
    response = logged_client.post(
        reverse("donation_create"), form_data(whole_blood, facility, **overrides)
    )

    assert response.status_code == 200
    form = response.context["form"]
    assert field in form.errors
    # błąd tylko przy polu, bez duplikatu nad formularzem
    assert not form.non_field_errors()
    assert not Donation.objects.exists()

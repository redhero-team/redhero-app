"""Dziennik donacji, edycja i usuwanie (#45). Razem z #44 daje pełny CRUD (W3)."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from redhero.data.models import Donation, DonationType, Facility
from redhero.presentation.views import DONATIONS_PER_PAGE
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
def logged_client(client, donor):
    client.force_login(donor)
    return client


def add(user, dtype, days_ago=0, place="Punkt mobilny", **extra):
    return Donation.objects.create(
        user=user,
        donation_type=dtype,
        donation_date=timezone.localdate() - timedelta(days=days_ago),
        volume_ml=450,
        location_text=place,
        **extra,
    )


# --- serwis: testy jednostkowe ---


def test_donations_for_returns_only_own_newest_first(donor, other_donor, whole_blood):
    old = add(donor, whole_blood, days_ago=100)
    new = add(donor, whole_blood, days_ago=1)
    add(other_donor, whole_blood)

    assert list(donations.donations_for(donor)) == [new, old]


def test_update_and_delete_refuse_foreign_donation(donor, other_donor, whole_blood):
    foreign = add(other_donor, whole_blood)

    with pytest.raises(PermissionError):
        donations.update_donation(donor, foreign)
    with pytest.raises(PermissionError):
        donations.delete_donation(donor, foreign)
    assert Donation.objects.filter(pk=foreign.pk).exists()


def test_interval_warning_ignores_edited_donation_itself(donor, whole_blood):
    donation = add(donor, whole_blood)

    warning = donations.interval_warning(
        donor, whole_blood, donation.donation_date, exclude_pk=donation.pk
    )

    assert warning is None


def test_inactive_type_and_facility_kept_when_editing(donor, whole_blood):
    closed = Facility.objects.create(name="Zamknięta", city="X", is_active=False)
    whole_blood.is_active = False
    whole_blood.save()

    assert closed in donations.active_facilities(include_pk=closed.pk)
    assert whole_blood in donations.active_donation_types(include_pk=whole_blood.pk)
    assert closed not in donations.active_facilities()


# --- dziennik (Read) ---


def test_journal_requires_login(client, db):
    response = client.get(reverse("donation_list"))

    assert response.url.startswith(reverse("login"))


def test_empty_journal_shows_link_to_first_donation(logged_client):
    response = logged_client.get(reverse("donation_list"))

    content = response.content.decode()
    assert "Nie masz jeszcze żadnych donacji" in content
    assert reverse("donation_create") in content


def test_journal_shows_own_donations_newest_first(logged_client, donor, whole_blood):
    add(donor, whole_blood, days_ago=100, place="Stara akcja")
    add(donor, whole_blood, days_ago=1, place="Nowa akcja")

    content = logged_client.get(reverse("donation_list")).content.decode()

    assert content.index("Nowa akcja") < content.index("Stara akcja")
    assert "450 ml" in content
    assert "Krew pełna" in content


def test_journal_does_not_show_other_donors_donations(
    logged_client, donor, other_donor, whole_blood
):
    add(donor, whole_blood, place="Moja donacja")
    add(other_donor, whole_blood, place="Cudza donacja")

    content = logged_client.get(reverse("donation_list")).content.decode()

    assert "Moja donacja" in content
    assert "Cudza donacja" not in content


def test_journal_is_paginated(logged_client, donor, whole_blood):
    for day in range(DONATIONS_PER_PAGE + 1):
        add(donor, whole_blood, days_ago=day)

    first = logged_client.get(reverse("donation_list"))
    second = logged_client.get(reverse("donation_list"), {"strona": 2})

    assert len(first.context["page"]) == DONATIONS_PER_PAGE
    assert len(second.context["page"]) == 1


# --- edycja (Update) ---


def test_edit_form_is_prefilled(logged_client, donor, whole_blood):
    donation = add(donor, whole_blood, notes="Pierwsza")

    response = logged_client.get(reverse("donation_update", args=[donation.pk]))

    assert response.status_code == 200
    assert "Edytuj donację" in response.content.decode()
    assert response.context["form"].instance == donation


def test_edit_saves_changes(logged_client, donor, whole_blood):
    donation = add(donor, whole_blood)
    data = {
        "donation_type": whole_blood.pk,
        "donation_date": donation.donation_date.isoformat(),
        "volume_ml": 470,
        "facility": "",
        "location_text": "Poprawione miejsce",
        "notes": "Zmienione",
    }

    response = logged_client.post(reverse("donation_update", args=[donation.pk]), data)

    assert response.url == reverse("donation_list")
    donation.refresh_from_db()
    assert donation.volume_ml == 470
    assert donation.place == "Poprawione miejsce"
    assert donation.user == donor


def test_edit_with_invalid_data_shows_error(logged_client, donor, whole_blood):
    donation = add(donor, whole_blood)
    data = {"donation_type": whole_blood.pk, "donation_date": "", "volume_ml": 450}

    response = logged_client.post(reverse("donation_update", args=[donation.pk]), data)

    assert response.status_code == 200
    assert "donation_date" in response.context["form"].errors


def test_cannot_edit_other_donors_donation(logged_client, other_donor, whole_blood):
    foreign = add(other_donor, whole_blood)

    assert logged_client.get(reverse("donation_update", args=[foreign.pk])).status_code == 404
    response = logged_client.post(
        reverse("donation_update", args=[foreign.pk]),
        {"donation_type": whole_blood.pk, "donation_date": "2026-01-01", "volume_ml": 450},
    )
    assert response.status_code == 404


# --- usuwanie (Delete) ---


def test_delete_asks_for_confirmation_first(logged_client, donor, whole_blood):
    donation = add(donor, whole_blood)

    response = logged_client.get(reverse("donation_delete", args=[donation.pk]))

    assert response.status_code == 200
    assert "Usunąć donację?" in response.content.decode()
    assert Donation.objects.filter(pk=donation.pk).exists()  # GET niczego nie usuwa


def test_delete_removes_donation(logged_client, donor, whole_blood):
    donation = add(donor, whole_blood)

    response = logged_client.post(reverse("donation_delete", args=[donation.pk]), follow=True)

    assert not Donation.objects.filter(pk=donation.pk).exists()
    assert "Usunięto donację" in response.content.decode()


def test_cannot_delete_other_donors_donation(logged_client, other_donor, whole_blood):
    foreign = add(other_donor, whole_blood)

    response = logged_client.post(reverse("donation_delete", args=[foreign.pk]))

    assert response.status_code == 404
    assert Donation.objects.filter(pk=foreign.pk).exists()

"""Testy modeli donacji: relacje, walidacja i ograniczenia w bazie (#36)."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from redhero.data.models import Donation, DonationType, Facility

User = get_user_model()


@pytest.fixture
def donor(db):
    return User.objects.create_user(email="dawca@example.com", password="Bezpieczne-haslo-123")


@pytest.fixture
def whole_blood(db):
    # rodzaj z danych startowych (migracja 0003)
    return DonationType.objects.get(code="whole_blood")


@pytest.fixture
def facility(db):
    return Facility.objects.create(name="RCKiK", city="Testowo")


def make_donation(donor, donation_type, **overrides):
    fields = {
        "user": donor,
        "donation_type": donation_type,
        "donation_date": timezone.localdate(),
        "volume_ml": 450,
        "location_text": "Mobilny punkt poboru",
    }
    fields.update(overrides)
    return Donation(**fields)


# --- dane startowe ---


@pytest.mark.django_db
def test_seed_data_contains_donation_types_and_facilities():
    codes = set(DonationType.objects.values_list("code", flat=True))

    assert {"whole_blood", "plasma", "platelets"} <= codes
    assert Facility.objects.exists()


# --- relacje ---


def test_donation_belongs_to_user(donor, whole_blood, facility):
    donation = make_donation(donor, whole_blood, facility=facility, location_text="")
    donation.full_clean()
    donation.save()

    assert list(donor.donations.all()) == [donation]
    assert donation.place == "RCKiK (Testowo)"
    assert str(donation).startswith("Krew pełna – ")


def test_deleting_user_deletes_their_donations(donor, whole_blood):
    make_donation(donor, whole_blood).save()

    donor.delete()

    assert not Donation.objects.exists()


def test_cannot_delete_donation_type_in_use(donor, whole_blood):
    make_donation(donor, whole_blood).save()

    with pytest.raises(ProtectedError):
        whole_blood.delete()


def test_donations_are_ordered_newest_first(donor, whole_blood):
    today = timezone.localdate()
    older = make_donation(donor, whole_blood, donation_date=today - timedelta(days=60))
    newer = make_donation(donor, whole_blood, donation_date=today)
    older.save()
    newer.save()

    assert list(Donation.objects.all()) == [newer, older]


# --- walidacja (clean) ---


def test_location_text_is_enough_without_facility(donor, whole_blood):
    make_donation(donor, whole_blood).full_clean()  # nie rzuca wyjątku


def test_future_date_is_rejected(donor, whole_blood):
    tomorrow = timezone.localdate() + timedelta(days=1)

    with pytest.raises(ValidationError) as error:
        make_donation(donor, whole_blood, donation_date=tomorrow).full_clean()

    assert "donation_date" in error.value.message_dict


@pytest.mark.parametrize("volume", [399, 501])
def test_volume_outside_type_range_is_rejected(donor, whole_blood, volume):
    with pytest.raises(ValidationError) as error:
        make_donation(donor, whole_blood, volume_ml=volume).full_clean()

    assert "volume_ml" in error.value.message_dict


def test_facility_or_location_is_required(donor, whole_blood):
    with pytest.raises(ValidationError) as error:
        make_donation(donor, whole_blood, location_text="   ").full_clean()

    assert "facility" in error.value.message_dict


# --- ograniczenia w bazie (działają nawet z pominięciem formularza) ---


def test_database_rejects_donation_without_place(donor, whole_blood):
    with pytest.raises(IntegrityError):
        make_donation(donor, whole_blood, location_text="").save()


def test_database_rejects_inconsistent_donation_type_volumes(db):
    with pytest.raises(IntegrityError):
        DonationType.objects.create(
            code="zly",
            name="Zły",
            default_volume_ml=1000,
            min_volume_ml=100,
            max_volume_ml=500,
            whole_blood_equivalent_ml=100,
            min_interval_days=1,
        )


# --- panel admina (test integracyjny) ---


@pytest.mark.parametrize("model", ["donation", "donationtype", "facility"])
def test_admin_pages_render(admin_client, model):
    response = admin_client.get(reverse(f"admin:redhero_{model}_changelist"))

    assert response.status_code == 200


def test_admin_can_open_donation_form(admin_client):
    response = admin_client.get(reverse("admin:redhero_donation_add"))

    assert response.status_code == 200

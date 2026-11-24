"""Logika donacji: zapisywanie i ostrzeżenia o zbyt krótkim odstępie.

Widok nie zapisuje donacji sam. Wywołuje te funkcje, a one korzystają z modeli.
"""

from datetime import date

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from redhero.data.models import Donation, DonationType, Facility


def active_donation_types(include_pk=None):
    """Aktywne rodzaje; `include_pk` dokłada rodzaj edytowanej donacji, nawet gdy jest wyłączony."""
    return DonationType.objects.filter(Q(is_active=True) | Q(pk=include_pk))


def active_facilities(include_pk=None):
    """Aktywne placówki; `include_pk` działa jak w `active_donation_types`."""
    return Facility.objects.filter(Q(is_active=True) | Q(pk=include_pk))


def donations_for(user):
    """Donacje dawcy od najnowszej. Tylko jego, nigdy cudze."""
    return (
        Donation.objects.filter(user=user)
        .select_related("donation_type", "facility")
        .order_by("-donation_date", "-created_at")
    )


def get_donation_for(user, pk) -> Donation:
    """Donacja o danym id, ale tylko jeśli należy do dawcy.

    Cudza donacja daje 404, a nie 403, żeby nie zdradzać, że w ogóle istnieje.
    """
    return get_object_or_404(donations_for(user), pk=pk)


@transaction.atomic
def create_donation(user, donation: Donation) -> Donation:
    """Zapisuje donację na koncie `user`.

    Właściciela ustawiamy tutaj, a nie w formularzu, więc dawca nie może
    dodać donacji na cudze konto, nawet podmieniając dane w żądaniu.
    """
    donation.user = user
    donation.full_clean()
    donation.save()
    return donation


@transaction.atomic
def update_donation(user, donation: Donation) -> Donation:
    """Zapisuje zmiany w donacji dawcy. Sprawdza, czy donacja na pewno jest jego."""
    if donation.user_id != user.pk:
        raise PermissionError("Dawca może zmieniać tylko swoje donacje.")
    donation.full_clean()
    donation.save()
    return donation


@transaction.atomic
def delete_donation(user, donation: Donation) -> None:
    if donation.user_id != user.pk:
        raise PermissionError("Dawca może usuwać tylko swoje donacje.")
    donation.delete()


def interval_warning(
    user, donation_type: DonationType, donation_date: date, exclude_pk=None
) -> str | None:
    """Ostrzeżenie, gdy od poprzedniej donacji tego rodzaju minęło mniej dni niż minimum.

    Nie blokujemy zapisu: dawca rejestruje donację, która już się odbyła,
    więc tylko informujemy (model-danych, sekcja 6).
    Odstępy między różnymi rodzajami dojdą razem z kalkulatorem terminów.
    Przy edycji `exclude_pk` pomija edytowaną donację, żeby nie porównywać jej z nią samą.
    """
    previous = (
        Donation.objects.filter(
            user=user, donation_type=donation_type, donation_date__lte=donation_date
        )
        .exclude(pk=exclude_pk)
        .order_by("-donation_date", "-created_at")
        .first()
    )
    if previous is None:
        return None

    days = (donation_date - previous.donation_date).days
    if days < donation_type.min_interval_days:
        return (
            f"Uwaga: od poprzedniej donacji ({donation_type.name}, "
            f"{previous.donation_date:%d.%m.%Y}) minęło {days} dni, "
            f"a zalecany odstęp to {donation_type.min_interval_days} dni. "
            "Sprawdź, czy data jest poprawna."
        )
    return None

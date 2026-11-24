"""Logika donacji: zapisywanie i ostrzeżenia o zbyt krótkim odstępie.

Widok nie zapisuje donacji sam. Wywołuje te funkcje, a one korzystają z modeli.
"""

from datetime import date

from django.db import transaction

from redhero.data.models import Donation, DonationType, Facility


def active_donation_types():
    return DonationType.objects.filter(is_active=True)


def active_facilities():
    return Facility.objects.filter(is_active=True)


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


def interval_warning(user, donation_type: DonationType, donation_date: date) -> str | None:
    """Ostrzeżenie, gdy od poprzedniej donacji tego rodzaju minęło mniej dni niż minimum.

    Nie blokujemy zapisu: dawca rejestruje donację, która już się odbyła,
    więc tylko informujemy (model-danych, sekcja 6).
    Odstępy między różnymi rodzajami dojdą razem z kalkulatorem terminów.
    """
    previous = (
        Donation.objects.filter(
            user=user, donation_type=donation_type, donation_date__lte=donation_date
        )
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

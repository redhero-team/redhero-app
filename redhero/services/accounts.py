"""Logika kont użytkowników: rejestracja dawcy i reguły z nią związane."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

# Kandydat na dawcę krwi w Polsce musi mieć ukończone 18 lat.
MIN_DONOR_AGE = 18
# Zabezpieczenie przed literówką w roku (np. 1094 zamiast 1994).
MAX_REASONABLE_AGE = 120


def age_on(date_of_birth: date, today: date) -> int:
    """Liczba ukończonych lat w dniu `today`."""
    had_birthday = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    return today.year - date_of_birth.year - (0 if had_birthday else 1)


def validate_donor_birth_date(date_of_birth: date, today: date | None = None) -> None:
    """Rzuca ValidationError, jeśli data urodzenia nie pozwala zarejestrować dawcy."""
    today = today or timezone.localdate()

    if date_of_birth > today:
        raise ValidationError("Data urodzenia nie może być z przyszłości.")

    age = age_on(date_of_birth, today)
    if age < MIN_DONOR_AGE:
        raise ValidationError(f"Krew mogą oddawać osoby, które ukończyły {MIN_DONOR_AGE} lat.")
    if age > MAX_REASONABLE_AGE:
        raise ValidationError("Sprawdź rok urodzenia.")


def email_is_taken(email: str) -> bool:
    """Czy istnieje już konto z tym adresem (bez względu na wielkość liter)."""
    return get_user_model().objects.filter(email__iexact=email.strip()).exists()


@transaction.atomic
def register_donor(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    date_of_birth: date,
    sex: str,
):
    """Tworzy konto dawcy. Dane muszą być już zwalidowane przez formularz."""
    return get_user_model().objects.create_user(
        email=email.strip(),
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        date_of_birth=date_of_birth,
        sex=sex,
    )

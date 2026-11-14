"""Testy własnego modelu użytkownika (logowanie e-mailem, hash hasła)."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_uses_email_and_hashes_password():
    user = User.objects.create_user(email="Dawca@Example.COM", password="Bezpieczne-haslo-123")

    # domena e-maila jest normalizowana do małych liter
    assert user.email == "Dawca@example.com"
    # hasło nie jest przechowywane jawnie, tylko jako hash Argon2 (W10)
    assert user.password.startswith("argon2")
    assert user.check_password("Bezpieczne-haslo-123")
    assert not user.is_staff


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="cokolwiek")


@pytest.mark.django_db
def test_create_superuser_is_staff():
    admin = User.objects.create_superuser(email="admin@example.com", password="Admin-haslo-123")

    assert admin.is_staff
    assert admin.is_superuser

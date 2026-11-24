"""Uwierzytelnianie: logowanie e-mailem bez rozróżniania wielkości liter."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Jak domyślny backend Django, ale szuka konta po e-mailu niezależnie od wielkości liter.

    Sprawdzanie hasła, blokada nieaktywnych kont i uprawnienia zostają z `ModelBackend`.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get(get_user_model().USERNAME_FIELD)
        if not email or password is None:
            return None

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            # Liczymy hash także dla nieistniejącego konta, żeby czas odpowiedzi
            # nie zdradzał, czy e-mail jest zarejestrowany.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Tworzy użytkowników identyfikowanych e-mailem zamiast loginu."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Adres e-mail jest wymagany.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # zapisuje hash (Argon2), nigdy jawne hasło
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superużytkownik musi mieć is_staff=True i is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Użytkownik aplikacji (dawca lub administrator).

    Pola z formularza rejestracji (data urodzenia, płeć) dodamy w Sprincie 1
    razem z historyjką o rejestracji. Dodanie pól to zwykła migracja,
    natomiast podmiana całego modelu użytkownika byłaby bardzo kosztowna.
    """

    username = None
    email = models.EmailField("adres e-mail", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "użytkownik"
        verbose_name_plural = "użytkownicy"

    def __str__(self):
        return self.email

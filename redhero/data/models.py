from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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
    """Użytkownik aplikacji (dawca lub administrator)."""

    class Sex(models.TextChoices):
        # progi odznak HDK i limity donacji różnią się dla kobiet i mężczyzn
        FEMALE = "K", "kobieta"
        MALE = "M", "mężczyzna"

    username = None
    email = models.EmailField("adres e-mail", unique=True)
    # W bazie pola są opcjonalne, bo konto admina zakładane z konsoli ich nie ma.
    # Dla dawcy są wymagane w formularzu rejestracji.
    date_of_birth = models.DateField("data urodzenia", null=True, blank=True)
    sex = models.CharField("płeć", max_length=1, choices=Sex.choices, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "użytkownik"
        verbose_name_plural = "użytkownicy"

    def __str__(self):
        return self.email


class TimeStampedModel(models.Model):
    """Dodaje daty utworzenia i ostatniej zmiany do tabel z danymi użytkownika."""

    created_at = models.DateTimeField("utworzono", auto_now_add=True)
    updated_at = models.DateTimeField("zmieniono", auto_now=True)

    class Meta:
        abstract = True


class DonationType(models.Model):
    """Słownik rodzajów donacji (krew pełna, osocze, płytki...).

    Trzymamy tu zasady medyczne zamiast wpisywać je w kod: gdy któraś wartość
    okaże się inna, admin poprawia ją w panelu bez nowego wdrożenia.
    Wartości startowe są w migracji 0003 i czekają na weryfikację (#42).
    """

    code = models.SlugField("kod", unique=True, help_text="Stały identyfikator używany w kodzie.")
    name = models.CharField("nazwa", max_length=100)
    default_volume_ml = models.PositiveIntegerField("typowa objętość (ml)")
    min_volume_ml = models.PositiveIntegerField("minimalna objętość (ml)")
    max_volume_ml = models.PositiveIntegerField("maksymalna objętość (ml)")
    whole_blood_equivalent_ml = models.PositiveIntegerField(
        "ekwiwalent krwi pełnej (ml)",
        help_text="Ile ml krwi pełnej zalicza się za jedną donację tego rodzaju.",
    )
    min_interval_days = models.PositiveIntegerField(
        "minimalny odstęp (dni)",
        help_text="Najkrótszy odstęp do kolejnej donacji tego samego rodzaju.",
    )
    is_active = models.BooleanField("aktywny", default=True)

    class Meta:
        verbose_name = "rodzaj donacji"
        verbose_name_plural = "rodzaje donacji"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(min_volume_ml__lte=models.F("default_volume_ml"))
                & Q(default_volume_ml__lte=models.F("max_volume_ml")),
                name="donation_type_volume_range",
                violation_error_message="Typowa objętość musi być między minimum a maksimum.",
            ),
        ]

    def __str__(self):
        return self.name


class Facility(models.Model):
    """Placówka, w której oddaje się krew (słownik zarządzany przez admina)."""

    name = models.CharField("nazwa", max_length=200)
    city = models.CharField("miasto", max_length=100)
    address = models.CharField("adres", max_length=200, blank=True)
    is_active = models.BooleanField(
        "aktywna",
        default=True,
        help_text="Nieaktywna placówka znika z formularza, ale zostaje w historii donacji.",
    )

    class Meta:
        verbose_name = "placówka"
        verbose_name_plural = "placówki"
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Donation(TimeStampedModel):
    """Pojedyncza donacja dawcy: główna encja aplikacji (pełny CRUD, W3)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="dawca",
        on_delete=models.CASCADE,  # usunięcie konta usuwa też jego donacje (RODO)
        related_name="donations",
    )
    donation_type = models.ForeignKey(
        DonationType,
        verbose_name="rodzaj",
        on_delete=models.PROTECT,  # nie da się usunąć rodzaju, który ma donacje
        related_name="donations",
    )
    donation_date = models.DateField("data donacji")
    volume_ml = models.PositiveIntegerField("objętość (ml)")
    facility = models.ForeignKey(
        Facility,
        verbose_name="placówka",
        on_delete=models.PROTECT,
        related_name="donations",
        null=True,
        blank=True,
    )
    location_text = models.CharField(
        "inne miejsce",
        max_length=200,
        blank=True,
        help_text="Wypełnij, jeśli placówki nie ma na liście (np. akcja w mobilnym punkcie).",
    )
    notes = models.TextField("notatki", blank=True)

    class Meta:
        verbose_name = "donacja"
        verbose_name_plural = "donacje"
        ordering = ["-donation_date", "-created_at"]
        # dziennik, dashboard i kalkulator zawsze pytają o donacje jednego dawcy po dacie
        indexes = [models.Index(fields=["user", "donation_date"], name="donation_user_date_idx")]
        constraints = [
            # to samo, co sprawdza clean(), ale pilnowane też przez bazę danych
            models.CheckConstraint(
                condition=Q(facility__isnull=False) | ~Q(location_text=""),
                name="donation_facility_or_location",
                violation_error_message="Wybierz placówkę albo wpisz miejsce donacji.",
            ),
            models.CheckConstraint(
                condition=Q(volume_ml__gt=0),
                name="donation_volume_positive",
                violation_error_message="Objętość musi być większa od zera.",
            ),
        ]

    def __str__(self):
        return f"{self.donation_type} – {self.donation_date:%d.%m.%Y}"

    @property
    def place(self):
        """Nazwa miejsca do wyświetlenia: placówka z listy albo wpisany tekst."""
        return str(self.facility) if self.facility else self.location_text

    def clean(self):
        """Walidacja wywoływana przez formularze i panel admina.

        Błędy przypisujemy do konkretnych pól, żeby pokazały się przy nich (W5).
        """
        errors = {}

        if self.donation_date and self.donation_date > timezone.localdate():
            errors["donation_date"] = "Data donacji nie może być z przyszłości."

        if self.donation_type_id and self.volume_ml is not None:
            dtype = self.donation_type
            if not dtype.min_volume_ml <= self.volume_ml <= dtype.max_volume_ml:
                errors["volume_ml"] = (
                    f"Dla rodzaju „{dtype.name}” objętość musi wynosić "
                    f"od {dtype.min_volume_ml} do {dtype.max_volume_ml} ml."
                )

        if not self.facility_id and not self.location_text.strip():
            errors["facility"] = "Wybierz placówkę albo wpisz miejsce donacji."

        if errors:
            raise ValidationError(errors)

    def validate_constraints(self, exclude=None):
        # Reguły „placówka albo miejsce” i „objętość > 0” sprawdza już clean()
        # i przypina błąd do konkretnego pola. Bez tego formularz pokazałby
        # ten sam błąd drugi raz, ogólnie nad formularzem. Baza dalej ich pilnuje.
        exclude = {*(exclude or ()), "location_text", "volume_ml"}
        super().validate_constraints(exclude=exclude)

"""Formularze: walidacja danych wejściowych i komunikaty błędów przy polach (W5).

Reguły biznesowe (np. minimalny wiek dawcy) są w warstwie serwisów,
a formularz tylko je wywołuje i przypina błąd do właściwego pola.
"""

from django import forms
from django.contrib.auth import get_user_model, password_validation

from redhero.services import accounts

User = get_user_model()


class BootstrapFormMixin:
    """Dokleja klasy Bootstrapa do pól, a polom z błędem dodaje `is-invalid`."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            field.widget.attrs.setdefault("class", "form-select" if is_select else "form-control")

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs["class"] += " is-invalid"


class DonorRegistrationForm(BootstrapFormMixin, forms.Form):
    first_name = forms.CharField(label="Imię", max_length=150)
    last_name = forms.CharField(label="Nazwisko", max_length=150)
    email = forms.EmailField(label="Adres e-mail")
    date_of_birth = forms.DateField(
        label="Data urodzenia",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    sex = forms.ChoiceField(
        label="Płeć",
        choices=[("", "— wybierz —"), *User.Sex.choices],
        help_text="Od płci zależą progi odznak Honorowego Dawcy Krwi.",
    )
    password1 = forms.CharField(
        label="Hasło",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Co najmniej 8 znaków, nie same cyfry i nie popularne hasło.",
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if accounts.email_is_taken(email):
            raise forms.ValidationError("Konto z tym adresem e-mail już istnieje.")
        return email

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]
        accounts.validate_donor_birth_date(date_of_birth)
        return date_of_birth

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Hasła nie są takie same.")
        elif password1:
            # walidatory z AUTH_PASSWORD_VALIDATORS; tymczasowy obiekt User pozwala
            # wykryć hasło podobne do e-maila albo imienia
            candidate = User(
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )
            try:
                password_validation.validate_password(password1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        return accounts.register_donor(
            email=data["email"],
            password=data["password1"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["date_of_birth"],
            sex=data["sex"],
        )

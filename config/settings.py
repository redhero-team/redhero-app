"""Ustawienia projektu RedHero.

Wszystko, co zależy od środowiska (sekrety, baza danych, tryb debug), czytamy
ze zmiennych środowiskowych (W10). Lokalnie dostarcza je plik .env,
którego wzór jest w .env.example.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


DEBUG = env_bool("DJANGO_DEBUG", default=False)

# Domyślny klucz wolno użyć tylko lokalnie (DEBUG=True). Na produkcji brak klucza = błąd startu.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    "django-insecure-tylko-do-developmentu" if DEBUG else None
)
if not SECRET_KEY:
    raise RuntimeError("Ustaw zmienną środowiskową DJANGO_SECRET_KEY.")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Warstwa danych RedHero (modele + migracje)
    "redhero.data",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Szablony należą do warstwy prezentacji
        "DIRS": [BASE_DIR / "redhero" / "presentation" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Baza danych: PostgreSQL 16 (ADR-001) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "redhero"),
        "USER": os.environ.get("POSTGRES_USER", "redhero"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "redhero"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# --- Uwierzytelnianie (W4, W10) ---
# Własny model użytkownika z logowaniem po e-mailu.
# MUSI istnieć przed pierwszą migracją, późniejsza zmiana jest bardzo kosztowna.
AUTH_USER_MODEL = "redhero.User"

# Argon2 jako główny algorytm hashowania haseł, PBKDF2 jako fallback
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Język i czas ---
LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

# --- Pliki statyczne ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

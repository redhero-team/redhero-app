# ADR-001: Stos technologiczny aplikacji RedHero

- **Status:** Proponowany (szkic do zatwierdzenia przez zespół)
- **Data:** 2026-11-11
- **Sprint:** 0
- **Issue:** #13
- **Decydenci:** cały zespół Developers, zatwierdza Product Owner

## Kontekst

RedHero to aplikacja webowa dla krwiodawców. Pozwala zarejestrować się, rejestrować donacje, przeglądać dziennik, liczyć terminy kolejnych donacji i postęp do odznak HDK. Ma też panel administratora.

Wybór stosu wynika z wymagań projektu (PDF „Projekt złożony – wymagania”):

| Wymaganie | Co oznacza dla stosu |
|---|---|
| W2 | trwała baza danych, min. 3 powiązane encje |
| W3 | pełny CRUD dla głównej encji (Donacja) |
| W4 | uwierzytelnianie i min. 2 role (USER, ADMIN) |
| W5 | interfejs webowy z walidacją i czytelnymi komunikatami błędów |
| W6 | architektura warstwowa: logika biznesowa oddzielona od prezentacji i dostępu do danych |
| W7 | testy jednostkowe + min. 1 integracyjny, raport pokrycia (≥ 60% logiki biznesowej) |
| W9 | uruchomienie jednym poleceniem (zalecany docker-compose) |
| W10 | brak sekretów w repo, hasła przechowywane jako hash |

Ograniczenia zespołu:
- 5 osób, 6 sprintów po 2 tygodnie, MVP (cały zakres Must) na koniec Sprintu 3, czyli po ok. 8 tygodniach;
- każdy członek zespołu musi realnie programować i rozumieć cały kod, który oddajemy;
- aplikacja jest mała (kilkanaście ekranów, kilka encji) i nie ma wymagań wysokiej skalowalności.

## Rozważane opcje

### Backend

| Opcja | Plusy | Minusy |
|---|---|---|
| **Django (Python)** | gotowe: auth, sesje, hashowanie haseł, formularze z walidacją, ORM z migracjami, panel admina; prosty język; bardzo dobra dokumentacja | łatwo wrzucić logikę do widoków lub modeli, więc warstwę serwisów trzeba pilnować samemu (patrz Konsekwencje) |
| Spring Boot (Java) | wymusza warstwy (controller/service/repository), mocne typowanie | dużo konfiguracji i boilerplate'u, wolniejszy start przy krótkim harmonogramie |
| Node.js + Express (JS/TS) | jeden język z frontendem | auth, walidację, ORM i migracje trzeba składać z osobnych bibliotek, więcej decyzji i ryzyka |

### Frontend

| Opcja | Plusy | Minusy |
|---|---|---|
| **Szablony Django + Bootstrap 5** (opcjonalnie HTMX) | jeden projekt, jedno wdrożenie; formularze Django dają walidację i komunikaty błędów (W5); dark mode przez wbudowany przełącznik motywu w Bootstrapie | mniej „aplikacyjny” interfejs niż SPA |
| React (SPA) + Django REST Framework | nowoczesny UI, wyraźny podział front/back | dwa projekty, dwa buildy, osobne API, CORS, auth tokenowy: praktycznie podwójna praca przy MVP po 8 tygodniach |

### Baza danych

| Opcja | Plusy | Minusy |
|---|---|---|
| **PostgreSQL** | produkcyjna relacyjna baza, łatwa w docker-compose, ta sama w CI i lokalnie | wymaga kontenera (przy W9 i tak go mamy) |
| SQLite | zero konfiguracji | plik w kontenerze łatwo zgubić przy restarcie (W2), inne zachowanie niż baza produkcyjna |
| MongoDB | elastyczny schemat | nasze dane są relacyjne (User → Donation → DonationType/Facility), Django nie wspiera jej natywnie |

### Uwierzytelnianie

| Opcja | Plusy | Minusy |
|---|---|---|
| **Sesje Django (cookie)** | wbudowane, bezpieczne domyślnie (CSRF, HttpOnly), wylogowanie = usunięcie sesji | nie pasują do osobnej aplikacji mobilnej (nie planujemy jej) |
| JWT | bezstanowe, dobre dla SPA i aplikacji mobilnych | przy renderowaniu po stronie serwera nic nie dają, trudne unieważnianie tokenów, więcej kodu |

## Decyzja

| Obszar | Wybór |
|---|---|
| Język | Python 3.12 |
| Backend | Django 5.x, monolit z architekturą warstwową |
| Frontend | szablony Django + Bootstrap 5 (opcjonalnie HTMX do drobnych interakcji) |
| Baza danych | PostgreSQL 16 |
| Uwierzytelnianie | sesje Django (`django.contrib.auth`), własny model użytkownika z logowaniem po e-mailu |
| Role | Django Groups: `USER`, `ADMIN` (opcjonalnie `MODERATOR`) |
| Hashowanie haseł | Argon2 (`argon2-cffi`, pierwszy w `PASSWORD_HASHERS`), PBKDF2 jako fallback |
| Testy | pytest + pytest-django |
| Pokrycie kodu | pytest-cov (coverage.py), próg w CI: `--cov-fail-under=60` dla warstwy serwisów |
| Lint i formatowanie | ruff (`ruff check` + `ruff format`) |
| Uruchamianie | Docker + docker-compose (`docker compose up`) |
| CI | GitHub Actions przy każdym PR: ruff, migracje, testy z PostgreSQL jako service container |
| Konfiguracja i sekrety | zmienne środowiskowe (`.env`, w repo tylko `.env.example`) |

### Planowany podział na warstwy (W6)

```
presentation/   views.py, forms.py, templates/   → obsługa HTTP, walidacja wejścia, renderowanie
services/       services.py                      → logika biznesowa (terminy donacji, odznaki, kalkulator)
data/           models.py (+ ewentualnie selectors.py) → encje i dostęp do bazy przez ORM
```

Zasada: widok wywołuje serwis, a serwis korzysta z modeli. Logika biznesowa nie zna obiektu `request` i nie renderuje szablonów, więc da się ją testować jednostkowo bez serwera.

## Konsekwencje

**Pozytywne**
- Auth, sesje, hashowanie haseł, CSRF, walidacja formularzy i panel admina są dostępne od razu (W4, W5, W10). Czas idzie w funkcje domenowe, a nie w infrastrukturę.
- Jeden projekt i jeden kontener aplikacji plus baza to proste docker-compose i proste CI (W9).
- Python jest czytelny, więc każda osoba w zespole jest w stanie wyjaśnić kod na odbiorze.

**Negatywne / ryzyka**
- Django nie wymusza warstwy serwisów. Musimy ją pilnować na code review, inaczej diagram architektury rozjedzie się z kodem.
- Własny model użytkownika (`AUTH_USER_MODEL`) musi powstać **przed pierwszą migracją** (task #14). Późniejsza zmiana jest bardzo kosztowna.
- Interfejs renderowany po stronie serwera ogranicza dynamikę UI. Przy naszych ekranach (formularze, listy, dashboard) to akceptowalne.
- Specyfikację interfejsów (sekcja 5, pkt 5 wymagań) opiszemy jako listę URL-i/widoków z metodą, danymi wejściowymi i odpowiedzią oraz jako sygnatury funkcji warstwy serwisów, a nie jako OpenAPI.

## Powiązane decyzje (do opisania w Sprincie 1)

- **ADR-002:** sesje zamiast JWT. Rozwinięcie sekcji „Uwierzytelnianie”.
- **ADR-003:** monolit z szablonami zamiast SPA + REST API. Rozwinięcie sekcji „Frontend”.

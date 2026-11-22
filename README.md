# redhero-app
Base repositroy for Red Hero application and documentation

My first commit done:
- Krzysiek
- Filip 
- Dawid
- Adrian

## Stos technologiczny

Python 3.12, Django 5.2, PostgreSQL 16, Bootstrap 5, pytest, ruff, Docker.
Uzasadnienie wyboru: [ADR-001](docs/architecture/ADR-001-stos-technologiczny.md).

## Uruchomienie lokalne

Wymagany jest tylko [Docker Desktop](https://www.docker.com/products/docker-desktop/), bez lokalnego Pythona i Postgresa.

```bash
cp .env.example .env          # jednorazowo: lokalna konfiguracja
docker compose up --build     # baza + aplikacja, migracje uruchamiają się automatycznie
```

Aplikacja działa pod adresem http://localhost:8000.

Konto administratora (panel pod `/admin/`):

```bash
docker compose exec web python manage.py createsuperuser
```

## Testy i lint

```bash
docker compose run --rm web pytest              # testy + raport pokrycia (próg 60%)
docker compose run --rm web ruff check .        # linter
docker compose run --rm web ruff format .       # automatyczne formatowanie
```

Te same kroki uruchamia GitHub Actions przy każdym PR (`.github/workflows/ci.yml`).
PR z błędem lintera albo z nieprzechodzącym testem nie może zostać zmergowany.

## Struktura projektu (architektura warstwowa, W6)

```
config/                 ustawienia Django, główne URL-e
redhero/
  presentation/         widoki, formularze, szablony, URL-e   → obsługa HTTP
  services/             logika biznesowa                      → bez request i szablonów
  data/                 modele i migracje                     → dostęp do bazy
tests/                  testy jednostkowe i integracyjne
docs/                   dokumentacja (ADR, procesy, Scrum)
```

Zasada: widok wywołuje serwis, a serwis korzysta z modeli. Nigdy odwrotnie.

Test 1 

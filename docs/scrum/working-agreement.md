# Working Agreement — Zasady współpracy

## 1. Komunikacja

- Microsoft Teams jest głównym kanałem komunikacji zespołu.
- Bieżące pytania i problemy omawiamy na wspólnym kanale.
- Istotne ustalenia dotyczące implementacji i wymagań zapisujemy w GitHub Issues lub Pull Requestach.
- O problemach blokujących realizację zadań informujemy zespół możliwie szybko.
- Krótki check-in zespołu odbywa się w miarę możliwości w weekend.

## 2. Zarządzanie zadaniami

- GitHub Issues służą do opisywania i śledzenia zadań.
- GitHub Projects służy do monitorowania postępu prac.
- Każde zadanie powinno mieć przypisanego właściciela (`Assignee`).
- Każde zadanie powinno mieć określony typ i priorytet.
- Przed rozpoczęciem realizacji zadanie powinno mieć status `Ready`.
- Status zadania aktualizujemy w miarę postępu prac.

## 3. Statusy zadań

| Status | Znaczenie |
|---|---|
| Backlog | Zadanie oczekujące na doprecyzowanie lub przyszłą realizację |
| Ready | Zadanie przygotowane do rozpoczęcia |
| In Progress | Zadanie aktualnie realizowane |
| In Review | Zadanie przekazane do przeglądu w Pull Request |
| Done | Zadanie ukończone zgodnie z Definition of Done |

## 4. Typy i priorytety

Typ zadania:

- `Feature` — funkcjonalność.
- `Bug` — błąd.
- `Task` — prace techniczne, organizacyjne i utrzymaniowe.
Priorytet:

- `High` — najwyższy.
- `Medium` — średni.
- `Low` — niski.

Podczas wyboru zadań do sprintu w pierwszej kolejności rozpatrujemy zadania High, następnie Medium i Low.

## 5. Etykiety

W projekcie stosujemy następujące etykiety:

- `documentation` — zadania związane z dokumentacją.
- `testing` — zadania związane z testowaniem.
- `onboarding` — zadania związane z wdrożeniem członków zespołu.
- `development` — zadania związane z pracami implementacyjnymi.

Typ zadania i etykieta pełnią różne funkcje. Typ określa rodzaj zadania, a etykieta pozwala dodatkowo je sklasyfikować.

## 6. Praca z kodem

- Każde zadanie realizujemy na osobnym branchu.
- Nazwa brancha jest numerem powiązanego GitHub Issue, np. `123`.
- Nie wprowadzamy zmian bezpośrednio do głównej gałęzi repozytorium.
- Zmiany przekazujemy przez Pull Request.
- Każdy Pull Request wymaga minimum jednej akceptacji innego członka zespołu.
- Autor Pull Requesta nie zatwierdza własnych zmian.
- Pull Request powinien być powiązany z odpowiednim GitHub Issue.

## 7. Spotkania

Zespół organizuje:

- Sprint Planning — ustalenie celu i zakresu sprintu.
- Sprint Review — prezentacja rezultatów sprintu.
- Sprint Retrospective — omówienie współpracy i usprawnień.
- Estymację — przy wykorzystaniu Planning Poker.
- Pracę z backlogiem — doprecyzowanie przyszłych zadań.

Spotkania odbywają się za pośrednictwem Microsoft Teams.

## 8. Zasady ogólne

- Dbamy o czytelność i jakość kodu.
- Przeglądamy zmiany przed ich scaleniem.
- Nie pozostawiamy problemów blokujących pracę bez informacji dla zespołu.
- W razie niejasności ustalamy wymagania przed rozpoczęciem implementacji.
- Ustalenia dotyczące procesu pracy mogą być zmieniane podczas retrospektyw.
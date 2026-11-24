## Opis zmian
-

Closes #

## Jak przetestować
1.

## Zrzuty ekranu (opcjonalnie)

## Definition of Done
<!-- Zgodnie z docs/scrum/definition-of-done.md. Punkty niezwiązane z tym PR zostaw odznaczone i dopisz "n/d". -->
- [ ] Zmiany są na osobnym branchu z numerem Issue (np. `10-szablony-pr-issue`)
- [ ] PR jest powiązany z Issue (`Closes #`)
- [ ] Implementacja spełnia wymagania i kryteria akceptacji z Issue
- [ ] Aplikacja buduje się i uruchamia bez błędów (`docker compose up --build`)
- [ ] CI jest zielone (ruff, kontrola migracji, pytest z pokryciem min. 60%)
- [ ] Dodano lub zaktualizowano testy (jeśli dotyczy)
- [ ] Brak znanych błędów blokujących zrealizowaną funkcjonalność
- [ ] Dokumentacja zaktualizowana (jeśli dotyczy)
- [ ] Zachowana architektura warstwowa: widok → serwis → model
- [ ] Brak sekretów, haseł i plików `.env` w kodzie
- [ ] Min. 1 akceptacja innej osoby z zespołu (autor nie zatwierdza własnego PR)
- [ ] Po merge'u: status zadania w GitHub Projects zmieniony na Done

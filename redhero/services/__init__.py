"""Warstwa logiki biznesowej.

Zasady (ADR-001, W6):
- widok wywołuje serwis, a serwis korzysta z modeli z warstwy danych;
- serwis nie zna obiektu `request` i nie renderuje szablonów;
- dzięki temu logikę testujemy jednostkowo, bez serwera HTTP.

Tu trafią m.in. terminy kolejnych donacji, odznaki HDK i kalkulator krwiodawcy.
"""

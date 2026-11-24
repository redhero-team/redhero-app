"""Dane startowe słowników: rodzaje donacji i przykładowe placówki.

Bez nich formularz donacji byłby pusty. Migracja danych trafia tak samo
do każdej bazy: lokalnej, CI i produkcyjnej.

UWAGA: wartości medyczne są WSTĘPNE i czekają na weryfikację w #42
(źródła: RCKiK/NCK, rozporządzenia MZ). Po weryfikacji poprawiamy je
kolejną migracją albo w panelu admina.
"""

from django.db import migrations

DONATION_TYPES = [
    # code, name, default, min, max, ekwiwalent krwi pełnej, odstęp w dniach
    ("whole_blood", "Krew pełna", 450, 400, 500, 450, 56),
    ("plasma", "Osocze", 600, 200, 650, 200, 14),
    ("platelets", "Płytki krwi", 250, 100, 600, 250, 28),
    ("red_cells", "Krwinki czerwone", 360, 200, 500, 450, 112),
    ("white_cells", "Krwinki białe", 250, 100, 500, 500, 28),
]

FACILITIES = [
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Warszawa"),
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Kraków"),
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Gdańsk"),
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Wrocław"),
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Poznań"),
    ("Regionalne Centrum Krwiodawstwa i Krwiolecznictwa", "Łódź"),
]


def seed(apps, schema_editor):
    DonationType = apps.get_model("redhero", "DonationType")
    Facility = apps.get_model("redhero", "Facility")

    for code, name, default, vmin, vmax, equivalent, interval in DONATION_TYPES:
        DonationType.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "default_volume_ml": default,
                "min_volume_ml": vmin,
                "max_volume_ml": vmax,
                "whole_blood_equivalent_ml": equivalent,
                "min_interval_days": interval,
            },
        )

    for name, city in FACILITIES:
        Facility.objects.get_or_create(name=name, city=city)


def unseed(apps, schema_editor):
    apps.get_model("redhero", "DonationType").objects.filter(
        code__in=[row[0] for row in DONATION_TYPES], donations__isnull=True
    ).delete()
    apps.get_model("redhero", "Facility").objects.filter(
        name__in=[row[0] for row in FACILITIES], donations__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("redhero", "0002_donation_models"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]

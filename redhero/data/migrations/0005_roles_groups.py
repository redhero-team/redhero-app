"""Role aplikacji jako grupy Django: USER (dawca) i ADMIN (administrator), W4.

ADMIN dostaje uprawnienia do zarządzania słownikami i donacjami w panelu /admin/,
więc nie musi być superużytkownikiem.
"""

from django.contrib.auth.management import create_permissions
from django.db import migrations

ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"

# (model, akcje) dla roli ADMIN
ADMIN_PERMISSIONS = [
    ("donationtype", ["add", "change", "delete", "view"]),
    ("facility", ["add", "change", "delete", "view"]),
    ("donation", ["change", "delete", "view"]),
    ("user", ["view"]),
]


def create_roles(apps, schema_editor):
    # Uprawnienia Django tworzy dopiero po wszystkich migracjach,
    # więc na czystej bazie trzeba je utworzyć tutaj, zanim przypiszemy je do grupy.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model("redhero", "User")

    user_group, _ = Group.objects.get_or_create(name=ROLE_USER)
    admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)

    codenames = [f"{action}_{model}" for model, actions in ADMIN_PERMISSIONS for action in actions]
    admin_group.permissions.set(
        Permission.objects.filter(content_type__app_label="redhero", codename__in=codenames)
    )

    # dotychczasowi użytkownicy bez roli to dawcy
    for user in User.objects.filter(is_superuser=False, groups__isnull=True):
        user.groups.add(user_group)


def remove_roles(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name__in=[ROLE_USER, ROLE_ADMIN]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("redhero", "0004_user_birth_date_and_sex"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_roles, remove_roles),
    ]

"""Role użytkowników (W4): USER, czyli dawca, i ADMIN, czyli administrator.

Role to grupy Django zakładane migracją 0005. Superużytkownik zawsze ma uprawnienia admina.
"""

from django.contrib.auth.models import Group
from django.db import transaction

ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"
ROLES = (ROLE_USER, ROLE_ADMIN)


def is_admin(user) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    return user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists()


def role_of(user) -> str:
    return ROLE_ADMIN if is_admin(user) else ROLE_USER


@transaction.atomic
def set_role(user, role: str) -> None:
    """Nadaje dokładnie jedną rolę.

    ADMIN dostaje też `is_staff`, żeby mógł wejść do panelu /admin/.
    Uprawnień superużytkownika nie ruszamy.
    """
    if role not in ROLES:
        raise ValueError(f"Nieznana rola: {role}. Dostępne: {', '.join(ROLES)}.")

    user.groups.remove(*Group.objects.filter(name__in=ROLES))
    user.groups.add(Group.objects.get(name=role))
    if not user.is_superuser:
        user.is_staff = role == ROLE_ADMIN
        user.save(update_fields=["is_staff"])

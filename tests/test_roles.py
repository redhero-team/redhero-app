"""Role USER/ADMIN i dashboard administratora (#38, W4)."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command
from django.urls import reverse
from django.utils import timezone

from redhero.data.models import Donation, DonationType
from redhero.services import accounts, roles, stats

User = get_user_model()
PASSWORD = "Krwiodawca-2026"


@pytest.fixture
def donor(db):
    user = User.objects.create_user(email="dawca@example.com", password=PASSWORD)
    roles.set_role(user, roles.ROLE_USER)
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(email="admin@example.com", password=PASSWORD)
    roles.set_role(user, roles.ROLE_ADMIN)
    return user


# --- role: testy jednostkowe ---


@pytest.mark.django_db
def test_migration_creates_both_roles_with_admin_permissions():
    admin_group = Group.objects.get(name=roles.ROLE_ADMIN)
    codenames = set(admin_group.permissions.values_list("codename", flat=True))

    assert Group.objects.filter(name=roles.ROLE_USER).exists()
    assert {"add_facility", "change_donationtype", "view_donation"} <= codenames
    assert "add_user" not in codenames  # admin nie zakłada kont w panelu Django


def test_donor_is_not_admin(donor):
    assert not roles.is_admin(donor)
    assert roles.role_of(donor) == roles.ROLE_USER
    assert not donor.is_staff


def test_admin_role_gives_admin_rights_and_staff(admin_user):
    assert roles.is_admin(admin_user)
    assert roles.role_of(admin_user) == roles.ROLE_ADMIN
    assert admin_user.is_staff  # może wejść do /admin/


def test_superuser_is_always_admin(db):
    superuser = User.objects.create_superuser(email="root@example.com", password=PASSWORD)

    assert roles.is_admin(superuser)


def test_inactive_admin_is_not_admin(admin_user):
    admin_user.is_active = False

    assert not roles.is_admin(admin_user)


def test_set_role_replaces_previous_role(admin_user):
    roles.set_role(admin_user, roles.ROLE_USER)

    assert list(admin_user.groups.values_list("name", flat=True)) == [roles.ROLE_USER]
    assert not admin_user.is_staff


def test_set_role_rejects_unknown_role(donor):
    with pytest.raises(ValueError):
        roles.set_role(donor, "MODERATOR")


@pytest.mark.django_db
def test_registered_donor_gets_user_role():
    user = accounts.register_donor(
        email="nowy@example.com",
        password=PASSWORD,
        first_name="Nowy",
        last_name="Dawca",
        date_of_birth=timezone.localdate().replace(year=1990),
        sex="M",
    )

    assert list(user.groups.values_list("name", flat=True)) == [roles.ROLE_USER]


# --- komenda set_role ---


def test_set_role_command(donor, capsys):
    call_command("set_role", "DAWCA@example.com", "ADMIN")

    donor.refresh_from_db()
    assert roles.is_admin(donor)
    assert "ma teraz rolę ADMIN" in capsys.readouterr().out


@pytest.mark.django_db
def test_set_role_command_unknown_user():
    with pytest.raises(CommandError):
        call_command("set_role", "nikt@example.com", "ADMIN")


# --- statystyki ---


def test_admin_summary_counts(donor, admin_user):
    whole_blood = DonationType.objects.get(code="whole_blood")
    plasma = DonationType.objects.get(code="plasma")
    for dtype, volume in [(whole_blood, 450), (whole_blood, 450), (plasma, 600)]:
        Donation.objects.create(
            user=donor,
            donation_type=dtype,
            donation_date=timezone.localdate(),
            volume_ml=volume,
            location_text="Punkt",
        )

    summary = stats.admin_summary()

    assert summary["users_count"] == 2
    assert summary["donors_with_donations"] == 1
    assert summary["donations_count"] == 3
    assert summary["recent_donations_count"] == 3
    assert summary["total_volume_ml"] == 1500
    assert summary["by_type"][0] == {"name": "Krew pełna", "count": 2, "volume": 900}
    assert summary["newest_users"][0] == admin_user


@pytest.mark.django_db
def test_admin_summary_without_data():
    summary = stats.admin_summary()

    assert summary["donations_count"] == 0
    assert summary["total_volume_ml"] == 0
    assert summary["by_type"] == []


# --- uprawnienia przez HTTP: testy integracyjne ---


@pytest.mark.django_db
def test_anonymous_user_is_sent_to_login(client):
    response = client.get(reverse("admin_dashboard"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_donor_gets_403_on_admin_dashboard(client, donor):
    client.force_login(donor)

    response = client.get(reverse("admin_dashboard"))

    assert response.status_code == 403
    assert "Brak dostępu" in response.content.decode()


def test_donor_cannot_enter_django_admin(client, donor):
    client.force_login(donor)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302  # przekierowanie na logowanie panelu Django
    assert reverse("admin:login") in response.url


def test_admin_sees_dashboard_and_menu_link(client, admin_user):
    client.force_login(admin_user)

    response = client.get(reverse("admin_dashboard"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Panel administratora" in content
    assert "Panel admina" in content  # link w menu


def test_donor_does_not_see_admin_link(client, donor):
    client.force_login(donor)

    response = client.get(reverse("dashboard"))

    assert "Panel admina" not in response.content.decode()


def test_admin_role_can_manage_facilities_in_django_admin(client, admin_user):
    client.force_login(admin_user)

    assert client.get(reverse("admin:redhero_facility_add")).status_code == 200
    # ale nie może zmieniać kont użytkowników (tylko podgląd)
    assert client.get(reverse("admin:redhero_user_add")).status_code == 403

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Donation, DonationType, Facility, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Panel admina dla użytkownika bez pola username (logowanie e-mailem)."""

    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dane osobowe", {"fields": ("first_name", "last_name", "date_of_birth", "sex")}),
        (
            "Uprawnienia",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Ważne daty", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(DonationType)
class DonationTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "default_volume_ml",
        "whole_blood_equivalent_ml",
        "min_interval_days",
        "is_active",
    ]
    list_filter = ["is_active"]
    prepopulated_fields = {"code": ["name"]}


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "address", "is_active"]
    list_filter = ["is_active", "city"]
    search_fields = ["name", "city", "address"]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["donation_date", "user", "donation_type", "volume_ml", "place"]
    list_filter = ["donation_type", "facility"]
    search_fields = ["user__email", "user__last_name", "location_text", "notes"]
    date_hierarchy = "donation_date"
    list_select_related = ["user", "donation_type", "facility"]
    autocomplete_fields = ["user", "facility"]

    @admin.display(description="miejsce")
    def place(self, obj):
        return obj.place

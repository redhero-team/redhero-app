"""Statystyki dla dashboardu administratora."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from redhero.data.models import Donation, DonationType

RECENT_DAYS = 30


def admin_summary(today=None) -> dict:
    today = today or timezone.localdate()
    User = get_user_model()
    since = today - timedelta(days=RECENT_DAYS)

    donations = Donation.objects.all()
    return {
        "users_count": User.objects.filter(is_active=True).count(),
        "donors_with_donations": donations.values("user").distinct().count(),
        "donations_count": donations.count(),
        "total_volume_ml": donations.aggregate(total=Sum("volume_ml"))["total"] or 0,
        "recent_days": RECENT_DAYS,
        "recent_donations_count": donations.filter(donation_date__gt=since).count(),
        "by_type": list(
            DonationType.objects.annotate(
                count=Count("donations"), volume=Sum("donations__volume_ml")
            )
            .filter(count__gt=0)
            .order_by("-count", "name")
            .values("name", "count", "volume")
        ),
        "newest_users": list(User.objects.order_by("-date_joined")[:5]),
    }

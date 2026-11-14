"""Test integracyjny: żądanie HTTP przechodzi przez URL, widok i szablon."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_renders(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "RedHero" in response.content.decode()

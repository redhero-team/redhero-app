from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("rejestracja/", views.register, name="register"),
    path("logowanie/", views.DonorLoginView.as_view(), name="login"),
    path("wyloguj/", views.logout_view, name="logout"),
    path("panel/", views.dashboard, name="dashboard"),
]

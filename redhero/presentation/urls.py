from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("rejestracja/", views.register, name="register"),
    path("logowanie/", views.DonorLoginView.as_view(), name="login"),
    path("wyloguj/", views.logout_view, name="logout"),
    path("panel/", views.dashboard, name="dashboard"),
    path("panel-admina/", views.admin_dashboard, name="admin_dashboard"),
    path("donacje/", views.donation_list, name="donation_list"),
    path("donacje/nowa/", views.donation_create, name="donation_create"),
    path("donacje/<int:pk>/edycja/", views.donation_update, name="donation_update"),
    path("donacje/<int:pk>/usun/", views.donation_delete, name="donation_delete"),
]

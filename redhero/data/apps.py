from django.apps import AppConfig


class DataConfig(AppConfig):
    name = "redhero.data"
    # Krótka etykieta używana w AUTH_USER_MODEL ("redhero.User") i w nazwach tabel
    label = "redhero"
    verbose_name = "RedHero"

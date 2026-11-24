"""Nadaje rolę użytkownikowi z konsoli, np. przy zakładaniu kont testowych.

Przykład:
    docker compose exec web python manage.py set_role admin@redhero.pl ADMIN
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from redhero.services import roles


class Command(BaseCommand):
    help = "Nadaje użytkownikowi rolę USER albo ADMIN."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("role", choices=roles.ROLES)

    def handle(self, *args, email, role, **options):
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as error:
            raise CommandError(f"Nie ma użytkownika {email}.") from error

        roles.set_role(user, role)
        self.stdout.write(self.style.SUCCESS(f"{user.email} ma teraz rolę {role}."))

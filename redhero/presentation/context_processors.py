"""Dane dostępne w każdym szablonie."""

from redhero.services import roles


def user_role(request):
    # menu pokazuje link do panelu admina tylko administratorom
    return {"is_admin": roles.is_admin(request.user)}

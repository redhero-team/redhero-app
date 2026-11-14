from django.shortcuts import render


def home(request):
    """Strona startowa. Docelowo: dashboard dawcy po zalogowaniu."""
    return render(request, "home.html")

from django.shortcuts import render
from .logic import run_skin_engine


def skin_form(request):
    if request.method == "POST":
        result = run_skin_engine(request.POST)
        if result.get("error"):
            return render(request, "skin_profile/skin_form.html", {"form_error": result["message"]})

        # Confirmation screen — user verifies before seeing routine
        if not request.POST.get("confirmed"):
            return render(request, "skin_profile/confirm.html", result)

        return render(request, "skin_profile/result.html", result)

    return render(request, "skin_profile/skin_form.html")


def confirm_result(request):
    """
    Called when user submits the confirmation screen.
    Re-runs engine with same data and confirmed=true.
    """
    if request.method == "POST":
        result = run_skin_engine(request.POST)
        return render(request, "skin_profile/result.html", result)
    return render(request, "skin_profile/skin_form.html")

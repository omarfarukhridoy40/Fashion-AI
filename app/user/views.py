from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegistrationForm


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Account created successfully! Please log in."
            )
            return redirect("login")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    # Implement logout logic here
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    from body_profile.models import BodyProfile

    try:
        body_profile = request.user.body_profile
    except BodyProfile.DoesNotExist:
        body_profile = None

    profile_steps = {
        "basic": bool(
            body_profile and body_profile.height_cm and body_profile.weight_kg
        ),
        "shape": bool(body_profile and body_profile.body_shape),
        "photo": bool(
            body_profile
            and (body_profile.body_photo or body_profile.face_photo)
        ),
        "skin": bool(
            body_profile and body_profile.skin_type and body_profile.vein_color
        ),
    }
    steps_total = len(profile_steps)
    steps_done = sum(1 for done in profile_steps.values() if done)
    profile_progress_percent = (
        int((steps_done / steps_total) * 100) if steps_total else 0
    )

    return render(
        request,
        "dashboards/dashboard.html",
        {
            "has_body_profile": body_profile is not None,
            "body_profile": body_profile,
            "profile_steps": profile_steps,
            "profile_progress_percent": profile_progress_percent,
        },
    )

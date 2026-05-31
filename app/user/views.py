import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import UserLoginForm, UserRegistrationForm
from skin.models import UserSkinProfile


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
    # Two-pillar dashboard. The Skin pillar is driven by the user's saved
    # UserSkinProfile (persisted by the skin app's confirm_result flow); the
    # Fashion pillar is all coming-soon cards rendered in the template.
    #
    # Brief 01 keeps one current profile per user via update_or_create, so
    # .first() returns that single row (or None for a user who has not analysed
    # their skin yet).
    profile = UserSkinProfile.objects.filter(linked_user=request.user).first()

    # skin_profile is a small dict the template consumes, or None for the empty
    # state. Building it here keeps the template free of parsing logic.
    skin_profile = None
    has_routine_started = False
    routine_day = None
    if profile is not None:
        # skin_states was persisted as json.dumps([{state, reason, ...}, ...]).
        # Wrap the load so a malformed or legacy blob degrades to [] instead of
        # raising and returning a 500 for the whole dashboard.
        try:
            skin_states = json.loads(profile.skin_states) if profile.skin_states else []
        except (ValueError, TypeError):
            skin_states = []

        # top_concerns was persisted as comma-separated concern keys. The "if c"
        # guard drops empty strings so a blank field yields [] rather than [''].
        top_concerns = [c for c in profile.top_concerns.split(",") if c]

        skin_profile = {
            "skin_type":         profile.skin_type,
            "primary_concern":   profile.primary_concern,
            "conflict_detected": profile.conflict_detected,
            "skin_states":       skin_states,
            "top_concerns":      top_concerns,
        }

        # Routine progress for the "Your Progress" card. routine_start_date is
        # set by skin.start_routine; None until the user taps Start.
        has_routine_started = profile.routine_start_date is not None
        if has_routine_started:
            # Day number from calendar dates: +1 so the start day reads as
            # "Day 1" (not "Day 0"). Compared on .date() so the count rolls over
            # at midnight rather than on the 24-hour mark.
            delta_days = (timezone.now().date() - profile.routine_start_date.date()).days
            routine_day = delta_days + 1

    return render(
        request,
        "dashboards/dashboard.html",
        {
            "skin_profile":        skin_profile,
            "has_routine_started": has_routine_started,
            "routine_day":         routine_day,
        },
    )

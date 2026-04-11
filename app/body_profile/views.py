from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import BodyProfile
from .forms import BodyProfileForm


@login_required
def create_body_profile_view(request):
    # If already has a profile, send them to detail
    if BodyProfile.objects.filter(user=request.user).exists():
        return redirect("body_profile")

    if request.method == "POST":
        form = BodyProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect("body_profile")
    else:
        form = BodyProfileForm()

    return render(
        request, "body_profile/body_profile_form.html", {"form": form}
    )


@login_required
def body_profile_view(request):
    # If no profile yet, send them to create
    if not BodyProfile.objects.filter(user=request.user).exists():
        return redirect("create_body_profile")

    profile = BodyProfile.objects.get(user=request.user)
    return render(
        request, "body_profile/body_profile_detail.html", {"profile": profile}
    )


@login_required
def update_body_profile_view(request):
    # If no profile yet, send them to create
    if not BodyProfile.objects.filter(user=request.user).exists():
        return redirect("create_body_profile")

    profile = BodyProfile.objects.get(user=request.user)

    if request.method == "POST":
        form = BodyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("body_profile")
    else:
        form = BodyProfileForm(instance=profile)

    return render(
        request, "body_profile/body_profile_form.html", {"form": form}
    )

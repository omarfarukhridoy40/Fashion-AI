from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import BodyProfile
from .forms import BodyProfileForm


@login_required
def body_profile_view(request):

    profile, created = BodyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        form = BodyProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            body_profile = form.save(commit=False)
            body_profile.user = request.user
            body_profile.save()
            return redirect("dashboard")
    else:
        form = BodyProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile
    }

    return render(request, "body_profile/body_profile_form.html", context)
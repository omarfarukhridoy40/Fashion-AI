from django.urls import path

from . import views

urlpatterns = [
    path("", views.body_profile_view, name="body_profile"),
]

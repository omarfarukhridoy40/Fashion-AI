from django.urls import path

from . import views

urlpatterns = [
    path("", views.body_profile_view, name="body_profile"),
    path("create/", views.create_body_profile_view, name="create_body_profile"),
    path("update/", views.update_body_profile_view, name="update_body_profile"),
]

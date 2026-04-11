from django.urls import path
from . import views

urlpatterns = [
    path('', views.skin_form, name='skin_form'),
    path('confirm/', views.confirm_result, name='confirm_result'),
]
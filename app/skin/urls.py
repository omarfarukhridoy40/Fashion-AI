from django.urls import path
from . import views

urlpatterns = [
    path('', views.skin_form, name='skin_form'),
    path('confirm/', views.confirm_result, name='confirm_result'),
    path('my-routine/', views.my_routine, name='my_routine'),
    path('start-routine/', views.start_routine, name='start_routine'),
]

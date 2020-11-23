from django.urls import path, include
from . import views

urlpatterns = [
    path('callback/', views.callback)
]

from django.urls import path, include
from . import views

app_name = 'line'
urlpatterns = [
    path('callback/', views.callback, name='callback'),
    path('test/', views.push_notice, name='test'),
]

#news URL Configuration
from django.urls import path, include
from . import views 

urlpatterns = [
    path('', views.index, name='index'),
    path('post/', views.post, name='post'),
]

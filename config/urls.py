# cards/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<key>/", views.showcase_detail, name="showcase_detail"),
]

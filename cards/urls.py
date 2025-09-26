from django.urls import path
from . import views

urlpatterns = [
    path("<int:pk>/", views.showcase_detail, name="showcase_detail"),  # /1, /2, ...
    path("", views.index, name="index"),
]

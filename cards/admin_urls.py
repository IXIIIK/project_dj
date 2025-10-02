from django.urls import path
from . import views

urlpatterns = [
    # Витрины
    path("", views.showcases_admin, name="showcases_admin"),
    path("add/", views.showcase_add, name="showcase_add"),
    path("<str:key>/edit/", views.showcase_edit, name="showcase_edit"),
    path("<str:key>/delete/", views.showcase_delete, name="showcase_delete"),
    path("<str:key>/duplicate/", views.showcase_duplicate, name="showcase_duplicate"),

    # Карточки внутри витрины
    path("<str:key>/cards/", views.cards_admin, name="cards_admin"),
    path("<str:key>/cards/add/", views.card_add, name="card_add"),
    path("<str:key>/cards/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("<str:key>/cards/<int:pk>/delete/", views.card_delete, name="card_delete"),
    path("<str:key>/cards/<int:pk>/toggle/", views.card_toggle, name="card_toggle"),

    path("logos/", views.logos_admin, name="logos_admin"),
    path("logos/add/", views.logo_add, name="logo_add"),
    path("logos/<int:pk>/delete/", views.logo_delete, name="logo_delete"),
]

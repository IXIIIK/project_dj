from django.urls import path
from . import views

urlpatterns = [
    # список/создание
    path("", views.showcases_admin, name="showcases_admin"),
    path("add/", views.showcase_add, name="showcase_add"),

    # ЛОГО
    path("logos/", views.logos_admin, name="logos_admin"),
    path("logos/add/", views.logo_add, name="logo_add"),
    path("logos/<int:pk>/delete/", views.logo_delete, name="logo_delete"),

    # действия над витриной — только по id
    path("<int:pk>/edit/", views.showcase_edit, name="showcase_edit"),
    path("<int:pk>/delete/", views.showcase_delete, name="showcase_delete"),
    path("<int:pk>/duplicate/", views.showcase_duplicate, name="showcase_duplicate"),

    # карточки внутри витрины
    path("<int:pk>/cards/", views.cards_admin, name="cards_admin"),
    path("<int:pk>/cards/add/", views.card_add, name="card_add"),
    path("<int:pk>/cards/<int:cid>/edit/", views.card_edit, name="card_edit"),
    path("<int:pk>/cards/<int:cid>/delete/", views.card_delete, name="card_delete"),
    path("<int:pk>/cards/<int:cid>/toggle/", views.card_toggle, name="card_toggle"),
]

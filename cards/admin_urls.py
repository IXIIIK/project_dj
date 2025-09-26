from django.urls import path
from . import views

urlpatterns = [
    # Витрины
    path("", views.showcases_admin, name="showcases_admin"),
    path("add/", views.showcase_add, name="showcase_add"),
    path("<int:pk>/edit/", views.showcase_edit, name="showcase_edit"),
    path("<int:pk>/delete/", views.showcase_delete, name="showcase_delete"),

    # Карточки внутри конкретной витрины
    path("<int:showcase_id>/cards/", views.cards_admin, name="cards_admin"),
    path("<int:showcase_id>/cards/add/", views.card_add, name="card_add"),
    path("<int:showcase_id>/cards/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("<int:showcase_id>/cards/<int:pk>/delete/", views.card_delete, name="card_delete"),
    path("<int:showcase_id>/cards/<int:pk>/toggle/", views.card_toggle, name="card_toggle"),
]

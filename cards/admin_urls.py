from django.urls import path
from . import views

urlpatterns = [
    # --- фиксированные разделы (ДОЛЖНЫ идти раньше динамики) ---
    path("", views.showcases_admin, name="showcases_admin"),
    path("add/", views.showcase_add, name="showcase_add"),

    # лого (отдельная секция)
    path("logos/", views.logos_admin, name="logos_admin"),
    path("logos/add/", views.logo_add, name="logo_add"),
    path("logos/<int:pk>/delete/", views.logo_delete, name="logo_delete"),

    # действия над витриной (фиксированные хвосты)
    path("<slug:key>/edit/", views.showcase_edit, name="showcase_edit"),
    path("<slug:key>/delete/", views.showcase_delete, name="showcase_delete"),
    path("<slug:key>/duplicate/", views.showcase_duplicate, name="showcase_duplicate"),

    # карточки внутри витрины
    path("<slug:key>/cards/", views.cards_admin, name="cards_admin"),
    path("<slug:key>/cards/add/", views.card_add, name="card_add"),
    path("<slug:key>/cards/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("<slug:key>/cards/<int:pk>/delete/", views.card_delete, name="card_delete"),
    path("<slug:key>/cards/<int:pk>/toggle/", views.card_toggle, name="card_toggle"),
]


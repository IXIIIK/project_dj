from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", include("cards.admin_urls")),  # кастомная админка
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
    path("", include("cards.urls")),              # публичные страницы
]

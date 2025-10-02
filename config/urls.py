# config/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    # кастомная админка витрин по /admin/...
    path("admin/", include("cards.admin_urls")),

    # логин/логаут
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),

    # публичная часть
    path("", include("cards.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

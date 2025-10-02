
from pathlib import Path
import os
from dotenv import load_dotenv

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS","*").split(",")
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("CSRF_TRUSTED_ORIGINS","").split(",") if x.strip()]
#DEBUG = os.getenv("DJANGO_DEBUG","0") == "1"
DEBUG = 1

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-not-secret")

load_dotenv(BASE_DIR / ".env")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "cards",
]

DOMAINS_ALLOWED = [
    "localhost", "127.0.0.1",       
    "xn--d1asbcbidu0b.xn--p1ai",    #сподручно.рф
    "xn--80aatfbqgidf6l.xn--p1ai",  # заимыонлаин.рф
    "xn--80anhmuy1c.online",        # займырф.online (пример)
    "xn--80agfgliehw.xn--p1ai",     # займлегко.рф (пример)
    # при желании — и юникод-формы:
    "сподручно.рф"
    "заимыонлаин.рф",
    "займырф.online",
    "займлегко.рф",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")

if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASS"),
            "HOST": os.getenv("DB_HOST","db"),
            "PORT": os.getenv("DB_PORT","5432"),
        }
    }

else:  # SQLite по умолчанию
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


# STATIC_URL = "/static/"
# STATICFILES_DIRS = [BASE_DIR / "static"]
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static_root"          # куда collectstatic кладёт
STATICFILES_DIRS = [BASE_DIR / "static"]        # ОТКУДА забирать твой style.css и img/

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

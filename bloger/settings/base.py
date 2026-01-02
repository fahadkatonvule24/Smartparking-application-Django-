"""
Base Django settings shared across environments.
Environment specific overrides live in development.py / production.py / staging.py.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Tuple

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(
        str,
        "replace-this-with-a-secure-random-value-and-keep-it-secret-please",
    ),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    LOG_LEVEL=(str, "INFO"),
    DATABASE_URL=(str, f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"),
    EMAIL_BACKEND=(
        str,
        "django.core.mail.backends.console.EmailBackend",
    ),
)

env_file = os.getenv("DJANGO_ENV_FILE")
env_file_path = Path(env_file) if env_file else BASE_DIR / ".env"
if env_file_path.exists():
    environ.Env.read_env(str(env_file_path))


def parse_admins(admin_list: Iterable[str]) -> List[Tuple[str, str]]:
    """Convert a list of `Name,email@example.com` strings to Django's ADMINS format."""
    parsed: List[Tuple[str, str]] = []
    for admin in admin_list:
        if "," in admin:
            name, email = admin.split(",", 1)
            parsed.append((name.strip(), email.strip()))
    return parsed


SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "blog",
    "crispy_forms",
    "crispy_bootstrap5",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bloger.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.global_login_form",
            ],
        },
    },
]

WSGI_APPLICATION = "bloger.wsgi.application"

DATABASES = {"default": env.db()}
if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    DATABASES["default"]["OPTIONS"] = {"timeout": 20}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CACHES = {
    "default": env.cache(
        "CACHE_URL", default="locmemcache://smart-parking-session-cache"
    )
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

ADMINS = parse_admins(env.list("ADMINS", default=[]))
EMAIL_BACKEND = env("EMAIL_BACKEND")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

LOG_LEVEL = env("LOG_LEVEL")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

"""Development settings."""

from .base import *  # noqa: F401,F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

# Keep DEBUG on locally unless explicitly overridden.
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug toolbar to diagnose performance locally.
if env.bool("ENABLE_DEBUG_TOOLBAR", default=False):
    INSTALLED_APPS += ["debug_toolbar"]  # type: ignore # noqa: F405
    MIDDLEWARE.insert(
        1, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )  # type: ignore # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _request: DEBUG}

# Use the simpler staticfiles storage locally to avoid manifest requirements.
STORAGES["staticfiles"]["BACKEND"] = (  # type: ignore # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore # noqa: F405

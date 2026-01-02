"""Production settings."""

from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["yourdomain.com", "www.yourdomain.com"]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[f"https://{host}" for host in ALLOWED_HOSTS if host != "localhost"],
)

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Prefer Redis/memcached when CACHE_URL is provided.
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

LOGGING["loggers"]["django"]["level"] = "INFO"  # type: ignore # noqa: F405

SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.05),
        send_default_pii=False,
    )

"""Staging settings mirror production with optional debug toggles."""

from .production import *  # noqa: F401,F403

DEBUG = env.bool("DEBUG", default=False)  # type: ignore # noqa: F405

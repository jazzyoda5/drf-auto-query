import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "tests",
]

MIDDLEWARE = []

USE_TZ = True

TIME_ZONE = "UTC"

SECRET_KEY = "can-tell-you-but-must-kill-you"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

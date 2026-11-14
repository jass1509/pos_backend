import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
#ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
#ALLOWED_HOSTS = ['*']
ALLOWED_HOSTS = ['pos-backend-rho-two.vercel.app','vercel.app', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = [
    'https://pos-backend-rho-two.vercel.app',
    'https://*.vercel.app',
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "accounts",
    "inventory",
    "sales",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.app"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
load_dotenv("""BASE_DIR / ".env""")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("name", "pos_db"),
        "USER": os.getenv("user", "postgres"),
        "PASSWORD": os.getenv("password", "postgres"),
        "HOST": os.getenv("host", "localhost"),
        "PORT": os.getenv("port", "5432"),
    }
}
"""DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pos_db",
        "USER": "postgres",
        "PASSWORD":"tu_nueva_contraseña_aqui",
        "HOST": "localhost",
        "PORT": "5432",
    }
}"""

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

#CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]

if DEBUG:
    # Flutter web usa un puerto distinto en cada ejecución
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),   # un turno de trabajo
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

import os
from pathlib import Path
<<<<<<< HEAD

import dj_database_url
=======
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

<<<<<<< HEAD
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() in {"1", "true", "yes", "on"}

allowed_hosts_raw = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_raw.split(",") if host.strip()]
=======
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
<<<<<<< HEAD
=======
    "corsheaders",
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
    "analyzer",
]

MIDDLEWARE = [
<<<<<<< HEAD
=======
    "corsheaders.middleware.CorsMiddleware",
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

<<<<<<< HEAD
=======
CORS_ALLOW_ALL_ORIGINS = True
APPEND_SLASH = True

>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
ROOT_URLCONF = "cropsight_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cropsight_backend.wsgi.application"
ASGI_APPLICATION = "cropsight_backend.asgi.application"

<<<<<<< HEAD
database_url = os.getenv("DATABASE_URL", "")
DATABASES = (
    {
        "default": dj_database_url.parse(database_url, conn_max_age=600, ssl_require=True),
    }
    if database_url
    else {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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
=======
# Django system tables still use SQLite locally.
# Application data (users, images, analysis) is stored in MongoDB via analyzer/mongo.py.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "cropsight")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
<<<<<<< HEAD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "farm-images")
=======

# Media files (uploaded images)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d

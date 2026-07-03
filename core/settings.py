"""
Settings da Plataforma PCP (Módulo: Controle de Chumbo).

Lê configuração de .env via django-environ (PRD §1.3 / §9.2 / §9.5).
Em dev local sem DATABASE_URL, cai em SQLite para validar telas rápido (§9.2).

Start Template (infra): apps da plataforma (base/accounts/shell/shared) e
AUTH_USER_MODEL ficam comentados — descomente na Sprint 1 antes do 1º migrate.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


def _env_int(key: str, default: int) -> int:
    raw = env.str(key, default="")
    return int(raw) if raw.strip() else default


def _env_bool(key: str, default: bool) -> bool:
    raw = env.str(key, default="")
    return env.bool(key, default=default) if raw.strip() else default

# ------------------------------------------------------------------ Core
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-troque-em-producao")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# ------------------------------------------------------------------ Apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_celery_beat",
    "django_celery_results",
    "dj_celery_panel",
]

# Plataforma — fixos e estáveis (criados na Sprint 1).
# Ordem: base primeiro (BaseModel/mixins), accounts antes do 1º migrate.
PLATFORM_APPS = [
    "base",
    "accounts",
    "shell",
    "shared",
]

# Módulos de negócio — descomente conforme cada módulo for criado.
# Ex.: "modules.chumbo" (e suas sub-apps) na Sprint 2.
MODULES_APPS = [
    "modules.chumbo",
    "modules.chumbo.ligas",
    "modules.chumbo.destinos",
    "modules.chumbo.modelos",
    "modules.chumbo.lotes",
    "modules.chumbo.montes",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PLATFORM_APPS + MODULES_APPS

# Fixado ANTES do primeiro migrate (accounts.User).
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailBackend"]

# ------------------------------------------------------------------ Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "base.middleware.SessionTimeoutMiddleware",
    "base.middleware.ModuleContextMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shell.context_processors.module_menu",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ------------------------------------------------------------------ Database
# Sem DATABASE_URL -> SQLite (dev rápido, §9.2). Com ela -> PostgreSQL.
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db()}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Default big int PK (PRD §5.1) — não UUID via SQL manual.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------ Auth / Sessão
# Sprint 1: LOGIN_URL aponta para accounts; enquanto accounts não existe,
# deixe o default do Django (útil só após a Sprint 1).
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# RF03: timeout por inatividade (30 min padrão). Idle real vem do
# base.middleware.SessionTimeoutMiddleware na Sprint 1; aqui só o teto.
SESSION_COOKIE_AGE = _env_int("SESSION_IDLE_TIMEOUT", 1800)
SESSION_SAVE_EVERY_REQUEST = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------ i18n / Tempo
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# RNF08/RNF09: armazena UTC, exibe America/Sao_Paulo; datas dd/MM/yyyy.
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]
USE_THOUSAND_SEPARATOR = False
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."

# ------------------------------------------------------------------ Static / Media / Storages
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ------------------------------------------------------------------ Segurança (prod)
if not DEBUG:
    # TLS termina no Traefik; confia no X-Forwarded-Proto dele (§9.4/§9.5).
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Redirect HTTP->HTTPS fica no Traefik (borda); /health/ interno em http.
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"
else:
    X_FRAME_OPTIONS = "SAMEORIGIN"

# ------------------------------------------------------------------ Email
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = _env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")

# ------------------------------------------------------------------ Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@rabbitmq:5672//")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 60 * 30
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 25
CELERY_TASK_DEFAULT_QUEUE = env("CELERY_TASK_DEFAULT_QUEUE", default="komotores_pcp")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_TASK_TRACK_STARTED = True

# Result backend "django-db" exige o app django_celery_results (já em THIRD_PARTY).

# dj-celery-panel: URLs incluídas em core/urls.py sob /admin/dj-celery-panel/.
DJ_CELERY_PANEL_SETTINGS = {
    "LOAD_DEFAULT_CSS": True,
    "EXTRA_CSS": [],
}

# ------------------------------------------------------------------ Cache
CACHES = {
    "default": env.cache("CACHE_URL", default="locmem://"),
}

# ------------------------------------------------------------------ Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

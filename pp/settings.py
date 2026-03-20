from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 SECURITY
# SECRET_KEY = os.environ.get('SECRET_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-key')
DEBUG = False
# ALLOWED_HOSTS = ['finex-kel1.onrender.com']
ALLOWED_HOSTS = ['sr-finance.onrender.com', '127.0.0.1', 'localhost']
# CSRF_TRUSTED_ORIGINS = [
#     "https://finex-kel1.onrender.com"
# ]
CSRF_TRUSTED_ORIGINS = [
    "https://finex-kel1.onrender.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
     "https://sr-finance.onrender.com",
]

# 🧠 APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
]

# ⚙️ MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ important
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pp.urls'

# 🎨 TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pp.wsgi.application'

# 🗄️ DATABASE (optimized)
# DATABASES = {
#     'default': dj_database_url.config(
#         default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
#         conn_max_age=600,   # keeps DB connection alive ⚡
#     )
# }
import os
import dj_database_url

DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get("DATABASE_URL")
    )
}

# 🔐 PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 INTERNATIONAL
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 📦 STATIC FILES (OPTIMIZED)
import os

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, '/static')   # 👈 THIS LINE IMPORTANT
]
# 🔥 IMPORTANT (performance boost)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 🔐 AUTH
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

# 📩 EMAIL (SendGrid)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
import os
DEFAULT_FROM_EMAIL = 'malladisrinu772@gmail.com'
ALLOWED_HOSTS = ['*']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')

# DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER')
DEFAULT_FROM_EMAIL='malladisrinu772@gmail.com'
# ⚡ CACHE (FREE performance boost)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# 🔒 SECURITY (lightweight but useful)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
# }
import os

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'apikey'   # always this (not your email)
EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")  # your API key

DEFAULT_FROM_EMAIL = 'malladisrinu772@gmail.com'
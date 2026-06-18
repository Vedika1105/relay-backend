from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG      = config('DEBUG', cast=bool, default=True)

# Comma-separated in .env, e.g. ALLOWED_HOSTS=your-app.up.railway.app
# Locally this still falls back to the same two hosts as before.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ─────────────────────────────────────────────────────────────
# APPS
# split into 3 groups so we always know where each app is from
# ─────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'daphne',                        # Needs to be at top of server 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.sites',          # required by allauth
]

THIRD_PARTY_APPS = [
    'rest_framework',                # builds our APIs
    'rest_framework_simplejwt',      # JWT login tokens
    'rest_framework_simplejwt.token_blacklist',
    # 'allauth',                       # handles registration, login, email verification
    # 'allauth.account',               # email + password auth
    # 'allauth.socialaccount',         # google/discord social login (added later)
    'channels', 
    'corsheaders',
]

LOCAL_APPS = [
    'apps.users',                    # our custom user app
    'apps.servers',
    'apps.chat',
    'apps.messaging',
    'apps.calls',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─────────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serves static files in prod, right after security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # 'allauth.account.middleware.AccountMiddleware',           # required by allauth
]

ROOT_URLCONF = 'config.urls'

# ─────────────────────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─────────────────────────────────────────────────────────────
# DATABASE
# all credentials come from .env — nothing hardcoded here.
# On Railway you don't touch this block at all: in the Railway
# dashboard you map their auto-generated Postgres variables onto
# these exact same names (DB_NAME, DB_USER, etc.) — zero code change.
# ─────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : config('DB_NAME'),
        'USER'    : config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST'    : config('DB_HOST'),
        'PORT'    : config('DB_PORT'),
    }
}

# ─────────────────────────────────────────────────────────────
# CUSTOM USER MODEL
# tells Django to use our User model everywhere
# ─────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

# ─────────────────────────────────────────────────────────────
# PASSWORD VALIDATION
# ─────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

# ─────────────────────────────────────────────────────────────
# STATIC FILES
# STATIC_ROOT is where `collectstatic` gathers everything for WhiteNoise
# to serve — Railway has no separate Nginx, so Django has to serve its
# own static files (admin CSS etc.) directly via WhiteNoise.
# ─────────────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# default rules applied to every API in our project
# ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # only logged in users can access APIs
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',      # always return JSON not HTML
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication', # use JWT tokens for auth
    ],
}

# ─────────────────────────────────────────────────────────────
# JWT SETTINGS
# controls how long login tokens stay valid
# ─────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(minutes=60), # expires every 60 mins
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # refresh token lasts 7 days
    'ROTATE_REFRESH_TOKENS' : True,                  # gives new refresh token on every refresh
}

# ── Django Channels ───────────────────────
# tells Django to use ASGI instead of WSGI
ASGI_APPLICATION = 'config.asgi.application'

# ── Channel Layer ─────────────────────────
# automatically switches between environments:
# local  → no REDIS_URL in .env → uses InMemory
# production → REDIS_URL in .env → uses Redis
REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG' : {
                'hosts': [REDIS_URL],
            },
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }


# ── Email (development → prints to console/logs, never sends for real) ──
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = 'noreply@discordapp.local'

# ── Frontend URL ──────────────────────────
# used to build links inside emails — change this one value once
# Vercel gives you a real URL, zero other code changes needed.
FRONTEND_URL = config('FRONTEND_URL', default='http://127.0.0.1:8000')


AGORA_APP_ID          = config('AGORA_APP_ID')
AGORA_APP_CERTIFICATE = config('AGORA_APP_CERTIFICATE')

# Comma-separated in .env. Once Vercel gives you a real URL, add it to
# this one env var on Railway and redeploy — no code change needed.
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173',
    cast=Csv()
)

# Same idea — only really matters once the Django admin is hit over
# the real domain. Leave blank locally, fill in once deployed.
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Image Processing 
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB, gives headroom above our 5MB limit
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ─────────────────────────────────────────────────────────────
# PROXY / HTTPS
# Railway terminates HTTPS at its edge and forwards plain HTTP
# internally. Without this, Django thinks every request is insecure
# and CSRF/cookie checks behave wrong. Only applies when DEBUG=False.
# ─────────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
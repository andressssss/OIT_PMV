from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar archivo .env según DJANGO_ENV
env_file = f".env.{os.getenv('DJANGO_ENV', 'dev')}"
env_path = BASE_DIR / env_file
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"¡Advertencia! El archivo {env_file} no se encuentra.")

# Cargar las variables de entorno
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# Ahora DEBUG debería estar correctamente definido después de cargar el .env
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_icons',
    'tasks',
    'usuarios',
    'formacion',
    'gestion_instructores',
    'commons',
    'mptt',
    'matricula',
    'rest_framework',
    'dal',
    'dal_select2',
    'administracion',
    'channels',
    'whitenoise.runserver_nostatic',
    'corsheaders'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'usuarios.middleware.ExpiredSessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'IOTPMV.urls'

TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'commons.context_processors.perfil',
                'commons.context_processors.expiracion_sesion_context'
            ],
        },
    },
]

WSGI_APPLICATION = 'IOTPMV.wsgi.application'
ASGI_APPLICATION = 'IOTPMV.asgi.application'

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = '/signin/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

CORS_ALLOW_ALL_ORIGINS = True

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'correo@ejemplo.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'clave')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DATE_INPUT_FORMATS = ['%d/%m/%Y', '%Y-%m-%d']

DJANGO_ICONS = {
    "ICONS": {
        "edit": {"name": "bi bi-pencil"},
        "plus": {"name": "bi bi-plus-lg"},
        "delete": {"name": "bi bi-trash"},
        "detalle": {"name": "bi bi-box-arrow-up-right"},
        "confirmar": {"name": "bi bi-check-square"},
        "asignarapre": {"name": "bi bi-person-fill-up"},
        "archivo": {"name": "bi bi-file-earmark-spreadsheet"},
        "download": {"name": "bi bi-box-arrow-down"},
        "search": {"name": "bi bi-search"},
        "password": {"name": "bi bi-asterisk"},
        "salir": {"name": "bi bi-box-arrow-right"},
        "perfil": {"name": "bi bi-person-bounding-box"},
        "upload": {"name": "bi bi-upload"},
        "x": {"name": "bi bi-x"},
        "confirm": {"name": "bi bi-check2"},
        "info": {"name": "bi bi-info-square"},
        'hv': {"name": "bi bi-file-earmark-person"},
        'laboral': {"name": "bi bi-briefcase"},
        'academico': {"name": "bi bi-mortarboard"},
        'hojas': {"name": "bi bi-bookshelf"},
        'ficha': {"name": "bi bi-person-video2"},
        'dividir': {"name": "bi bi-file-earmark-break"}
    }
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576000

os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django_error.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

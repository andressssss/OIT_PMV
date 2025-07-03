from .base import *
import os

DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DB_NAME', 'oit_senatic'),
        'USER': os.getenv('DB_USER', 'oit_app'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', 3306),
    }
}

STATIC_URL = os.getenv('STATIC_URL', '/static/')

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)

STATIC_ROOT = os.getenv('STATIC_ROOT', 'staticfiles')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', 'media')

required_env_vars = [
    'DJANGO_SECRET_KEY', 'DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
    'DB_HOST', 'DB_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD'
]

for var in required_env_vars:
    if os.getenv(var) is None:
        raise ValueError(f"Missing required environment variable: {var}")
    

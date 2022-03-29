from .base import *
from os import getenv

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': getenv('LOCAL_DB_NAME', 'snugh'),
        'USER': getenv('LOCAL_DB_USER', 'snugh'),
        'PASSWORD': getenv('LOCAL_DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"'
        }
    },
    'remote': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': getenv('DB_NAME', 'snugh'),
        'USER': getenv('DB_USER', 'snugh'),
        'PASSWORD': getenv('DB_PASSWORD'),
        'HOST': getenv('DB_HOST'),
        'PORT': '3306',
        'OPTIONS': {
            'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"'
        }
    }
}
DEBUG = True
INTERNAL_IPS = [
    "127.0.0.1",
]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INSTALLED_APPS += ["debug_toolbar"]
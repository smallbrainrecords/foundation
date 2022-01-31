import os

from decouple import config

BASE_DIR = os.getcwd()

PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')

COMPRESS_ENABLED = True

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = ['127.0.0.1']

SNOMEDCT = {
    'snomedct': {
        'ssl': {'key': '/path/to/key', 'cert': '/path/to/cert', 'ca': '/path/to/ca'},
        'host': 'host',
        'user': 'user',
        'passwd': 'passwd',
        'db': 'snomedct',
    }
}

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.mysql',
        # Or path to database file if using sqlite3.
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),                      # Not used with sqlite3.
        'PASSWORD': config('DATABASE_PASSWORD', default=''),                  # Not used with sqlite3.
        # Set to empty string for localhost. Not used with sqlite3.
        'HOST': config('DATABASE_HOST'),
        # Set to empty string for default. Not used with sqlite3.
        'PORT': config('DATABASE_PORT'),
        'OPTIONS': {},
        'TEST': {
            'NAME': config('DATABASE_TEST_NAME'),
        },

    }
}

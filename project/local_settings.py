from google.oauth2 import service_account
import os

from decouple import config

BASE_DIR = os.getcwd()

PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')

COMPRESS_ENABLED = True

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = ['*']

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
        # Not used with sqlite3.
        'USER': config('DATABASE_USER'),
        # Not used with sqlite3.
        'PASSWORD': config('DATABASE_PASSWORD'),
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

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = config('GCP_BUCKET_NAME')

gcp_sa_credentials = {
    "type": "service_account",
    "project_id": config('GCP_PROJECT_ID'),
    "private_key_id": config('GCP_PRIVATE_KEY_ID'),
    "private_key": config('GCP_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": config('GCP_CLIENT_EMAIL'),
    "client_id": config('GCP_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": config('GCP_CLIENT_X509_CERT_URL')
}

GS_CREDENTIALS = service_account.Credentials.from_service_account_info(
    gcp_sa_credentials)

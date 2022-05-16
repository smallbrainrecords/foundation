from google.oauth2 import service_account
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.getcwd()

PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')

COMPRESS_ENABLED = True

SECRET_KEY = os.getenv('SECRET_KEY')

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
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'OPTIONS': {},
        'TEST': {
            'NAME': os.getenv('DATABASE_TEST_NAME'),
        },

    }
}

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.getenv('GCP_BUCKET_NAME')

gcp_sa_credentials = {
    "type": "service_account",
    "project_id": os.getenv('GCP_PROJECT_ID'),
    "private_key_id": os.getenv('GCP_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GCP_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('GCP_CLIENT_EMAIL'),
    "client_id": os.getenv('GCP_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('GCP_CLIENT_X509_CERT_URL')
}

GS_CREDENTIALS = service_account.Credentials.from_service_account_info(
    gcp_sa_credentials)

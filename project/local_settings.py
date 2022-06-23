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
    },
    'snomedict': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME_SNOMEDCT'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT')
    }
}

if os.getenv('DATABASE_USE_SSL').lower() == "true":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DATABASE_NAME'),
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST'),
            'PORT': os.getenv('DATABASE_PORT'),
            'OPTIONS': {
                'ssl': {
                    'ca': os.getenv('DATABASE_SSL_CA'),
                    'cert': os.getenv('DATABASE_SSL_CERT'),
                    'key': os.getenv('DATABASE_SSL_KEY'),
                }
            },
            'TEST': {
                'NAME': os.getenv('DATABASE_TEST_NAME'),
            },
        },
        'snomedict': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DATABASE_NAME_SNOMEDCT'),
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST'),
            'PORT': os.getenv('DATABASE_PORT'),
            'OPTIONS': {
                'ssl': {
                    'ca': os.getenv('DATABASE_SSL_CA'),
                    'cert': os.getenv('DATABASE_SSL_CERT'),
                    'key': os.getenv('DATABASE_SSL_KEY'),
                }
            },
        }
    }

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.getenv('GCP_BUCKET_NAME')

GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    os.getenv('GCP_SERVICE_ACCOUNT_PATH'))

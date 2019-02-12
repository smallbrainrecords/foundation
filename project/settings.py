"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import os
import sys

import raven

# Django settings for emr project.

DEBUG = False  # Never set 'DEBUG = True' in production environment
COMPRESS_ENABLED = True

# toggle experimental features
VOICE_CONTROL = False
SYNCING = False

os.environ['LANG'] = 'en_US.UTF-8'
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

APP_PATH = os.path.join(BASE_DIR, 'apps')
sys.path.append(APP_PATH)

AUTH_PROFILE_MODULE = "account.UserProfile"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Detroit'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # os.path.join(BASE_DIR, 'staticdev'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'session_security.middleware.SessionSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'emr.middleware.AccessLogMiddleware',
)

ROOT_URLCONF = 'project.urls'

# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = 'project.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': True
        }
    }
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'mptt',
    'reversion',
    'emr',
    'pain',
    'genericadmin',
    'compressor',
    'cronjobs',
    'session_security',
    'raven.contrib.django.raven_compat',
    'django_crontab',
)

AUTHENTICATION_BACKENDS = (
    #    'social_auth.backends.google.GoogleOAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

# GOOGLE_OAUTH2_CLIENT_ID = ''
# GOOGLE_OAUTH2_CLIENT_SECRET = ''
# GOOGLE_WHITE_LISTED_DOMAINS = []
# SOCIAL_AUTH_USER_MODEL = 'auth.User'
# SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True
SESSION_SECURITY_WARN_AFTER = 1740
SESSION_SECURITY_EXPIRE_AFTER = 1800
SESSION_SECURITY_PASSIVE_URLS = {}

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# LOGIN_URL          = '/login/google-oauth2/'
LOGIN_URL = '/u/login/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL = '/login-error/'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SNOMEDCT = {}

# ###################################################################
# LOCAL SETTINGS FILE IS USED TO IMPORT SENSITIVE CONFIGURATION INFO. 
# MODIFY THE INCLUDED TEMPLATE FOR YOUR OWN PARTICULAR ENVIRONMENT
# ###################################################################

try:
    from local_settings import *
except ImportError as e:
    pass

    # ADMINS = (
    #     ('', ''),('', ''),
    # )
    #    Imported from local_settings.py

    # MANAGERS =
    #    Imported from local_settings.py

    # DATABASES = {
    #
    # }
    #    Imported from local_settings.py

    # Make this unique, and don't share it with anybody.
    # SECRET_KEY = ''   # Imported from local_settings.py

    # ALLOWED_HOSTS = [
    #     '',
    # ]
    #    Imported from local_settings.py

    # SITE_ID =    # Imported from local_settings.py

    # The following is imported from local_settings.py
    # EMAIL_USE_TLS = True
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = ''
    # EMAIL_HOST_PASSWORD = ''
    # EMAIL_HOST_USER = ''
    # EMAIL_PORT = 
    # DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

    # RAVEN_CONFIG = {
    #     'dsn': '',   #Imported from local_settings.py
    #      If you are using git, you can also automatically configure the
    #      release based on the git info.
    # }

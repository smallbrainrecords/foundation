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
import environ

import MySQLdb

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)
# Read from .env file if it exists
environ.Env.read_env(env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env_local'))

# Django settings for emr project.

DEBUG = env('DEBUG', default=True)  # Never set 'DEBUG = True' in production environment
COMPRESS_ENABLED = True

# toggle experimental features
VOICE_CONTROL = False
SYNCING = False

SECRET_KEY = env('SECRET_KEY', default="{~9@e\1VKr|zlM&vl5ZJTOqBX#b!Aa1cv;pN!J\H=cL=<48<|7r4s1Z!U")
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

os.environ["LANG"] = "en_US.UTF-8"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

APP_PATH = os.path.join(BASE_DIR, "apps")
sys.path.append(APP_PATH)

AUTH_PROFILE_MODULE = "account.UserProfile"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "America/Detroit"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

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
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

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
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "session_security.middleware.SessionSecurityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "emr.middleware.AccessLogMiddleware",
)

ROOT_URLCONF = "project.urls"

# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = 'project.wsgi.application'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            ""
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": True,
        },
    }
]

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "mptt",
    "compressor",
    "session_security",
    "raven.contrib.django.raven_compat",
    "django_crontab",
    'emr',
    'apps.analytics_app',
)

CRONJOBS = [
    ("0 0 * * *", "emr.cron.a1c_order_was_automatically_generated"),
    (
        "0 0 * * *",
        "emr.cron.physician_adds_the_same_data_to_the_same_problem_concept_id_more_than_3_times",
    ),
    (
        "0 0 * * *",
        "emr.cron.physician_adds_the_same_medication_to_the_same_problem_concept_id_more_than_3_times",
    ),
    ("0 0 * * *", "emr.cron.problem_relationship_auto_pinning_for_3_times_matched"),
]

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 28800  # 8 hours (full shift)
SESSION_SAVE_EVERY_REQUEST = True  # Reset timeout on every request
SESSION_SECURITY_WARN_AFTER = 28740
SESSION_SECURITY_EXPIRE_AFTER = 28800
SESSION_SECURITY_PASSIVE_URLS = ['/api/']

# CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://10.0.1.8:8000",
    "https://10.0.1.8:8000",
    "http://dev.smallbrainrecords.org",
    "https://dev.smallbrainrecords.org",
    "https://qa.smallbrainrecords.org",
    "https://smallbrainrecords.org",
    "https://sbr-backend-698480968754.us-central1.run.app",
    "https://smallbrain-api-439817011164.us-east5.run.app",
]
INTERNAL_IPS = ("127.0.0.1",)

SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGIN_URL = "/u/login/"
LOGIN_REDIRECT_URL = "/"
LOGIN_ERROR_URL = "/login-error/"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        # Pass-through: mobile_batch_errors already encodes its payload as
        # a single JSON document via json.dumps, and Cloud Run's logging
        # agent auto-parses any stdout line that is valid JSON. Emitting
        # just `%(message)s` keeps that line intact end-to-end.
        "smallbrain_passthrough_json": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "smallbrain_error_reporter_stdout": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "smallbrain_passthrough_json",
        },
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        # Dedicated logger for iOS-relayed errors. `propagate: False` keeps
        # these out of the global mail_admins handler — they're already in
        # Cloud Logging and Cloud Error Reporting groups them automatically.
        "smallbrain.error_reporter": {
            "handlers": ["smallbrain_error_reporter_stdout"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

SNOMEDCT: dict = {}

ALLOWED_HOSTS = ["*"]

# ###################################################################
# LOCAL SETTINGS FILE IS USED TO IMPORT SENSITIVE CONFIGURATION INFO.
# MODIFY THE INCLUDED TEMPLATE FOR YOUR OWN PARTICULAR ENVIRONMENT
# ###################################################################

# Database configuration via django-environ
# GCP Cloud SQL Connection String using the explicit GCP project 'projects/sbr1'
# Format: mysql://user:password@//cloudsql/projects/sbr1:region:instance/dbname
DATABASES = {
    'default': env.db(
        'DATABASE_URL', 
        default='mysql://root:@127.0.0.1:3306/andromeda_redacted'
    ),
    'default_read_uncommitted': env.db(
        'DATABASE_URL', 
        default='mysql://root:@127.0.0.1:3306/andromeda_redacted'
    ),
    'snomedict': env.db(
        'SNOMEDCT_DATABASE_URL',
        default='mysql://root:@127.0.0.1:3306/snomedct'
    )
}

# Apply read uncommitted mapping if the engine is mysql
if DATABASES['default_read_uncommitted']['ENGINE'] == 'django.db.backends.mysql':
    DATABASES['default_read_uncommitted']['OPTIONS'] = {'isolation_level': 'read uncommitted'}

# Static files / Media files for Google Cloud Storage
if env.bool('USE_CLOUD_STORAGE', default=False):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    GS_BUCKET_NAME = env('GS_BUCKET_NAME')
    GS_PROJECT_ID = env('GS_PROJECT_ID', default='openemr-493416')
    GS_QUERYSTRING_AUTH = True


try:
    from project.local_settings import *
except ImportError as e:
    pass


# --- Local dev: disable django-compressor (missing node_modules assets) ---
try:
    DEBUG
except NameError:
    DEBUG = False

if DEBUG:
    COMPRESS_ENABLED = False

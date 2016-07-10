import os

BASE_DIR  = os.getcwd()



PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')


COMPRESS_ENABLED = False

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'sbtest',                      # Or path to database file if using sqlite3.
            'USER': 'root',                      # Not used with sqlite3.
            'PASSWORD': '123',                  # Not used with sqlite3.
            'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }

# DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
#             'NAME': 'sbtest',                      # Or path to database file if using sqlite3.
#             'USER': 'root',                      # Not used with sqlite3.
#             'PASSWORD': 'Volatile0',                  # Not used with sqlite3.
#             'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#             'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#         }
#     }

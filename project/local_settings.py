import os

BASE_DIR  = os.getcwd()



PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')


COMPRESS_ENABLED = False


SNOMEDCT = {
        'snomedct': {
            'ssl': {'key':'/path/to/key','cert':'/path/to/cert','ca':'/path/to/ca'},
            'host':'host',
            'user':'user',
            'passwd':'passwd',
            'db':'snomedct',
         }
}

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'NAME',                      # Or path to database file if using sqlite3.
            'USER': 'USER',                      # Not used with sqlite3.
            'PASSWORD': 'PASSWORD',                  # Not used with sqlite3.
            'HOST': 'HOST',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': 'PORT',                      # Set to empty string for default. Not used with sqlite3.
            'OPTIONS': {'ssl':{'key':'/path/to/key','cert':'/path/to/cert','ca':'/path/to/ca'}},
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

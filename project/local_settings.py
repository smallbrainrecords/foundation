import os

BASE_DIR  = os.getcwd()



PROBLEMS_PATH = os.path.join(BASE_DIR, 'static/js/problems')


COMPRESS_ENABLED = False


SNOMEDCT = {
        'snomedct': {
            'ssl': {'key':'/home/kevin_perdue/client-key.pem','cert':'/home/kevin_perdue/client-cert.pem','ca':'/home/kevin_perdue/server-ca.pem'},
            'host':'104.198.68.134',
            'user':'smallbrain_app',
            'passwd':'Waukap00k@-21-6',
            'db':'snomedct',
         }
}

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'vestalbeast',                      # Or path to database file if using sqlite3.
            'USER': 'smallbrain_app',                      # Not used with sqlite3.
            'PASSWORD': 'Waukap00k@-21-6',                  # Not used with sqlite3.
            'HOST': '104.198.68.134',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
            'OPTIONS': {'ssl':{'key':'/home/kevin_perdue/client-key.pem','cert':'/home/kevin_perdue/client-cert.pem','ca':'/home/kevin_perdue/server-ca.pem'}},
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

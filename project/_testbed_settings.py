# Local test-bed settings: run Django against the locally-imported prod copy
# (`smallbrain2` on Homebrew MySQL :3306, root / no password).
#   Refresh the copy : scripts/refresh_testdb.sh
#   Run the server   : scripts/run_testbed.sh
# Inherits everything from project.settings — including local_settings, which
# replaces the whole DATABASES dict (dropping the snomedict alias) — and then
# repoints every alias at the local MySQL.
from project.settings import *  # noqa: F401,F403

_LOCAL = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'smallbrain2',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': '127.0.0.1',
    'PORT': '3306',
}

DATABASES = {
    'default': dict(_LOCAL),
    # Base settings defines this alias (no app code reads it today) and
    # local_settings wipes it — keep it resolvable so nothing KeyErrors.
    'default_read_uncommitted': dict(_LOCAL),
    # SNOMED term search does .using('snomedict') (emr/views.py:408); point it
    # at the local snomedct import so search/validate work on the test bed.
    'snomedict': dict(_LOCAL, NAME='snomedct'),
}

# Hard guard: never touch prod GCS from the test bed, even if
# USE_CLOUD_STORAGE=true leaks in from the shell environment.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

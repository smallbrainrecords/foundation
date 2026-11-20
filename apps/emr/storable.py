"""Two things the database connection and the file storage do not do for
us in production, found 2026-11-18. Use these instead of the obvious calls.

`storable_text`: Django connects to MySQL as three-byte `utf8` (its default
"charset"; DATABASE_URL sets none), and that connection refuses four-byte
UTF-8 (error 1366 "Incorrect string value") whatever the column allows. One
emoji read off a fax page (document 52269, U+1F642) made that document's text
upload answer 500 about 3,000 times in a week, from every Mac that held it.
Text a Mac sends for a document passes through this first.

`stored_file_exists`: django-storages' GoogleCloudStorage.exists() answers
False whenever `file_overwrite` is on, the default (a save-time shortcut, not
a check; `audit_encounter_audio` noted it in 2026-09). So every request for a
fax as received (`/api/fax/review/<id>/original`) and every document restore
was refused in production while the tests, on local file storage, passed.
`size()` asks the bucket and raises when the object is missing.
"""
import re

from django.core.files.storage import default_storage

try:
    from google.cloud.exceptions import NotFound as _BucketNotFound
except Exception:  # the Google client is not installed (local runs)
    class _BucketNotFound(Exception):
        pass

# Characters a three-byte utf8 connection cannot carry: everything outside the
# Basic Multilingual Plane, and lone surrogates (never valid UTF-8).
_UNSTORABLE = re.compile('[\U00010000-\U0010FFFF\ud800-\udfff]')

REPLACEMENT = '�'


def storable_text(value):
    """`value` with each character the database connection would refuse
    replaced by U+FFFD. Anything that is not a string comes back as it is."""
    if not isinstance(value, str):
        return value
    return _UNSTORABLE.sub(REPLACEMENT, value)


def stored_file_exists(name, storage=None):
    """Whether `name` is really in `storage` (default storage when None).
    A storage error other than "not found" is raised, never read as missing."""
    if not name:
        return False
    storage = storage or default_storage
    try:
        storage.size(name)
    except (FileNotFoundError, _BucketNotFound):
        return False
    return True


def document_files(doc):
    """Every stored file that belongs to `doc`: its current file, each file a
    PDF edit replaced or brought back, and the fax as received that page
    removal keeps (2026-11-18). Collect them BEFORE the row is deleted; the
    edit and review rows go with it."""
    from emr.models import DocumentEdit, DocumentReview
    files = set()
    if doc.document:
        files.add(doc.document.name)
    for edit in DocumentEdit.objects.filter(document=doc):
        files.update(name for name in (edit.previous_file, edit.new_file) if name)
    review = DocumentReview.objects.filter(document=doc).first()
    if review is not None and review.original_file:
        files.add(review.original_file)
    return files


def delete_stored_files(names, storage=None):
    """Deletes each of `names`; answers how many could not be deleted. A
    missing file is not an error (GCS and local storage both pass)."""
    storage = storage or default_storage
    failed = 0
    for name in names:
        try:
            storage.delete(name)
        except Exception:
            failed += 1
    return failed


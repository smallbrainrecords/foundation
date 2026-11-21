"""Replaced profile photos are kept (owner request 2026-11-20: "ensure that
when a user's profile photo is updated the old photos are stored").

`UserProfile.save()` calls `keep_replaced_portrait` before it writes. When
the save is about to change `portrait_image`, the photo it replaces is
COPIED into a `PortraitHistory` row under its own random key, then the save
goes ahead. So every writer is covered without remembering to: the check-in
iPad's apply (the only path the app has today), the Django admin, and the
retired web forms.

Why a copy rather than a pointer to the old object: the retired web forms
named an upload after the user's own file (`cover_image/photo.jpg`), and
GCS overwrites by default, so a later upload of another "photo.jpg" would
have replaced the bytes a pointer named. The copy's key is random and no
profile write can reach it.

If the old photo cannot be read for any reason but "it is not there", the
error is raised and the save does not happen: the photo is never replaced
unless the old one was kept first. An old file already missing from
storage is recorded with an empty `image`, its name kept.

`set_new_portrait` is how a route sets a new photo and says who did it and
from where; a save without it is recorded as source `unknown`, no actor.
"""
import json
import logging
import os
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from emr.storable import _BucketNotFound

LOGGER = logging.getLogger('smallbrain.portrait_history')


def is_real_photo_name(name):
    """False for no photo and for the legacy default avatar (a static path
    stored as the field's value)."""
    return bool(name) and not name.startswith('/static/')


def set_new_portrait(profile, data, *, actor, source, extension='.jpg'):
    """Writes `data` as `profile`'s photo under a fresh random name (a fixed
    name would put every patient's photo in one object) and notes who
    replaced the old one and from where. The caller saves `profile`; that
    save keeps the photo it replaces."""
    profile._portrait_replaced_by = actor
    profile._portrait_source = source
    profile.portrait_image.save(
        'portrait-%s%s' % (uuid.uuid4(), extension), ContentFile(data), save=False)


def _changing(profile, old_name):
    field = profile.portrait_image
    if not getattr(field, '_committed', True):
        return True  # a new upload assigned to the field, not yet written
    return (field.name or '') != old_name


def keep_replaced_portrait(profile):
    """Copies the photo `profile` is about to replace into PortraitHistory.
    Answers the new row, or None when the save does not replace a photo."""
    from emr.models import PortraitHistory, UserProfile
    old_name = (UserProfile.objects.filter(pk=profile.pk)
                .values_list('portrait_image', flat=True).first())
    if not is_real_photo_name(old_name) or not _changing(profile, old_name):
        return None
    actor = getattr(profile, '_portrait_replaced_by', None)
    if getattr(actor, 'pk', None) is None:
        actor = None
    source = getattr(profile, '_portrait_source', None) or PortraitHistory.SOURCE_UNKNOWN
    try:
        with default_storage.open(old_name, 'rb') as handle:
            data = handle.read()
    except (FileNotFoundError, _BucketNotFound):
        data = None
    row = PortraitHistory(user_id=profile.user_id, original_name=old_name[:255],
                          replaced_by=actor, source=source)
    if data is not None:
        row.image.save('kept%s' % os.path.splitext(old_name)[1], ContentFile(data), save=False)
    row.save()
    # Said once: a later replacement through this same object is its own.
    for attr in ('_portrait_replaced_by', '_portrait_source'):
        if hasattr(profile, attr):
            delattr(profile, attr)
    LOGGER.info(json.dumps({
        'event': 'portrait_kept', 'user_id': profile.user_id, 'history_id': row.id,
        'source': source, 'actor_id': actor.pk if actor else None, 'copied': data is not None,
    }))
    return row

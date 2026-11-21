"""Replaced profile photos are kept (2026-11-20). emr.portrait_history and
UserProfile.save()."""
import io
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from emr.models import PortraitHistory, UserProfile
from emr.portrait_history import set_new_portrait


def _jpeg(color):
    from PIL import Image
    out = io.BytesIO()
    Image.new('RGB', (8, 8), color).save(out, format='JPEG')
    return out.getvalue()


RED, GREEN, BLUE = _jpeg((255, 0, 0)), _jpeg((0, 255, 0)), _jpeg((0, 0, 255))


class PortraitHistoryTests(TestCase):

    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)
        self.patient = User.objects.create_user(username='pt_photo', password='x')
        self.profile = UserProfile.objects.create(user=self.patient, role='patient')
        self.nurse = User.objects.create_user(username='nurse_photo', password='x')
        UserProfile.objects.create(user=self.nurse, role='nurse')

    def _set(self, data, actor=None, source='check_in'):
        profile = UserProfile.objects.get(pk=self.profile.pk)
        set_new_portrait(profile, data, actor=actor, source=source)
        profile.save()
        return profile

    def _read(self, field_file):
        with default_storage.open(field_file.name, 'rb') as handle:
            return handle.read()

    def test_a_first_photo_and_the_default_avatar_leave_no_history(self):
        # The legacy default avatar is a static path stored as the value.
        self.assertEqual(self.profile.portrait_image.name, '/static/images/avatar.png')
        self._set(RED)
        self.assertEqual(PortraitHistory.objects.count(), 0)
        UserProfile.objects.filter(pk=self.profile.pk).update(portrait_image='')
        self._set(GREEN)
        self.assertEqual(PortraitHistory.objects.count(), 0)

    def test_replacing_a_photo_keeps_a_copy_of_the_old_one(self):
        first = self._set(RED, actor=self.nurse)
        old_name = first.portrait_image.name
        second = self._set(GREEN, actor=self.nurse, source='check_in')
        row = PortraitHistory.objects.get()
        self.assertEqual(row.user, self.patient)
        self.assertEqual(row.original_name, old_name)
        self.assertEqual(row.replaced_by, self.nurse)
        self.assertEqual(row.source, 'check_in')
        self.assertTrue(row.image.name.startswith('portrait_history/'))
        self.assertNotEqual(row.image.name, old_name)
        self.assertNotIn('pt_photo', row.image.name)
        self.assertEqual(self._read(row.image), RED)
        self.assertEqual(self._read(second.portrait_image), GREEN)

    def test_every_replacement_is_kept_in_order(self):
        self._set(RED)
        self._set(GREEN)
        self._set(BLUE)
        rows = list(PortraitHistory.objects.filter(user=self.patient).order_by('replaced_at', 'id'))
        self.assertEqual([self._read(r.image) for r in rows], [RED, GREEN])

    def test_a_save_that_does_not_change_the_photo_keeps_nothing(self):
        profile = self._set(RED)
        profile.summary = 'Likes gardening'
        profile.save()
        UserProfile.objects.get(pk=profile.pk).save(update_fields=['summary'])
        self.assertEqual(PortraitHistory.objects.count(), 0)

    def test_a_save_without_the_portrait_field_asks_nothing(self):
        self._set(RED)
        profile = UserProfile.objects.get(pk=self.profile.pk)
        with mock.patch('emr.portrait_history.keep_replaced_portrait') as keep:
            profile.save(update_fields=['summary'])
        keep.assert_not_called()

    def test_an_upload_assigned_to_the_field_is_covered(self):
        # The admin and the retired web forms assign an upload named after
        # the user's file; nobody says who or why.
        self._set(RED)
        profile = UserProfile.objects.get(pk=self.profile.pk)
        profile.portrait_image = SimpleUploadedFile('photo.jpg', GREEN, content_type='image/jpeg')
        profile.save()
        row = PortraitHistory.objects.get()
        self.assertEqual((row.source, row.replaced_by), ('unknown', None))
        self.assertEqual(self._read(row.image), RED)

    def test_who_and_where_are_said_once(self):
        profile = UserProfile.objects.get(pk=self.profile.pk)
        set_new_portrait(profile, RED, actor=self.nurse, source='check_in')
        profile.save()
        set_new_portrait(profile, GREEN, actor=self.nurse, source='check_in')
        profile.save()
        profile.portrait_image = SimpleUploadedFile('p.jpg', BLUE, content_type='image/jpeg')
        profile.save()
        rows = list(PortraitHistory.objects.order_by('id'))
        self.assertEqual([(r.source, r.replaced_by) for r in rows],
                         [('check_in', self.nurse), ('unknown', None)])

    def test_clearing_the_photo_keeps_the_old_one(self):
        self._set(RED)
        profile = UserProfile.objects.get(pk=self.profile.pk)
        profile.portrait_image = ''
        profile.save()
        self.assertEqual(self._read(PortraitHistory.objects.get().image), RED)

    def test_an_old_photo_already_missing_is_recorded_by_name(self):
        profile = self._set(RED)
        old_name = profile.portrait_image.name
        default_storage.delete(old_name)
        self._set(GREEN)
        row = PortraitHistory.objects.get()
        self.assertEqual(row.original_name, old_name)
        self.assertFalse(row.image)

    def test_a_storage_failure_replaces_nothing(self):
        profile = self._set(RED)
        old_name = profile.portrait_image.name
        profile = UserProfile.objects.get(pk=profile.pk)
        set_new_portrait(profile, GREEN, actor=None, source='check_in')
        with mock.patch('emr.portrait_history.default_storage.open', side_effect=RuntimeError('bucket down')):
            with self.assertRaises(RuntimeError):
                profile.save()
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).portrait_image.name, old_name)
        self.assertEqual(PortraitHistory.objects.count(), 0)

    def test_the_kept_copy_survives_the_old_name_being_reused(self):
        # GCS overwrites by default: a later write to the old key must not
        # reach the history.
        profile = self._set(RED)
        old_name = profile.portrait_image.name
        self._set(GREEN)
        default_storage.delete(old_name)
        default_storage.save(old_name, ContentFile(BLUE))
        self.assertEqual(self._read(PortraitHistory.objects.get().image), RED)

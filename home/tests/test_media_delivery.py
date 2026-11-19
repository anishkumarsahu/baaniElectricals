import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class MediaDeliveryTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'media'
        (self.root / 'photo').mkdir(parents=True)
        (self.root / 'photo' / 'test image.png').write_bytes(b'image data')
        self.settings_override = override_settings(MEDIA_ROOT=self.root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.user = User.objects.create_user(username='media-user', password='test-password')

    def test_session_can_read_existing_and_new_uploads(self):
        self.client.force_login(self.user)
        for name in ('test image.png', 'new.png'):
            (self.root / 'photo' / name).write_bytes(b'image data')
            response = self.client.get('/media/photo/' + name)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response['Content-Disposition'].startswith('inline'))
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(b''.join(response.streaming_content), b'image data')
            response.close()
        response = self.client.head('/media/photo/test%20image.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'')
        response.close()

    def test_anonymous_missing_hidden_and_escape_denied(self):
        self.assertEqual(self.client.get('/media/photo/test%20image.png').status_code, 403)
        self.client.force_login(self.user)
        outside = Path(self.directory.name) / 'secret.txt'
        outside.write_text('private')
        (self.root / 'escape.txt').symlink_to(outside)
        (self.root / '.hidden').write_text('private')
        for path in ('missing.png', 'photo/', '../secret.txt', '%2e%2e/secret.txt', '.hidden', 'escape.txt'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get('/media/' + path).status_code, 404)

    def test_active_content_downloads_and_writes_are_rejected(self):
        self.client.force_login(self.user)
        (self.root / 'test.html').write_text('<script>alert(1)</script>')
        response = self.client.get('/media/test.html')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
        self.assertIn('sandbox', response['Content-Security-Policy'])
        response.close()
        self.assertEqual(self.client.post('/media/test.html').status_code, 405)

from unittest.mock import patch

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class ErrorPageTests(SimpleTestCase):
    def test_invalid_host_returns_custom_bad_request_page(self):
        response = self.client.get(reverse('healthz'), HTTP_HOST='invalid.example')

        self.assertContains(response, '<h1 id="heading">Invalid request</h1>', status_code=400, html=True)

    def test_unmatched_url_returns_custom_not_found_page(self):
        response = self.client.get('/missing-page/')

        self.assertContains(response, 'Page not found', status_code=404)
        self.assertContains(response, f'href="{reverse("homeApp:loginPage")}"', status_code=404)

    def test_rejected_form_returns_custom_csrf_page(self):
        response = Client(enforce_csrf_checks=True).post(reverse('admin:login'))

        self.assertContains(response, 'Please reopen the form', status_code=403)

    def test_unhandled_exception_returns_custom_server_error_page(self):
        client = Client(raise_request_exception=False)
        with patch('baani.urls.JsonResponse', side_effect=RuntimeError('internal exception detail')):
            response = client.get(reverse('healthz'))

        self.assertContains(response, 'Something went wrong', status_code=500)
        self.assertNotContains(response, 'internal exception detail', status_code=500)

import datetime

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from activation.models import EcomValidity, Validity
from activation.views import is_activated, is_ecom_activated


class ActivationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.today = datetime.date.today()

    def test_validity_string_representation(self):
        val = Validity.objects.create(
            activationDate=self.today,
            expiryDate=self.today + datetime.timedelta(days=365),
            activationType="Enterprise"
        )
        expected = f"{val.activationDate}  -  {val.expiryDate}"
        self.assertEqual(str(val), expected)

    def test_ecom_validity_string_representation(self):
        ecom = EcomValidity.objects.create(
            activationDate=self.today,
            expiryDate=self.today + datetime.timedelta(days=180),
            activationType="Standard"
        )
        expected = f"{ecom.activationDate}  -  {ecom.expiryDate}"
        self.assertEqual(str(ecom), expected)

    def test_activate_view_renders(self):
        response = self.client.get('/activate/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activation/activate.html')

    def test_is_activated_when_no_records_exist(self):
        @is_activated()
        def dummy_view(request):
            return HttpResponse("OK")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_is_activated_when_valid(self):
        Validity.objects.create(
            activationDate=self.today - datetime.timedelta(days=10),
            expiryDate=self.today + datetime.timedelta(days=30),
            activationType="Pro"
        )

        @is_activated()
        def dummy_view(request):
            return HttpResponse("ACTIVE")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "ACTIVE")

    def test_is_activated_when_expired(self):
        Validity.objects.create(
            activationDate=self.today - datetime.timedelta(days=40),
            expiryDate=self.today - datetime.timedelta(days=1),
            activationType="Pro"
        )

        @is_activated()
        def dummy_view(request):
            return HttpResponse("EXPIRED")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/activate/')

    def test_is_ecom_activated_when_no_records_exist(self):
        @is_ecom_activated()
        def dummy_view(request):
            return HttpResponse("ECOM_OK")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "ECOM_OK")

    def test_is_ecom_activated_when_valid(self):
        EcomValidity.objects.create(
            activationDate=self.today - datetime.timedelta(days=5),
            expiryDate=self.today + datetime.timedelta(days=60),
            activationType="Online"
        )

        @is_ecom_activated()
        def dummy_view(request):
            return HttpResponse("ECOM_ACTIVE")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "ECOM_ACTIVE")

    def test_is_ecom_activated_when_expired(self):
        EcomValidity.objects.create(
            activationDate=self.today - datetime.timedelta(days=20),
            expiryDate=self.today - datetime.timedelta(days=2),
            activationType="Online"
        )

        @is_ecom_activated()
        def dummy_view(request):
            return HttpResponse("ECOM_EXPIRED")

        request = self.factory.get('/test/')
        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/activate/')

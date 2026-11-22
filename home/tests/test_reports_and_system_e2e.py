import datetime

from home.models import Collection, PartyGroup, Sales
from home.tests.base import BaseTestCase


class ReportsAndSystemIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for:
    - Financial & operations reporting endpoints (Collection, Sales, Cash Counter reports)
    - Admin and Staff operational dashboard aggregates
    - Core system healthcheck (/healthz) and PWA endpoints (/serviceworker.js, /manifest.json)
    - View routing and template rendering integrity
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_rep", "Pass123!", "Admin")
        self.coll_user, self.coll_staff = self.create_staff("coll_rep", "Pass123!", "Collection")
        self.party_group = PartyGroup.objects.create(name="Eastern Division")
        self.party = self.create_party("Eastern Electricals", "9876500000", self.party_group, assign_to=self.coll_staff)

    def test_healthz_endpoint(self):
        resp = self.client.get('/healthz')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_pwa_endpoints(self):
        sw_resp = self.client.get('/serviceworker.js')
        self.assertEqual(sw_resp.status_code, 200)

        manifest_resp = self.client.get('/manifest.json')
        self.assertEqual(manifest_resp.status_code, 200)

    def test_admin_dashboard_report_api(self):
        self.client.force_login(self.admin_user)

        # Seed collection and sales for today
        Collection.objects.create(
            partyID=self.party,
            paymentID="P00000201",
            modeOfPayment="Cash",
            paidAmount=10000.0,
            collectedBy=self.coll_staff,
            collectionDateTime=datetime.datetime.now(),
            isApproved=True
        )
        Sales.objects.create(
            partyID=self.party,
            paymentID="S00000201",
            invoiceNumber="BSSAC/901/26-27",
            amount=25000.0,
            createdBy=self.admin_staff,
            buildDate=self.today
        )

        resp = self.client.get('/api/get_admin_dashboard_report_api/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('data', {})
        self.assertIn('partyCount', data)
        self.assertIn('staffCount', data)
        self.assertIn('collection', data)
        self.assertIn('Sale', data)

    def test_staff_dashboard_report_api(self):
        self.client.force_login(self.coll_user)

        Collection.objects.create(
            partyID=self.party,
            paymentID="P00000202",
            modeOfPayment="Cash",
            paidAmount=5000.0,
            collectedBy=self.coll_staff,
            collectionDateTime=datetime.datetime.now(),
            isApproved=True
        )

        resp = self.client.get('/api/get_staff_dashboard_report_api/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('data', {})
        self.assertIn('collection_total', data)
        self.assertIn('collection', data)

    def test_generate_collection_report_e2e(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        Collection.objects.create(
            partyID=self.party,
            paymentID="P00000203",
            modeOfPayment="Cash",
            paidAmount=7000.0,
            collectedBy=self.coll_staff,
            collectionDateTime=datetime.datetime.now(),
            isApproved=True
        )

        # 1. Report for All Staff
        resp_all = self.client.get(f'/api/generate_collection_report/?cDate={col_date_str}&staffID=All')
        self.assertEqual(resp_all.status_code, 200)

        # 2. Report for Specific Staff
        resp_staff = self.client.get(f'/api/generate_collection_report/?cDate={col_date_str}&staffID={self.coll_staff.pk}')
        self.assertEqual(resp_staff.status_code, 200)

    def test_generate_sales_report_e2e(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        Sales.objects.create(
            partyID=self.party,
            paymentID="S00000204",
            invoiceNumber="BSSAC/902/26-27",
            amount=18000.0,
            createdBy=self.coll_staff,
            buildDate=self.today
        )

        # 1. All Staff
        resp_all = self.client.get(f'/api/generate_sales_report/?cDate={col_date_str}&staffID=All')
        self.assertEqual(resp_all.status_code, 200)

        # 2. Specific Staff
        resp_staff = self.client.get(f'/api/generate_sales_report/?cDate={col_date_str}&staffID={self.coll_staff.pk}')
        self.assertEqual(resp_staff.status_code, 200)

    def test_generate_cash_counter_report_e2e(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        resp = self.client.get(f'/api/generate_cash_counter_report/?cDate={col_date_str}&staffID=All')
        self.assertEqual(resp.status_code, 200)

    def test_admin_navigation_pages_render(self):
        self.client.force_login(self.admin_user)

        endpoints = [
            '/admin_home/',
            '/user_list/',
            '/party_group_list/',
            '/bank_list/',
            '/party_list/',
            '/sales_list/',
            '/collection_list/',
            '/cheque_reminder_list/',
            '/my_profile/',
        ]

        for url in endpoints:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)

    def test_collection_navigation_pages_render(self):
        self.client.force_login(self.coll_user)

        endpoints = [
            '/collection_home/',
            '/my_collection/',
            '/myProfile/',
        ]

        for url in endpoints:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)

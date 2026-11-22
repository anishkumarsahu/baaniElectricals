from home.models import PartyGroup, Sales
from home.tests.base import BaseTestCase


class SalesIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for Sales & Billing:
    - Creation of Sales with 26-27 FY invoice numbering format
    - SalesAdmin and Admin role edit/update permissions
    - Soft-deletion invariant (never hard deleted)
    - Sales dispatch notification queuing
    - DataTables JSON endpoints
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_sales", "Pass123!", "Admin")
        self.sales_admin_user, self.sales_admin_staff = self.create_staff("sales_mgr", "Pass123!", "SalesAdmin")
        self.party_group = PartyGroup.objects.create(name="Project Contractors")
        self.party = self.create_party("Apex Infra Projects", "9830011223", self.party_group, assign_to=self.sales_admin_staff)

    def test_add_sales_invoice_with_fiscal_year_26_27_format(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        resp = self.client.post('/api/add_sales_by_admin_api/', {
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '501',
            'invoiceYearSelect': '26-27',
            'colDate': col_date_str,
            'party': f"{self.party.name}@{self.party.pk}",
            'amount': '84500.0',
            'remark': 'Switchgear control panel delivery'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        sale = Sales.objects.filter(partyID=self.party).latest('id')
        self.assertEqual(sale.invoiceNumber, 'BSSAC/501/26-27')
        self.assertEqual(sale.amount, 84500.0)
        self.assertEqual(sale.createdBy, self.admin_staff)
        self.assertEqual(sale.buildDate, self.today)
        self.assertTrue(sale.paymentID.startswith('S'))
        self.assertFalse(sale.isDeleted)

    def test_sales_admin_can_update_sales_record(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        # Create initial record
        sale = Sales.objects.create(
            partyID=self.party,
            paymentID="S00000001",
            invoiceNumber="BSSAC/202/26-27",
            amount=50000.0,
            remark="Initial booking",
            createdBy=self.admin_staff,
            buildDate=self.today
        )

        # Switch to SalesAdmin user and perform update
        self.client.force_login(self.sales_admin_user)
        update_resp = self.client.post('/api/update_sales_by_admin_api/', {
            'ID': str(sale.pk),
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '202-A',
            'invoiceYearSelect': '26-27',
            'colDate': col_date_str,
            'party': str(self.party.pk),
            'amount': '53200.0',
            'remark': 'Revised with transport freight charge'
        })
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json(), {'message': 'success'})

        sale.refresh_from_db()
        self.assertEqual(sale.invoiceNumber, 'BSSAC/202-A/26-27')
        self.assertEqual(sale.amount, 53200.0)
        self.assertEqual(sale.remark, 'Revised with transport freight charge')

    def test_sales_soft_deletion_invariant(self):
        sale = Sales.objects.create(
            partyID=self.party,
            paymentID="S00000002",
            invoiceNumber="BSSAC/303/26-27",
            amount=15000.0,
            createdBy=self.admin_staff,
            buildDate=self.today
        )

        self.client.force_login(self.admin_user)
        del_resp = self.client.post('/api/delete_sales/', {
            'userID': str(sale.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})

        sale.refresh_from_db()
        self.assertTrue(sale.isDeleted)
        # Ensure row remains in database for accounting audit
        self.assertTrue(Sales.objects.filter(pk=sale.pk).exists())

    def test_send_message_sales_dispatch_trigger(self):
        sale = Sales.objects.create(
            partyID=self.party,
            paymentID="S00000003",
            invoiceNumber="BSSAC/404/26-27",
            amount=22000.0,
            createdBy=self.admin_staff,
            buildDate=self.today,
            isApproved=False
        )

        self.client.force_login(self.admin_user)
        resp = self.client.post('/api/send_message_sales/', {
            'userID': str(sale.pk)
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        sale.refresh_from_db()
        self.assertTrue(sale.isApproved)
        self.assertEqual(sale.approvedBy, self.admin_staff)
        self.mock_send_msg.assert_called()

    def test_sales_datatables_json_views(self):
        Sales.objects.create(
            partyID=self.party,
            paymentID="S00000004",
            invoiceNumber="BSSAC/505/26-27",
            amount=10000.0,
            createdBy=self.admin_staff,
            buildDate=self.today
        )

        self.client.force_login(self.admin_user)
        admin_dt = self.client.get('/api/SalesByAdminListJson/')
        self.assertEqual(admin_dt.status_code, 200)

        self.client.force_login(self.sales_admin_user)
        staff_dt = self.client.get('/api/SalesByStaffListJson/')
        self.assertEqual(staff_dt.status_code, 200)

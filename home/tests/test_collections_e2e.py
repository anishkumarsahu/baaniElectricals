import datetime

from home.models import Collection, PartyGroup
from home.tests.base import BaseTestCase


class CollectionIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for Field Collections:
    - Staff collection entry (Cash, Cheque, Transfer) with GPS tracking
    - Admin collection entry & updates
    - Managerial approval workflow with payment receipt triggers
    - Soft-deletion invariants
    - DataTables JSON endpoints and Cheque reminder tracking
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_collector", "Pass123!", "Admin")
        self.staff_user, self.staff_profile = self.create_staff("field_collector", "Pass123!", "Collection")
        self.bank = self.create_bank("Punjab National Bank", "PNB0009876543")

        self.party_group = PartyGroup.objects.create(name="Authorized Dealers")
        self.party = self.create_party("Sharma Lighting Store", "9876543210", self.party_group, assign_to=self.staff_profile)
        self.transfer_party = self.create_party("Verma Electrical Works", "9123456780", self.party_group)

    def test_staff_add_collection_cash_e2e(self):
        self.client.force_login(self.staff_user)

        resp = self.client.post('/api/add_collection_by_staff_api/', {
            'party': f"{self.party.name}@{self.party.pk}",
            'paymentMode': 'Cash',
            'amountPaid': '15000.0',
            'bank': '',
            'detail': 'Cash received on counter delivery',
            'remark': 'Clean notes verified',
            'lat': '22.5726',
            'lng': '88.3639',
            'chequeDate': ''
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        collection = Collection.objects.filter(partyID=self.party).latest('id')
        self.assertEqual(collection.paidAmount, 15000.0)
        self.assertEqual(collection.modeOfPayment, 'Cash')
        self.assertEqual(collection.collectedBy, self.staff_profile)
        self.assertEqual(collection.latitude, '22.5726')
        self.assertEqual(collection.longitude, '88.3639')
        self.assertFalse(collection.isApproved)
        self.assertFalse(collection.isTallied)
        self.assertFalse(collection.isDeleted)
        self.assertEqual(len(collection.paymentID), 8)
        self.assertTrue(collection.paymentID.isdigit())

    def test_staff_add_collection_cheque_e2e(self):
        self.client.force_login(self.staff_user)

        cheque_date_str = (self.today + datetime.timedelta(days=7)).strftime('%d/%m/%Y')
        resp = self.client.post('/api/add_collection_by_staff_api/', {
            'party': f"{self.party.name}@{self.party.pk}",
            'paymentMode': 'Cheque',
            'amountPaid': '45000.0',
            'bank': str(self.bank.pk),
            'detail': 'Cheque No. 405928',
            'remark': 'Post-dated cheque for invoice clearing',
            'lat': '22.5800',
            'lng': '88.3700',
            'chequeDate': cheque_date_str
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        collection = Collection.objects.filter(partyID=self.party, modeOfPayment='Cheque').latest('id')
        self.assertEqual(collection.paidAmount, 45000.0)
        self.assertEqual(collection.bankID, self.bank)
        self.assertEqual(collection.chequeDate, self.today + datetime.timedelta(days=7))

    def test_admin_add_and_edit_collection_e2e(self):
        self.client.force_login(self.admin_user)
        col_date_str = self.today.strftime('%d/%m/%Y')

        # 1. Admin Add Collection
        resp = self.client.post('/api/add_collection_by_admin_api/', {
            'party': f"{self.party.name}@{self.party.pk}",
            'paymentMode': 'Online',
            'amountPaid': '25000.0',
            'bank': str(self.bank.pk),
            'detail': 'NEFT Ref UTR9988776655',
            'remark': 'Direct RTGS to account',
            'lat': '0.0',
            'lng': '0.0',
            'chequeDate': '',
            'collectDate': col_date_str
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        collection = Collection.objects.filter(partyID=self.party, modeOfPayment='Online').latest('id')
        self.assertEqual(collection.paidAmount, 25000.0)

        # 2. Admin Edit Collection
        edit_resp = self.client.post('/api/edit_collection_by_admin_api/', {
            'ID': str(collection.pk),
            'cDate': col_date_str,
            'party': str(self.party.pk),
            'paymentMode': 'Online',
            'amountPaid': '26500.0',
            'bank': str(self.bank.pk),
            'detail': 'NEFT Ref UTR9988776655 (Revised)',
            'remark': 'Adjusted for GST rounding',
            'chequeDate': ''
        })
        self.assertEqual(edit_resp.status_code, 200)
        self.assertEqual(edit_resp.json(), {'message': 'success'})

        collection.refresh_from_db()
        self.assertEqual(collection.paidAmount, 26500.0)
        self.assertEqual(collection.remark, 'Adjusted for GST rounding')

    def test_collection_approval_workflow_and_receipt_trigger(self):
        # Create unapproved collection
        collection = Collection.objects.create(
            partyID=self.party,
            paymentID="P00000099",
            modeOfPayment="Cash",
            paidAmount=12000.0,
            collectedBy=self.staff_profile,
            collectionDateTime=datetime.datetime.now(),
            isApproved=False
        )

        self.client.force_login(self.admin_user)
        approve_resp = self.client.post('/api/approve_collection/', {
            'userID': str(collection.pk)
        })
        self.assertEqual(approve_resp.status_code, 200)
        self.assertEqual(approve_resp.json(), {'message': 'success'})

        collection.refresh_from_db()
        self.assertTrue(collection.isApproved)
        self.assertEqual(collection.approvedBy, self.admin_staff)
        # Verify receipt dispatch was triggered
        self.mock_send_msg.assert_called()

    def test_collection_soft_delete_invariant(self):
        collection = Collection.objects.create(
            partyID=self.party,
            paymentID="P00000100",
            modeOfPayment="Cash",
            paidAmount=5000.0,
            collectedBy=self.staff_profile,
            collectionDateTime=datetime.datetime.now()
        )

        self.client.force_login(self.admin_user)
        del_resp = self.client.post('/api/delete_collection/', {
            'userID': str(collection.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})

        collection.refresh_from_db()
        self.assertTrue(collection.isDeleted)
        # Record must NEVER be hard deleted
        self.assertTrue(Collection.objects.filter(pk=collection.pk).exists())

    def test_collection_datatables_json_views(self):
        # Create an approved and an unapproved collection for today
        Collection.objects.create(
            partyID=self.party,
            paymentID="P00000101",
            modeOfPayment="Cash",
            paidAmount=8000.0,
            collectedBy=self.staff_profile,
            collectionDateTime=datetime.datetime.now(),
            isApproved=True
        )

        self.client.force_login(self.admin_user)
        resp_admin = self.client.get('/api/CollectionByAdminListJson/')
        self.assertEqual(resp_admin.status_code, 200)

        self.client.force_login(self.staff_user)
        resp_staff = self.client.get('/api/CollectionByStaffListJson/')
        self.assertEqual(resp_staff.status_code, 200)

        # Cheque reminder list
        resp_cheque = self.client.get('/api/ChequeReminderCollectionListJson/')
        self.assertEqual(resp_cheque.status_code, 200)

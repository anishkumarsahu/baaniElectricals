from home.models import CashCounter, CollectionCashCounter, PartyGroup
from home.tests.base import BaseTestCase


class CashCounterIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for Cash Counter (POS / Point of Sale):
    - Multi-mode transactions (Cash, Card, Mix, Credit, Return, Advance, Expense)
    - Counter collection entries
    - Updates and soft-deletion across CashCounter and CollectionCashCounter
    - Dashboard aggregate reports (staff & admin views)
    - DataTables JSON endpoints across counter streams
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_counter", "Pass123!", "Admin")
        self.counter_user, self.counter_staff = self.create_staff("cashier_01", "Pass123!", "CashCounter")
        self.bank = self.create_bank("ICICI Bank", "ICIC000554433")
        self.party_group = PartyGroup.objects.create(name="Walk-in Retail")
        self.party = self.create_party("Walk-in Customer", "9900112233", self.party_group)

    def test_add_cash_counter_cash_and_card_modes(self):
        self.client.force_login(self.counter_user)

        # 1. Standard Cash Sale
        resp_cash = self.client.post('/api/add_cash_counter_entry_api/', {
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '1001',
            'invoiceYearSelect': '26-27',
            'mode': 'Cash',
            'amount': '3200.0',
            'remark': 'Counter cash sale'
        })
        self.assertEqual(resp_cash.status_code, 200)
        self.assertEqual(resp_cash.json(), {'message': 'success'})

        cash_entry = CashCounter.objects.filter(mode='Cash').latest('id')
        self.assertEqual(cash_entry.amount, 3200.0)
        self.assertEqual(cash_entry.invoiceNumber, 'BSSAC/1001/26-27')
        self.assertEqual(cash_entry.createdBy, self.counter_staff)
        self.assertFalse(cash_entry.isDeleted)

        # 2. Card Sale with Bank ID
        resp_card = self.client.post('/api/add_cash_counter_entry_api/', {
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '1002',
            'invoiceYearSelect': '26-27',
            'mode': 'Card',
            'amount': '7500.0',
            'bank': str(self.bank.pk),
            'remark': 'POS swipe on ICICI terminal'
        })
        self.assertEqual(resp_card.status_code, 200)
        self.assertEqual(resp_card.json(), {'message': 'success'})

        card_entry = CashCounter.objects.filter(mode='Card').latest('id')
        self.assertEqual(card_entry.amount, 7500.0)
        self.assertEqual(card_entry.bankID, self.bank)

    def test_add_cash_counter_mix_split_payment_mode(self):
        self.client.force_login(self.counter_user)

        resp_mix = self.client.post('/api/add_cash_counter_entry_api/', {
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '1003',
            'invoiceYearSelect': '26-27',
            'mode': 'Mix',
            'amountMixCash': '2000.0',
            'amountMixCard': '3000.0',
            'amount': '5000.0',
            'bank': str(self.bank.pk),
            'remark': 'Split payment: 2000 Cash + 3000 Card'
        })
        self.assertEqual(resp_mix.status_code, 200)
        self.assertEqual(resp_mix.json(), {'message': 'success'})

        mix_entry = CashCounter.objects.filter(mode='Mix').latest('id')
        self.assertEqual(mix_entry.mixCashAmount, 2000.0)
        self.assertEqual(mix_entry.mixCardAmount, 3000.0)
        self.assertTrue(mix_entry.counterID.startswith('CC'))

    def test_add_cash_counter_credit_and_expense_modes(self):
        self.client.force_login(self.counter_user)

        # 1. Credit Sale
        resp_credit = self.client.post('/api/add_cash_counter_entry_api/', {
            'invoiceSeriesSelect': 'BSSAC',
            'invoiceNo': '1004',
            'invoiceYearSelect': '26-27',
            'mode': 'Credit',
            'party': f"{self.party.name}@{self.party.pk}",
            'amount': '12000.0',
            'remark': 'Credit bill on account'
        })
        self.assertEqual(resp_credit.status_code, 200)
        self.assertEqual(resp_credit.json(), {'message': 'success'})

        credit_entry = CashCounter.objects.filter(mode='Credit').latest('id')
        self.assertEqual(credit_entry.partyID, self.party)
        self.assertEqual(credit_entry.amount, 12000.0)

        # 2. Expense Entry
        resp_exp = self.client.post('/api/add_cash_counter_entry_api/', {
            'mode': 'Expense',
            'expenseType': 'Office Tea & Snacks',
            'amount': '250.0',
            'remark': 'Tea stall voucher'
        })
        self.assertEqual(resp_exp.status_code, 200)
        self.assertEqual(resp_exp.json(), {'message': 'success'})

        exp_entry = CashCounter.objects.filter(mode='Expense').latest('id')
        self.assertEqual(exp_entry.expenseType, 'Office Tea & Snacks')
        self.assertEqual(exp_entry.amount, 250.0)

    def test_cash_counter_collection_flow(self):
        self.client.force_login(self.counter_user)

        resp = self.client.post('/api/add_collection_from_cash_counter_api/', {
            'party': f"{self.party.name}@{self.party.pk}",
            'paymentMode': 'Cash',
            'amountPaid': '4000.0',
            'detail': 'Counter ledger clearance',
            'remark': 'Cash received at shop counter',
            'lat': '22.5700',
            'lng': '88.3600',
            'chequeDate': ''
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        cc_col = CollectionCashCounter.objects.filter(partyID=self.party).latest('id')
        self.assertEqual(cc_col.paidAmount, 4000.0)
        self.assertEqual(cc_col.collectedBy, self.counter_staff)
        self.assertFalse(cc_col.isDeleted)

    def test_cash_counter_soft_deletion(self):
        self.client.force_login(self.admin_user)

        # 1. Soft delete regular CashCounter entry
        entry = CashCounter.objects.create(
            mode="Cash",
            amount=1000.0,
            createdBy=self.counter_staff
        )
        del_resp = self.client.post('/api/delete_cash_counter/', {
            'userID': str(entry.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})
        entry.refresh_from_db()
        self.assertTrue(entry.isDeleted)
        self.assertTrue(CashCounter.objects.filter(pk=entry.pk).exists())

        # 2. Soft delete CollectionCashCounter entry (ID with 'c' prefix)
        col_entry = CollectionCashCounter.objects.create(
            partyID=self.party,
            modeOfPayment="Cash",
            paidAmount=1500.0,
            collectedBy=self.counter_staff
        )
        del_col_resp = self.client.post('/api/delete_cash_counter/', {
            'userID': f"c{col_entry.pk}"
        })
        self.assertEqual(del_col_resp.status_code, 200)
        self.assertEqual(del_col_resp.json(), {'message': 'success'})
        col_entry.refresh_from_db()
        self.assertTrue(col_entry.isDeleted)
        self.assertTrue(CollectionCashCounter.objects.filter(pk=col_entry.pk).exists())

    def test_cash_counter_dashboard_reports_and_datatables(self):
        # Create cash and card entries
        CashCounter.objects.create(
            mode="Cash",
            amount=5000.0,
            createdBy=self.counter_staff
        )
        CashCounter.objects.create(
            mode="Card",
            amount=3000.0,
            createdBy=self.counter_staff
        )

        # 1. Staff Dashboard Report
        self.client.force_login(self.counter_user)
        staff_rep = self.client.get('/api/get_cash_counter_dashboard_report_api/')
        self.assertEqual(staff_rep.status_code, 200)

        # 2. Admin Dashboard Report
        self.client.force_login(self.admin_user)
        admin_rep = self.client.get('/api/get_cash_counter_dashboard_report_admin_api/')
        self.assertEqual(admin_rep.status_code, 200)

        # 3. DataTables JSON views
        self.client.force_login(self.counter_user)
        dt_cash = self.client.get('/api/CashCounterByStaffListJson/')
        self.assertEqual(dt_cash.status_code, 200)

        dt_card = self.client.get('/api/CardCounterByStaffListJson/')
        self.assertEqual(dt_card.status_code, 200)

        dt_mix = self.client.get('/api/MixCounterByStaffListJson/')
        self.assertEqual(dt_mix.status_code, 200)

from home.models import Bank, Party, PartyGroup, StaffGroup, StaffUser
from home.tests.base import BaseTestCase


class MasterDataIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for Master Data management:
    - Staff Users
    - Party Groups
    - Banks
    - Parties (Customers/Vendors) with createdBy auditing and soft-deletion
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_master", "Pass123!", "Admin")
        self.client.force_login(self.admin_user)

    def test_party_group_lifecycle(self):
        # 1. Create Party Group
        resp = self.client.post('/api/add_party_group_api/', {
            'groupName': 'Wholesale Dealers',
            'description': 'Bulk distributors for Eastern region'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        group = PartyGroup.objects.get(name='Wholesale Dealers')
        self.assertEqual(group.description, 'Bulk distributors for Eastern region')
        self.assertFalse(group.isDeleted)

        # 2. Get Detail
        detail_resp = self.client.get(f'/api/get_party_group_detail/?id={group.pk}')
        self.assertEqual(detail_resp.status_code, 200)
        data = detail_resp.json().get('data')
        self.assertEqual(data.get('Name'), 'Wholesale Dealers')

        # 3. Edit Party Group
        edit_resp = self.client.post('/api/edit_part_group_api/', {
            'EditId': str(group.pk),
            'groupName': 'Premium Wholesale Dealers',
            'description': 'Updated description'
        })
        self.assertEqual(edit_resp.status_code, 200)
        self.assertEqual(edit_resp.json(), {'message': 'success'})
        group.refresh_from_db()
        self.assertEqual(group.name, 'Premium Wholesale Dealers')

        # 4. Soft Delete Party Group
        del_resp = self.client.post('/api/delete_part_group/', {
            'userID': str(group.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})
        group.refresh_from_db()
        self.assertTrue(group.isDeleted)

        # 5. DataTables filtering excludes soft-deleted
        dt_resp = self.client.get('/api/PartyGroupListJson/')
        self.assertEqual(dt_resp.status_code, 200)

    def test_bank_lifecycle(self):
        # 1. Create Bank
        resp = self.client.post('/api/add_bank_api/', {
            'bankName': 'State Bank of India',
            'accountNumber': 'SBIN00012345678',
            'description': 'Main current collection account'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        bank = Bank.objects.get(accountNumber='SBIN00012345678')
        self.assertEqual(bank.name, 'State Bank of India')
        self.assertFalse(bank.isDeleted)

        # 2. Get Detail
        detail_resp = self.client.get(f'/api/get_bank_detail/?id={bank.pk}')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json().get('data').get('AccountNumber'), 'SBIN00012345678')

        # 3. Edit Bank
        edit_resp = self.client.post('/api/edit_bank_api/', {
            'EditId': str(bank.pk),
            'bankName': 'SBI Corporate Branch',
            'accountNumber': 'SBIN00012345678',
            'description': 'Corporate account'
        })
        self.assertEqual(edit_resp.status_code, 200)
        self.assertEqual(edit_resp.json(), {'message': 'success'})
        bank.refresh_from_db()
        self.assertEqual(bank.name, 'SBI Corporate Branch')

        # 4. Soft Delete Bank
        del_resp = self.client.post('/api/delete_bank/', {
            'userID': str(bank.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})
        bank.refresh_from_db()
        self.assertTrue(bank.isDeleted)

    def test_staff_user_lifecycle(self):
        # Prepare uploads
        photo = self.create_dummy_image("staff_photo.jpg")
        id_proof = self.create_dummy_image("staff_id.jpg")
        StaffGroup.objects.create(name="Collection")

        # 1. Create Staff User
        resp = self.client.post('/api/add_staff_api/', {
            'CompanyUserName': 'Rajesh Sharma',
            'UserPhoneNo': '9871122334',
            'UserEmail': 'rajesh@baanielectricals.com',
            'UserAddress': 'Sector 5, Salt Lake, Kolkata',
            'UserGroup': 'Collection',
            'UserStatus': 'Active',
            'UserPwd': 'StaffSecretPassword123!',
            'imageUpload': photo,
            'imageUploadID': id_proof
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        staff = StaffUser.objects.get(name='Rajesh Sharma')
        self.assertEqual(staff.phone, '9871122334')
        self.assertFalse(staff.isDeleted)
        self.assertIsNotNone(staff.user_ID)
        self.assertTrue(staff.user_ID.groups.filter(name='Collection').exists())

        # 2. Detail
        detail_resp = self.client.get(f'/api/get_staff_user_detail/?id={staff.pk}')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json().get('data').get('UserName'), 'Rajesh Sharma')

        # 3. Edit Staff User
        edit_resp = self.client.post('/api/edit_staff_api/', {
            'EditUserId': str(staff.pk),
            'CompanyUserName': 'Rajesh Kumar Sharma',
            'UserPhoneNo': '9871122334',
            'UserEmail': 'rajesh.kumar@baanielectricals.com',
            'UserAddress': 'Sector 5, Salt Lake, Kolkata Updated',
            'UserGroup': 'Collection',
            'UserStatus': 'Active',
            'UserPwd': 'NewStaffSecretPassword123!',
            'imageUpload': '',
            'imageUploadID': ''
        })
        self.assertEqual(edit_resp.status_code, 200)
        self.assertEqual(edit_resp.json(), {'message': 'success'})
        staff.refresh_from_db()
        self.assertEqual(staff.name, 'Rajesh Kumar Sharma')

        # 4. Soft Delete Staff User
        del_resp = self.client.post('/api/delete_staff_user/', {
            'userID': str(staff.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})
        staff.refresh_from_db()
        self.assertTrue(staff.isDeleted)

    def test_party_lifecycle_and_created_by_audit(self):
        pg = PartyGroup.objects.create(name="Retailers")
        _, collector = self.create_staff("field_staff", "Pass123!", "Collection")

        # 1. Create Party via API
        resp = self.client.post('/api/add_party_api/', {
            'partyName': 'Gupta Electricals & Hardware',
            'phoneNumber': '9933445566',
            'partyGroup': str(pg.pk),
            'staffID': str(collector.pk)
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        party = Party.objects.get(name='Gupta Electricals & Hardware')
        self.assertEqual(party.phone, '9933445566')
        self.assertEqual(party.partyGroupID, pg)
        self.assertEqual(party.assignTo, collector)
        # Verify createdBy audit field populated
        self.assertEqual(party.createdBy, self.admin_staff)
        self.assertFalse(party.isDeleted)
        self.assertIsNotNone(party.userID)
        self.assertTrue(party.userID.groups.filter(name='Customer').exists())

        # 2. Get Detail
        detail_resp = self.client.get(f'/api/get_party_detail/?id={party.pk}')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json().get('data').get('Name'), 'Gupta Electricals & Hardware')

        # 3. Edit Party
        edit_resp = self.client.post('/api/edit_party_api/', {
            'EditId': str(party.pk),
            'partyName': 'Gupta Electricals & Hardware Pvt Ltd',
            'phoneNumber': '9933445566',
            'partyGroup': str(pg.pk),
            'staffID': str(collector.pk)
        })
        self.assertEqual(edit_resp.status_code, 200)
        self.assertEqual(edit_resp.json(), {'message': 'success'})
        party.refresh_from_db()
        self.assertEqual(party.name, 'Gupta Electricals & Hardware Pvt Ltd')

        # 4. List Parties API
        list_resp = self.client.get('/api/list_party_api/')
        self.assertEqual(list_resp.status_code, 200)
        parties = list_resp.json().get('data', [])
        self.assertTrue(any(p.get('Name') == 'Gupta Electricals & Hardware Pvt Ltd' for p in parties))

        # 5. List by executive
        exec_resp = self.client.get(f'/api/list_party_by_executive_or_station_api/?staffID={collector.pk}')
        self.assertEqual(exec_resp.status_code, 200)

        # 6. Soft Delete Party
        del_resp = self.client.post('/api/delete_party/', {
            'userID': str(party.pk)
        })
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json(), {'message': 'success'})
        party.refresh_from_db()
        self.assertTrue(party.isDeleted)
        # Party must NOT be deleted from DB
        self.assertTrue(Party.objects.filter(pk=party.pk).exists())

    def test_generate_party_users_api_e2e(self):
        # Create parties without linked User accounts
        pg = PartyGroup.objects.create(name="Unregistered Parties")
        p1 = Party.objects.create(name="Store A", phone="9000000001", partyGroupID=pg)
        p2 = Party.objects.create(name="Store B", phone="9000000002", partyGroupID=pg)

        resp = self.client.get('/api/generate_party_users_api/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('message'), 'success')
        self.assertGreaterEqual(data.get('created'), 2)

        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertIsNotNone(p1.userID)
        self.assertIsNotNone(p2.userID)
        self.assertTrue(p1.userID.groups.filter(name='Customer').exists())

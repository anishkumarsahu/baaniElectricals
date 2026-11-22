from home.models import Party
from home.tests.base import BaseTestCase


class AuthenticationAndRBACIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for authentication lifecycle, session routing,
    RBAC authorization checks, and credential updates.
    """

    def test_login_page_renders_successfully(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/login.html')

    def test_post_login_success_for_all_supported_roles(self):
        roles = ['Admin', 'Moderator', 'Collection', 'NormalStaff', 'CashCounter', 'SalesAdmin', 'Customer']

        for role in roles:
            with self.subTest(role=role):
                username = f"user_{role.lower()}"
                password = "SecurePassword123!"
                self.create_user_with_group(username=username, password=password, group_name=role)

                response = self.client.post('/postLogin/', {
                    'userName': username,
                    'password': password
                })
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data.get('message'), 'success')
                self.assertEqual(data.get('data'), '/home/')
                self.client.logout()

    def test_post_login_invalid_password(self):
        self.create_user_with_group("test_admin", "ValidPass123!", "Admin")
        response = self.client.post('/postLogin/', {
            'userName': 'test_admin',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'fail'})

    def test_post_login_nonexistent_user(self):
        response = self.client.post('/postLogin/', {
            'userName': 'does_not_exist',
            'password': 'SomePassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'fail'})

    def test_post_login_unauthorized_group(self):
        user = self.create_user_with_group("guest_user", "GuestPass123!", "UnauthorizedGroup")
        response = self.client.post('/postLogin/', {
            'userName': user.username,
            'password': 'GuestPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'fail'})

    def test_homepage_redirects_by_role(self):
        routing_map = [
            ('Admin', '/admin_home/'),
            ('Moderator', '/admin_home/'),
            ('Collection', '/collection_home/'),
            ('NormalStaff', '/staff_home/'),
            ('CashCounter', '/cash_counter_home/'),
            ('SalesAdmin', '/collection_home/'),
            ('Customer', '/customer_home/'),
        ]

        for role, expected_redirect in routing_map:
            with self.subTest(role=role):
                username = f"route_{role.lower()}"
                password = "RoutePass123!"
                user = self.create_user_with_group(username, password, role)
                if role == 'Customer':
                    # Customer home expects an associated Party record
                    Party.objects.create(
                        name="Customer Co",
                        phone="9876543210",
                        username=username,
                        password=password,
                        userID=user
                    )
                self.client.force_login(user)

                response = self.client.get('/home/')
                self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)
                self.client.logout()

    def test_homepage_anonymous_user_renders_login(self):
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/login.html')

    def test_user_logout_clears_session(self):
        user = self.create_user_with_group("logout_user", "Pass123!", "Admin")
        self.client.force_login(user)

        response = self.client.get('/logout/')
        self.assertRedirects(response, '/', target_status_code=200)

        # Confirm session is terminated
        home_resp = self.client.get('/home/')
        self.assertTemplateUsed(home_resp, 'home/login.html')

    def test_rbac_view_restrictions(self):
        # 1. Collection user attempting to view Admin home
        coll_user = self.create_user_with_group("collector1", "Pass123!", "Collection")
        self.client.force_login(coll_user)
        resp = self.client.get('/admin_home/')
        self.assertRedirects(resp, '/', fetch_redirect_response=False)

        # 2. Customer attempting to view Collection home
        cust_user = self.create_user_with_group("cust1", "Pass123!", "Customer")
        self.client.force_login(cust_user)
        resp = self.client.get('/collection_home/')
        self.assertRedirects(resp, '/', fetch_redirect_response=False)

        # 3. Unauthenticated user accessing protected Admin endpoints
        self.client.logout()
        resp = self.client.get('/admin_home/')
        self.assertRedirects(resp, '/', fetch_redirect_response=False)

    def test_change_password_api_for_staff(self):
        user, staff = self.create_staff("pass_changer", "OldPass123!", "Admin")
        self.client.force_login(user)

        response = self.client.post('/api/change_password_api/', {
            'password': 'NewSecurePass456!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), 'success')

        # Verify password in database and authentication with new password
        user.refresh_from_db()
        staff.refresh_from_db()
        self.assertTrue(user.check_password('NewSecurePass456!'))
        self.assertEqual(staff.userPassword, 'NewSecurePass456!')

    def test_customer_change_password_flow(self):
        user = self.create_user_with_group("cust_changer", "123456", "Customer")
        party = Party.objects.create(
            name="Party Alpha",
            phone="9123456789",
            username=user.username,
            password="123456",
            userID=user
        )
        self.client.force_login(user)

        # Valid numeric 6-digit password update
        response = self.client.post('/customer/change-password/', {
            'current_password': '123456',
            'new_password': '654321',
            'confirm_password': '654321'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), 'success')

        user.refresh_from_db()
        party.refresh_from_db()
        self.assertTrue(user.check_password('654321'))
        self.assertEqual(party.password, '654321')

    def test_customer_change_password_validation_errors(self):
        user = self.create_user_with_group("cust_validator", "123456", "Customer")
        self.client.force_login(user)

        # Mismatched passwords
        resp = self.client.post('/customer/change-password/', {
            'current_password': '123456',
            'new_password': '654321',
            'confirm_password': '999999'
        })
        self.assertEqual(resp.status_code, 400)

        # Non-numeric 6-character password
        resp = self.client.post('/customer/change-password/', {
            'current_password': '123456',
            'new_password': 'abcdef',
            'confirm_password': 'abcdef'
        })
        self.assertEqual(resp.status_code, 400)

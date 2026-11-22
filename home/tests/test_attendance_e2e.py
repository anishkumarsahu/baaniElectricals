import datetime

from home.models import Attendance
from home.tests.base import BaseTestCase


class AttendanceIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for Staff Attendance:
    - Daily attendance record provisioning
    - Check-in (Login) event logging with GPS coordinates
    - Check-out (Logout) event logging with GPS coordinates
    - Soft-deletion invariants
    - Staff & Admin DataTables JSON views
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_attend", "Pass123!", "Admin")
        self.staff_user, self.staff = self.create_staff("field_attend", "Pass123!", "NormalStaff")

    def test_attendance_lifecycle_login_and_logout_e2e(self):
        self.client.force_login(self.staff_user)

        # 1. Access attendance page - auto-creates today's Attendance instance if not present
        page_resp = self.client.get('/add_attendance/')
        self.assertEqual(page_resp.status_code, 200)

        attend = Attendance.objects.get(staffID=self.staff)
        self.assertFalse(attend.isLogIn)
        self.assertFalse(attend.isLogOut)

        # 2. Check-in (Login)
        login_resp = self.client.post('/api/add_attendance_api/', {
            'stat': 'Login',
            'remark': 'Reached regional depot on time',
            'lat': '22.5726',
            'lng': '88.3639'
        })
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json(), {'message': 'success'})

        attend.refresh_from_db()
        self.assertTrue(attend.isLogIn)
        self.assertEqual(attend.login_remark, 'Reached regional depot on time')
        self.assertEqual(attend.login_latitude, '22.5726')
        self.assertEqual(attend.login_longitude, '88.3639')
        self.assertIsNotNone(attend.loginDateTime)

        # 3. Check-out (Logout)
        logout_resp = self.client.post('/api/add_attendance_api/', {
            'stat': 'Logout',
            'remark': 'All deliveries and collections completed',
            'lat': '22.5800',
            'lng': '88.3700'
        })
        self.assertEqual(logout_resp.status_code, 200)
        self.assertEqual(logout_resp.json(), {'message': 'success'})

        attend.refresh_from_db()
        self.assertTrue(attend.isLogOut)
        self.assertEqual(attend.logout_remark, 'All deliveries and collections completed')
        self.assertEqual(attend.logout_latitude, '22.5800')
        self.assertEqual(attend.logout_longitude, '88.3700')
        self.assertIsNotNone(attend.logoutDateTime)

    def test_attendance_soft_delete_invariant(self):
        attend = Attendance.objects.create(
            staffID=self.staff,
            isLogIn=True,
            login_latitude="22.5726",
            login_longitude="88.3639"
        )
        attend.isDeleted = True
        attend.save()

        self.assertTrue(attend.isDeleted)
        self.assertTrue(Attendance.objects.filter(pk=attend.pk).exists())

    def test_attendance_datatables_json_views(self):
        Attendance.objects.create(
            staffID=self.staff,
            isLogIn=True,
            loginDateTime=datetime.datetime.now(),
            login_latitude="22.5726",
            login_longitude="88.3639"
        )

        self.client.force_login(self.staff_user)
        staff_dt = self.client.get('/api/StaffAttendanceListJson/')
        self.assertEqual(staff_dt.status_code, 200)

        self.client.force_login(self.admin_user)
        admin_dt = self.client.get('/api/AdminAttendanceListJson/')
        self.assertEqual(admin_dt.status_code, 200)

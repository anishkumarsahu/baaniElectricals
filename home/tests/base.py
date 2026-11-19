import datetime
import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from activation.models import Validity
from home.models import (
    Bank,
    GeolocationPackage,
    Party,
    PartyGroup,
    StaffGroup,
    StaffUser,
    WhatsappMessage,
)


class BaseTestCase(TestCase):
    """
    Base test case providing shared fixtures, mock helpers, and teardown
    for end-to-end integration tests across the Baani Electricals platform.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media = tempfile.mkdtemp()
        cls.override_media = override_settings(MEDIA_ROOT=cls.temp_media)
        cls.override_media.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override_media.disable()
        shutil.rmtree(cls.temp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.today = datetime.date.today()

        # Seed Active Software Validity
        self.validity = Validity.objects.create(
            activationDate=self.today - datetime.timedelta(days=30),
            expiryDate=self.today + datetime.timedelta(days=365),
            activationType="Enterprise"
        )

        # Seed Geolocation & Messaging packages
        self.geo_package = GeolocationPackage.objects.create(
            name="Default Geo",
            balance=1000.0,
            used=10.0,
            description="Production Geo Package"
        )
        self.wa_package = WhatsappMessage.objects.create(
            name="Default WA",
            instanceID="inst_12345",
            apiKey="key_12345",
            balance=1000.0,
            used=5.0
        )

        # Patch external IO / threading calls to keep test execution fast & deterministic
        self.patcher_send_msg = patch('home.apiView.send_message')
        self.patcher_get_loc = patch('home.apiView.get_location')
        self.mock_send_msg = self.patcher_send_msg.start()
        self.mock_get_loc = self.patcher_get_loc.start()
        self.addCleanup(self.patcher_send_msg.stop)
        self.addCleanup(self.patcher_get_loc.stop)

    def create_dummy_image(self, name="avatar.jpg"):
        buf = BytesIO()
        Image.new('RGB', (100, 100), color=(73, 109, 137)).save(buf, format='JPEG')
        return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')

    def create_user_with_group(self, username, password="TestPassword123!", group_name="Admin"):
        user = User.objects.create_user(username=username, password=password)
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        return user

    def create_staff(self, username, password="TestPassword123!", group_name="Admin", name=None):
        user = self.create_user_with_group(username, password, group_name)
        StaffGroup.objects.get_or_create(name=group_name)
        party_group, _ = PartyGroup.objects.get_or_create(name="Retail Group")

        staff = StaffUser.objects.create(
            name=name or f"Staff {username}",
            phone="9876543210",
            address="123 Test Street, Kolkata",
            email=f"{username}@test.com",
            username=username,
            userPassword=password,
            group=group_name,
            partyGroupID=party_group,
            user_ID=user,
            isActive="Active"
        )
        return user, staff

    def create_bank(self, name="HDFC Bank", account_number="123456789012"):
        return Bank.objects.create(
            name=name,
            accountNumber=account_number,
            description="Primary Operating Account"
        )

    def create_party(self, name="Test Enterprise", phone="9988776655", party_group=None, assign_to=None, created_by=None):
        if party_group is None:
            party_group, _ = PartyGroup.objects.get_or_create(name="Standard Dealers")

        party_user = User.objects.create_user(
            username=f"party_{name.lower().replace(' ', '_')[:10]}",
            password="CustomerPass123!"
        )
        cust_group, _ = Group.objects.get_or_create(name="Customer")
        party_user.groups.add(cust_group)

        return Party.objects.create(
            name=name,
            phone=phone,
            address="456 Market Lane",
            username=party_user.username,
            password="CustomerPass123!",
            userID=party_user,
            partyGroupID=party_group,
            assignTo=assign_to,
            createdBy=created_by
        )

from unittest.mock import MagicMock, patch

from home.models import WhatsappMessageStatus
from home.tests.base import BaseTestCase
from sms_worker import MessageProcessor


class SMSWorkerAndMessagingIntegrationTests(BaseTestCase):
    """
    End-to-end integration tests for the asynchronous WhatsApp / SMS worker daemon:
    - Message staging and querying via `/api/get_all_unsent_messages/`
    - Gateway callback status updates via `/api/update_sent_msg_status/`
    - MessageProcessor daemon execution loop (fetch -> send -> update status)
    - Filtering invariants: 10-digit phone number validation & 5-day window
    """

    def setUp(self):
        super().setUp()
        self.admin_user, self.admin_staff = self.create_staff("admin_sms", "Pass123!", "Admin")

    def test_get_all_unsent_messages_endpoint_filters(self):
        # Valid unsent message: 10 digits, status 'Fail', created recently
        valid_msg = WhatsappMessageStatus.objects.create(
            phone="9876543210",
            message="Payment received test",
            messageTo="Test Customer",
            status="Fail"
        )

        # Invalid: status is already 'Success'
        WhatsappMessageStatus.objects.create(
            phone="9876543211",
            message="Already sent",
            messageTo="Customer Two",
            status="Success"
        )

        # Invalid: phone length is not 10 digits
        WhatsappMessageStatus.objects.create(
            phone="919876543212",  # 12 digits
            message="Country code prefix",
            messageTo="Customer Three",
            status="Fail"
        )

        # Invalid: soft deleted
        WhatsappMessageStatus.objects.create(
            phone="9876543213",
            message="Soft deleted",
            messageTo="Customer Four",
            status="Fail",
            isDeleted=True
        )

        resp = self.client.get('/api/get_all_unsent_messages/')
        self.assertEqual(resp.status_code, 200)
        messages = resp.json()

        # Only the valid 10-digit Fail message should be returned
        msg_ids = [m['id'] for m in messages]
        self.assertIn(valid_msg.pk, msg_ids)
        self.assertEqual(len(messages), 1)

    def test_update_sent_msg_status_endpoint(self):
        msg = WhatsappMessageStatus.objects.create(
            phone="9876543210",
            message="Status update test",
            messageTo="Customer Update",
            status="Fail"
        )

        resp = self.client.post('/api/update_sent_msg_status/', {
            'id': str(msg.pk)
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'success'})

        msg.refresh_from_db()
        self.assertEqual(msg.status, 'Success')

    @patch('sms_worker.time.sleep')
    @patch('sms_worker.requests.post')
    @patch('sms_worker.requests.get')
    def test_message_processor_daemon_e2e(self, mock_get, mock_post, mock_sleep):
        # 1. Mock fetch response from /api/get_all_unsent_messages/
        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = [{
            "id": 101,
            "phone": "9876543210",
            "message": "Payment Rs.5000 received. Ref 0001",
            "messageTo": "Retail Dealer",
            "status": "Fail"
        }]
        mock_get_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_resp

        # 2. Mock gateway send response and status callback
        mock_post_resp = MagicMock()
        mock_post_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_post_resp

        processor = MessageProcessor(delay_between_requests=0)
        processor.process_all_messages()

        # Verify gateway call payload
        self.assertEqual(mock_post.call_count, 2)  # 1 for send, 1 for update status
        _, send_call_kwargs = mock_post.call_args_list[0]
        self.assertEqual(send_call_kwargs['json']['to'], '919876543210@c.us')
        self.assertEqual(send_call_kwargs['json']['message'], 'Payment Rs.5000 received. Ref 0001')

        # Verify status update payload
        _, update_call_kwargs = mock_post.call_args_list[1]
        self.assertEqual(update_call_kwargs['data']['id'], 101)

    def test_message_list_datatable_view(self):
        WhatsappMessageStatus.objects.create(
            phone="9876543210",
            message="Datatable message test",
            messageTo="Customer DT",
            status="Success"
        )

        self.client.force_login(self.admin_user)
        resp = self.client.get('/api/MessageListJson/')
        self.assertEqual(resp.status_code, 200)

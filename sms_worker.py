import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class MessageProcessor:
    FETCH_URL = os.environ.get("SMS_FETCH_URL", "https://bssac.in/api/get_all_unsent_messages/")
    SEND_URL = os.environ.get("SMS_SEND_URL", "http://localhost:8082/api/v1/users/send-message")
    UPDATE_STATUS_URL = os.environ.get("SMS_UPDATE_STATUS_URL", "https://bssac.in/api/update_sent_msg_status/")
    user_id = os.environ.get("SMS_USER_ID", "1")

    def __init__(self, delay_between_requests=None):
        env_delay = os.environ.get("SMS_DELAY_SECONDS")
        self.delay = int(env_delay) if env_delay is not None else (delay_between_requests or 5)

        auth_token = os.environ.get(
            "SMS_AUTH_TOKEN",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiaHlkcmFib3QiLCJ0aW1lIjoiMjAyNS0wNi0yM1QxMDo0Nzo0My40OTFaIiwiaWF0IjoxNzUwNjc1NjYzfQ.7SHnk7qFz21weHgr6p-swLlMxn0NET1Ja5DhP-If8Sg"
        )
        if auth_token and not auth_token.startswith("Bearer "):
            auth_token = f"Bearer {auth_token}"

        self.auth_header = {
            "Authorization": auth_token
        }

    def fetch_unsent_messages(self):
        try:
            response = requests.get(self.FETCH_URL)
            response.raise_for_status()
            messages = response.json()
            print(f"Fetched {len(messages)} unsent messages.")
            return messages
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch messages: {e}")
            return []

    def send_message(self, phone, message):
        print(phone)
        print(phone.strip(' '))
        payload = {
            "userId": self.user_id,
            "to": '91' + str(phone).strip(' ') + '@c.us',
            "message": message
        }
        headers = {
            **self.auth_header,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(self.SEND_URL, json=payload, headers=headers)
            response.raise_for_status()
            print(f"[SUCCESS] Message sent to {phone}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send message to {phone}: {e}")
            return False

    def update_message_status(self, message_id):
        try:
            payload = {"id": message_id}
            response = requests.post(self.UPDATE_STATUS_URL, data=payload)  # sent as form data
            response.raise_for_status()
            print(f"[UPDATED] Status updated for message ID {message_id}")
        except requests.RequestException as e:
            print(f"[ERROR] Failed to update status for ID {message_id}: {e}")

    def process_all_messages(self):
        messages = self.fetch_unsent_messages()
        for msg in messages:
            msg_id = msg.get("id")
            phone = msg.get("phone")
            message = msg.get("message")

            if not all([msg_id, phone, message]):
                print(f"[SKIPPED] Invalid message format: {msg}")
                continue

            sent = self.send_message(phone, message)
            if sent:
                self.update_message_status(msg_id)

            time.sleep(self.delay)  # optional delay to avoid rate limiting


if __name__ == "__main__":
    processor = MessageProcessor(delay_between_requests=1)
    processor.process_all_messages()

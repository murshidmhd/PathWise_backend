from django.test import TestCase
from unittest.mock import patch
from firebase_admin import messaging
from .utils import send_user_notification # Assume this is your function

class NotificationTest(TestCase):

    @patch('firebase_admin.messaging.send')
    def test_send_notification_logic(self, mock_fcm_send):
        """Test if our function passes the right data to Firebase"""
        
        # 1. Define dummy data
        test_token = "fake-token-123"
        test_title = "Hello"
        
        # 2. Call your actual function
        send_user_notification(test_token, test_title, "Test Body")

        # 3. Assertions (The Verification)
        # Check if the Firebase 'send' function was called at least once
        self.assertTrue(mock_fcm_send.called)
        
        # Check if the data passed to it was a 'Message' object
        args, kwargs = mock_fcm_send.call_args
        sent_message = args[0]
        
        self.assertIsInstance(sent_message, messaging.Message)
        self.assertEqual(sent_message.notification.title, test_title)
        self.assertEqual(sent_message.token, test_token)
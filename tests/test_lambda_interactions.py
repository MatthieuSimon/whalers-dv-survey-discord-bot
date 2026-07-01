import base64
import json
import unittest
from unittest.mock import MagicMock, patch

import lambda_interactions


class TestLambdaInteractions(unittest.TestCase):
    def setUp(self):
        self.valid_headers = {
            "x-signature-ed25519": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "x-signature-timestamp": "2026-07-01T00:00:00.000Z",
        }
        self.valid_body = json.dumps({
            "type": 1,
            "data": {},
        })

    @patch("lambda_interactions.config.DISCORD_PUBLIC_KEY", "a" * 64)
    @patch("lambda_interactions.config.validate_config")
    @patch("lambda_interactions.VerifyKey")
    def test_handler_responds_to_ping(self, mock_verify_key, mock_validate_config):
        mock_verify = mock_verify_key.return_value
        mock_verify.verify.return_value = True

        event = {
            "headers": self.valid_headers,
            "body": self.valid_body,
            "isBase64Encoded": False,
        }

        response = lambda_interactions.handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["type"], 1)

    @patch("lambda_interactions.config.DISCORD_PUBLIC_KEY", "a" * 64)
    @patch("lambda_interactions.config.validate_config")
    @patch("lambda_interactions.RegistrationDB")
    @patch("lambda_interactions.requests.patch")
    @patch("lambda_interactions.VerifyKey")
    def test_handler_updates_message_and_replies(self, mock_verify_key, mock_patch, mock_db_class, mock_validate_config):
        mock_verify = mock_verify_key.return_value
        mock_verify.verify.return_value = True

        mock_db = MagicMock()
        mock_db.get_all_registrations.return_value = {
            "Fire": ["123"],
            "Water": [],
            "Earth": [],
            "Wind": [],
            "Whatever": [],
        }
        mock_db_class.return_value = mock_db

        interaction = {
            "type": 3,
            "data": {"custom_id": "survey_select", "values": ["Fire"]},
            "member": {"user": {"id": "9999"}},
            "message": {"id": "msg123"},
            "channel_id": "chan456",
        }

        event = {
            "headers": self.valid_headers,
            "body": json.dumps(interaction),
            "isBase64Encoded": False,
        }

        response = lambda_interactions.handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["type"], 4)
        self.assertIn("✅ Your registration has been updated", body["data"]["content"])
        mock_patch.assert_called_once()


if __name__ == "__main__":
    unittest.main()

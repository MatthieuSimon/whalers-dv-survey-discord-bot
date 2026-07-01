import json
import unittest
from unittest.mock import MagicMock, patch

import lambda_publish


class TestLambdaPublish(unittest.TestCase):
    @patch("lambda_publish.RegistrationDB")
    @patch("lambda_publish.requests.post")
    @patch("lambda_publish.config.validate_config")
    def test_publish_survey_message_sends_correct_payload(self, mock_validate_config, mock_post, mock_db_class):
        mock_db = MagicMock()
        mock_db.get_all_registrations.return_value = {
            "Fire": [],
            "Water": [],
            "Earth": [],
            "Wind": [],
            "Whatever": [],
        }
        mock_db_class.return_value = mock_db

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg123", "channel_id": "chan456", "timestamp": "2026-07-01T00:00:00.000Z"}
        mock_post.return_value = mock_response

        result = lambda_publish.publish_survey_message(mock_db)

        mock_post.assert_called_once()
        self.assertEqual(result["id"], "msg123")
        self.assertEqual(result["channel_id"], "chan456")

    @patch("lambda_publish.RegistrationDB")
    @patch("lambda_publish.requests.post")
    @patch("lambda_publish.config.validate_config")
    def test_handler_returns_expected_body(self, mock_validate_config, mock_post, mock_db_class):
        mock_db = MagicMock()
        mock_db.get_all_registrations.return_value = {}
        mock_db_class.return_value = mock_db

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg123", "channel_id": "chan456", "timestamp": "2026-07-01T00:00:00.000Z"}
        mock_post.return_value = mock_response

        event = {}
        response = lambda_publish.handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        payload = json.loads(response["body"])
        self.assertEqual(payload["message_id"], "msg123")
        self.assertEqual(payload["channel_id"], "chan456")
        self.assertEqual(payload["timestamp"], "2026-07-01T00:00:00.000Z")


if __name__ == "__main__":
    unittest.main()

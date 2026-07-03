import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Mock config before importing RegistrationDB to prevent validation errors
with patch('config.DYNAMODB_TABLE_NAME', 'mock_table'), \
     patch('config.DYNAMODB_ENDPOINT_URL', None), \
     patch('config.AWS_ACCESS_KEY_ID', None), \
     patch('config.AWS_SECRET_ACCESS_KEY', None), \
     patch('config.AWS_DEFAULT_REGION', 'us-east-1'):
    from db import RegistrationDB


class TestRegistrationDB(unittest.TestCase):
    @patch('boto3.resource')
    def setUp(self, mock_boto_resource):
        self.mock_dynamodb = MagicMock()
        self.mock_table = MagicMock()
        
        self.mock_dynamodb.Table.return_value = self.mock_table
        mock_boto_resource.return_value = self.mock_dynamodb
        
        self.db = RegistrationDB(table_name="mock_table")

    def test_register_user_activities_add_and_delete(self):
        """Test registering user adding to selected and removing from unselected zones."""
        user_id = 123456
        selected_zones = ["Fire", "Water"]
        self.mock_table.get_item.return_value = {"Item": {"priorities": {}}}

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            self.db.register_user_activities(user_id, selected_zones)

        self.assertEqual(self.mock_table.update_item.call_count, 2)

        calls = self.mock_table.update_item.call_args_list

        set_zones = []
        for call in calls:
            kwargs = call.kwargs
            self.assertEqual(kwargs['Key']['survey_date'], '29-06-2026')
            zone = kwargs['Key']['zone']
            expr = kwargs['UpdateExpression']

            self.assertIn("SET", expr)
            set_zones.append(zone)
            expected_priority = {"123456": 1 if zone == 'Fire' else 2}
            self.assertEqual(kwargs['ExpressionAttributeValues'], {':p': expected_priority})
            self.assertEqual(kwargs['ExpressionAttributeNames'], {'#p': 'priorities'})

        self.assertEqual(sorted(set_zones), ["Fire", "Water"])

    def test_register_user_activities_assigns_priorities(self):
        """Test selected zones are stored with the correct priority order."""
        user_id = 123456
        selected_zones = ["Fire", "Water", "Wind"]
        self.mock_table.get_item.return_value = {"Item": {"priorities": {}}}

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            self.db.register_user_activities(user_id, selected_zones)

        self.assertEqual(self.mock_table.update_item.call_count, 3)

        priorities = {
            call.kwargs['Key']['zone']: call.kwargs['ExpressionAttributeValues'][':p']
            for call in self.mock_table.update_item.call_args_list
            if call.kwargs['UpdateExpression'].startswith('SET')
        }

        self.assertEqual(priorities, {
            "Fire": {"123456": 1},
            "Water": {"123456": 2},
            "Wind": {"123456": 3},
        })

    def test_clear_user_registration(self):
        """Test clearing user registration removes from all zones."""
        user_id = 987654
        self.mock_table.get_item.return_value = {"Item": {"priorities": {"987654": 1}}}

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            self.db.clear_user_registration(user_id)

        self.assertEqual(self.mock_table.update_item.call_count, 5)

        calls = self.mock_table.update_item.call_args_list
        for call in calls:
            self.assertEqual(call.kwargs['Key']['survey_date'], '29-06-2026')
            self.assertEqual(call.kwargs['ExpressionAttributeNames'], {'#p': 'priorities'})
            self.assertTrue(call.kwargs['UpdateExpression'] in {'SET #p = :p', 'REMOVE #p'})

    def test_set_priority_creates_initial_map(self):
        """Test creating the first priority entry creates a priorities map."""
        self.mock_table.get_item.return_value = {}

        self.db._set_zone_priority("123456", "Fire", "29-06-2026", 1)

        self.mock_table.update_item.assert_called_once_with(
            Key={'survey_date': '29-06-2026', 'zone': 'Fire'},
            UpdateExpression='SET #p = :p',
            ExpressionAttributeNames={'#p': 'priorities'},
            ExpressionAttributeValues={':p': {'123456': 1}},
        )

    def test_remove_priority_skips_missing_item(self):
        """Test removing a priority from an empty database does not raise."""
        self.mock_table.get_item.return_value = {}

        self.db._remove_zone_priority("123456", "Fire", "29-06-2026")

        self.mock_table.get_item.assert_called_with(Key={'survey_date': '29-06-2026', 'zone': 'Fire'})
        self.mock_table.update_item.assert_not_called()

    def test_get_zone_registrants_existing(self):
        """Test retrieving list of user IDs for a zone when it has data."""
        self.mock_table.get_item.return_value = {
            'Item': {
                'zone': 'Fire',
                'users': {'123', '456'}
            }
        }

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            registrants = self.db.get_zone_registrants('Fire')

        self.assertEqual(registrants, {'123': 1, '456': 1})
        self.mock_table.get_item.assert_called_with(Key={'survey_date': '29-06-2026', 'zone': 'Fire'})

    def test_get_zone_registrants_returns_priority_order(self):
        """Test retrieving registrants ordered by saved priority."""
        self.mock_table.get_item.return_value = {
            'Item': {
                'zone': 'Fire',
                'priorities': {'123': 2, '456': 1}
            }
        }

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            registrants = self.db.get_zone_registrants('Fire')

        self.assertEqual(registrants, {'123': 2, '456': 1})
        self.mock_table.get_item.assert_called_with(Key={'survey_date': '29-06-2026', 'zone': 'Fire'})

    def test_get_zone_registrants_empty(self):
        """Test retrieving list of user IDs for a zone when there is no record."""
        self.mock_table.get_item.return_value = {}

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            registrants = self.db.get_zone_registrants('Water')

        self.assertEqual(registrants, {})
        self.mock_table.get_item.assert_called_with(Key={'survey_date': '29-06-2026', 'zone': 'Water'})

    def test_get_all_registrations(self):
        """Test aggregating registrations for all zones."""
        def mock_get_item(Key):
            zone = Key['zone']
            if zone == 'Fire':
                return {'Item': {'zone': 'Fire', 'users': {'111'}}}
            elif zone == 'Water':
                return {'Item': {'zone': 'Water', 'users': {'222', '333'}}}
            else:
                return {}

        self.mock_table.get_item.side_effect = mock_get_item

        with patch.object(RegistrationDB, "get_current_survey_date", return_value="29-06-2026"):
            all_regs = self.db.get_all_registrations()

        self.assertEqual(all_regs['Fire'], {'111': 1})
        self.assertEqual(all_regs['Water'], {'222': 1, '333': 1})
        self.assertEqual(all_regs['Earth'], {})
        self.assertEqual(all_regs['Wind'], {})
        self.assertEqual(all_regs['Whatever'], {})


if __name__ == "__main__":
    unittest.main()

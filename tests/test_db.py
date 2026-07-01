import unittest
from unittest.mock import MagicMock, patch

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
        """Test registering user adding to selected and deleting from unselected zones."""
        user_id = 123456
        # Select "Fire" and "Water"
        selected_zones = ["Fire", "Water"]
        
        self.db.register_user_activities(user_id, selected_zones)
        
        # Verify update_item calls
        # Should call ADD for Fire, Water and DELETE for Earth, Wind, Whatever
        self.assertEqual(self.mock_table.update_item.call_count, 5)
        
        # Build list of call arguments
        calls = self.mock_table.update_item.call_args_list
        
        add_zones = []
        delete_zones = []
        for call in calls:
            kwargs = call.kwargs
            zone = kwargs['Key']['zone']
            expr = kwargs['UpdateExpression']
            self.assertEqual(kwargs['ExpressionAttributeValues'], {':u': {'123456'}})
            
            if "ADD" in expr:
                add_zones.append(zone)
            elif "DELETE" in expr:
                delete_zones.append(zone)
                
        self.assertEqual(sorted(add_zones), ["Fire", "Water"])
        self.assertEqual(sorted(delete_zones), ["Earth", "Whatever", "Wind"])

    def test_clear_user_registration(self):
        """Test clearing user registration removes from all zones."""
        user_id = 987654
        self.db.clear_user_registration(user_id)
        
        self.assertEqual(self.mock_table.update_item.call_count, 5)
        
        # All expressions should be DELETE
        calls = self.mock_table.update_item.call_args_list
        for call in calls:
            self.assertIn("DELETE", call.kwargs['UpdateExpression'])

    def test_get_zone_registrants_existing(self):
        """Test retrieving list of user IDs for a zone when it has data."""
        self.mock_table.get_item.return_value = {
            'Item': {
                'zone': 'Fire',
                'users': {'123', '456'}
            }
        }
        
        registrants = self.db.get_zone_registrants('Fire')
        self.assertEqual(registrants, ['123', '456'])
        self.mock_table.get_item.assert_called_with(Key={'zone': 'Fire'})

    def test_get_zone_registrants_empty(self):
        """Test retrieving list of user IDs for a zone when there is no record."""
        self.mock_table.get_item.return_value = {}
        
        registrants = self.db.get_zone_registrants('Water')
        self.assertEqual(registrants, [])

    def test_get_all_registrations(self):
        """Test aggregating registrations for all zones."""
        # Setup mock behavior to return different users for different zones
        def mock_get_item(Key):
            zone = Key['zone']
            if zone == 'Fire':
                return {'Item': {'zone': 'Fire', 'users': {'111'}}}
            elif zone == 'Water':
                return {'Item': {'zone': 'Water', 'users': {'222', '333'}}}
            else:
                return {}
                
        self.mock_table.get_item.side_effect = mock_get_item
        
        all_regs = self.db.get_all_registrations()
        
        self.assertEqual(all_regs['Fire'], ['111'])
        self.assertEqual(all_regs['Water'], ['222', '333'])
        self.assertEqual(all_regs['Earth'], [])
        self.assertEqual(all_regs['Wind'], [])
        self.assertEqual(all_regs['Whatever'], [])


if __name__ == "__main__":
    unittest.main()

import boto3
from botocore.exceptions import ClientError
import config
class RegistrationDB:
    """Manages storing zone registrations in a DynamoDB table where 'zone' is the primary key."""
    VALID_ZONES = ["Fire", "Water", "Earth", "Wind", "Whatever"]
    def __init__(self, table_name=None, endpoint_url=None):
        self.table_name = table_name or config.DYNAMODB_TABLE_NAME
        self.endpoint_url = endpoint_url or config.DYNAMODB_ENDPOINT_URL
        # Setup AWS session parameters dynamically
        params = {}
        if config.AWS_ACCESS_KEY_ID:
            params['aws_access_key_id'] = config.AWS_ACCESS_KEY_ID
        if config.AWS_SECRET_ACCESS_KEY:
            params['aws_secret_access_key'] = config.AWS_SECRET_ACCESS_KEY
        if config.AWS_DEFAULT_REGION:
            params['region_name'] = config.AWS_DEFAULT_REGION
        if self.endpoint_url:
            params['endpoint_url'] = self.endpoint_url
        self.dynamodb = boto3.resource('dynamodb', **params)
        self.table = self.dynamodb.Table(self.table_name)

    def register_user_activities(self, user_id: int, selected_zones: list[str]) -> None:
        """
        Updates the user's registration by adding them to selected zones and removing from unselected zones.
        """
        user_id_str = str(user_id)
        for zone in self.VALID_ZONES:
            if zone in selected_zones:
                # Add user to the zone set
                try:
                    self.table.update_item(
                        Key={'zone': zone},
                        UpdateExpression="ADD #u :u",
                        ExpressionAttributeNames={"#u": "users"},
                        ExpressionAttributeValues={":u": {user_id_str}}
                    )
                except ClientError as e:
                    raise RuntimeError(f"Failed to add user to {zone}: {e}")
            else:
                # Remove user from the zone set
                try:
                    self.table.update_item(
                        Key={'zone': zone},
                        UpdateExpression="DELETE #u :u",
                        ExpressionAttributeNames={"#u": "users"},
                        ExpressionAttributeValues={":u": {user_id_str}}
                    )
                except ClientError as e:
                    raise RuntimeError(f"Failed to remove user from {zone}: {e}")

    def clear_user_registration(self, user_id: int) -> None:
        """Removes the user from all zones' registration sets."""
        self.register_user_activities(user_id, [])

    def get_zone_registrants(self, zone: str) -> list[str]:
        """Retrieves a list of user IDs registered for a specific zone."""
        if zone not in self.VALID_ZONES:
            raise ValueError(f"Invalid zone: {zone}")
        try:
            response = self.table.get_item(Key={'zone': zone})
            item = response.get('Item')
            if not item:
                return []
            users_set = item.get('users', set())
            return sorted(list(users_set))
        except ClientError as e:
            raise RuntimeError(f"Failed to fetch registrants for {zone}: {e}")

    def get_all_registrations(self) -> dict[str, list[str]]:
        """Retrieves all registrations grouped by zone."""
        registrations = {}
        for zone in self.VALID_ZONES:
            registrations[zone] = self.get_zone_registrants(zone)
        return registrations

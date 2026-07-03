import boto3
from botocore.exceptions import ClientError
from datetime import date, timedelta
import config

class RegistrationDB:
    """Manages storing weekly zone registrations in a DynamoDB table."""
    VALID_ZONES = ["Fire", "Water", "Earth", "Wind", "Whatever"]
    SURVEY_DATE_FORMAT = "%d-%m-%Y"

    def __init__(self, table_name=None, endpoint_url=None):
        self.table_name = table_name or config.DYNAMODB_TABLE_NAME
        self.endpoint_url = endpoint_url or config.DYNAMODB_ENDPOINT_URL
        params = {}
        if config.AWS_ACCESS_KEY_ID or config.AWS_SECRET_ACCESS_KEY or config.AWS_SESSION_TOKEN:
            if not (config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY):
                raise ValueError(
                    "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must both be set when manually configuring AWS credentials."
                )
            params['aws_access_key_id'] = config.AWS_ACCESS_KEY_ID
            params['aws_secret_access_key'] = config.AWS_SECRET_ACCESS_KEY
            if config.AWS_SESSION_TOKEN:
                params['aws_session_token'] = config.AWS_SESSION_TOKEN
        if config.AWS_DEFAULT_REGION:
            params['region_name'] = config.AWS_DEFAULT_REGION
        if self.endpoint_url:
            params['endpoint_url'] = self.endpoint_url
        self.dynamodb = boto3.resource('dynamodb', **params)
        self.table = self.dynamodb.Table(self.table_name)

    @staticmethod
    def get_current_survey_date(today: date | None = None) -> str:
        """Return the current survey date as DD-MM-YYYY."""
        today = today or date.today()
        return today.strftime(RegistrationDB.SURVEY_DATE_FORMAT)

    def _item_key(self, zone: str, survey_date: str) -> dict[str, str]:
        return {"survey_date": survey_date, "zone": zone}

    def _set_zone_priority(self, user_id_str: str, zone: str, survey_date: str, priority: int) -> None:
        key = self._item_key(zone, survey_date)
        try:
            existing_item = self.table.get_item(Key=key)
            item = existing_item.get("Item")
            priorities = item.get("priorities") if item else {}
            if not isinstance(priorities, dict):
                priorities = {}

            priorities = dict(priorities)
            priorities[user_id_str] = priority

            self.table.update_item(
                Key=key,
                UpdateExpression="SET #p = :p",
                ExpressionAttributeNames={"#p": "priorities"},
                ExpressionAttributeValues={":p": priorities},
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to set priority for user {user_id_str} in {zone}: {e}")

    def _remove_zone_priority(self, user_id_str: str, zone: str, survey_date: str) -> None:
        key = self._item_key(zone, survey_date)
        try:
            existing_item = self.table.get_item(Key=key)
            item = existing_item.get("Item")
            if not item:
                return

            priorities = item.get("priorities")
            if not isinstance(priorities, dict):
                return

            priorities = dict(priorities)
            if user_id_str not in priorities:
                return

            priorities.pop(user_id_str, None)
            if priorities:
                self.table.update_item(
                    Key=key,
                    UpdateExpression="SET #p = :p",
                    ExpressionAttributeNames={"#p": "priorities"},
                    ExpressionAttributeValues={":p": priorities},
                )
            else:
                self.table.update_item(
                    Key=key,
                    UpdateExpression="REMOVE #p",
                    ExpressionAttributeNames={"#p": "priorities"},
                )
        except ClientError as e:
            raise RuntimeError(f"Failed to remove priority for user {user_id_str} from {zone}: {e}")

    def register_user_activities(self, user_id: int, selected_zones: list[str], survey_date: str | None = None) -> None:
        """Updates the user's registration for the current survey week."""
        survey_date = survey_date or self.get_current_survey_date()
        user_id_str = str(user_id)
        selected_priorities = {zone: index + 1 for index, zone in enumerate(selected_zones)}

        for zone in self.VALID_ZONES:
            if zone in selected_priorities:
                self._set_zone_priority(user_id_str, zone, survey_date, selected_priorities[zone])
            else:
                self._remove_zone_priority(user_id_str, zone, survey_date)

    def clear_user_registration(self, user_id: int, survey_date: str | None = None) -> None:
        """Removes the user from all zones for the current survey week."""
        self.register_user_activities(user_id, [], survey_date=survey_date)

    def get_zone_registrants(self, zone: str, survey_date: str | None = None) -> dict[str, int]:
        """Retrieves registered user IDs and priorities for a specific zone and survey week."""
        if zone not in self.VALID_ZONES:
            raise ValueError(f"Invalid zone: {zone}")
        survey_date = survey_date or self.get_current_survey_date()
        try:
            response = self.table.get_item(Key=self._item_key(zone, survey_date))
            item = response.get('Item')
            if not item:
                return {}
            if 'priorities' in item and isinstance(item['priorities'], dict):
                return {user_id: int(priority) for user_id, priority in item['priorities'].items()}
            users_set = item.get('users', set())
            return {user_id: 1 for user_id in users_set}
        except ClientError as e:
            raise RuntimeError(f"Failed to fetch registrants for {zone}: {e}")

    def get_all_registrations(self, survey_date: str | None = None) -> dict[str, dict[str, int]]:
        """Retrieves all registrations for the current survey week, grouped by zone."""
        survey_date = survey_date or self.get_current_survey_date()
        registrations = {}
        for zone in self.VALID_ZONES:
            registrations[zone] = self.get_zone_registrants(zone, survey_date=survey_date)
        return registrations

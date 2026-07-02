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
        """Return the current survey week start date as DD-MM-YYYY."""
        today = today or date.today()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.strftime(RegistrationDB.SURVEY_DATE_FORMAT)

    def _item_key(self, zone: str, survey_date: str) -> dict[str, str]:
        return {"survey_date": survey_date, "zone": zone}

    def register_user_activities(self, user_id: int, selected_zones: list[str], survey_date: str | None = None) -> None:
        """Updates the user's registration for the current survey week."""
        survey_date = survey_date or self.get_current_survey_date()
        user_id_str = str(user_id)
        for zone in self.VALID_ZONES:
            key = self._item_key(zone, survey_date)
            if zone in selected_zones:
                try:
                    self.table.update_item(
                        Key=key,
                        UpdateExpression="ADD #u :u",
                        ExpressionAttributeNames={"#u": "users"},
                        ExpressionAttributeValues={":u": {user_id_str}}
                    )
                except ClientError as e:
                    raise RuntimeError(f"Failed to add user to {zone}: {e}")
            else:
                try:
                    self.table.update_item(
                        Key=key,
                        UpdateExpression="DELETE #u :u",
                        ExpressionAttributeNames={"#u": "users"},
                        ExpressionAttributeValues={":u": {user_id_str}}
                    )
                except ClientError as e:
                    raise RuntimeError(f"Failed to remove user from {zone}: {e}")

    def clear_user_registration(self, user_id: int, survey_date: str | None = None) -> None:
        """Removes the user from all zones for the current survey week."""
        self.register_user_activities(user_id, [], survey_date=survey_date)

    def get_zone_registrants(self, zone: str, survey_date: str | None = None) -> list[str]:
        """Retrieves a list of user IDs registered for a specific zone and survey week."""
        if zone not in self.VALID_ZONES:
            raise ValueError(f"Invalid zone: {zone}")
        survey_date = survey_date or self.get_current_survey_date()
        try:
            response = self.table.get_item(Key=self._item_key(zone, survey_date))
            item = response.get('Item')
            if not item:
                return []
            users_set = item.get('users', set())
            return sorted(list(users_set))
        except ClientError as e:
            raise RuntimeError(f"Failed to fetch registrants for {zone}: {e}")

    def get_all_registrations(self, survey_date: str | None = None) -> dict[str, list[str]]:
        """Retrieves all registrations for the current survey week, grouped by zone."""
        survey_date = survey_date or self.get_current_survey_date()
        registrations = {}
        for zone in self.VALID_ZONES:
            registrations[zone] = self.get_zone_registrants(zone, survey_date=survey_date)
        return registrations

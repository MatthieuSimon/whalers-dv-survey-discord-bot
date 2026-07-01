import json

import requests

import config
from db import RegistrationDB
from survey_payload import build_survey_components, build_survey_embed

DISCORD_API_BASE = "https://discord.com/api/v10"


def publish_survey_message(db: RegistrationDB) -> dict[str, object]:
    embed = build_survey_embed(db.get_all_registrations())
    payload = {
        "embeds": [embed],
        "components": build_survey_components(),
    }

    response = requests.post(
        f"{DISCORD_API_BASE}/channels/{config.SURVEY_CHANNEL_ID}/messages",
        headers={
            "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def handler(event, context):
    config.validate_config()
    db = RegistrationDB()

    result = publish_survey_message(db)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message_id": result.get("id"),
            "channel_id": result.get("channel_id"),
            "timestamp": result.get("timestamp"),
        }),
    }

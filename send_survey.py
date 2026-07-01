import json

import requests

import config
from db import RegistrationDB
from survey_payload import build_survey_components, build_survey_embed

DISCORD_API_BASE = "https://discord.com/api/v10"


def publish_survey_message(db: RegistrationDB) -> dict[str, object]:
    payload = {
        "embeds": [build_survey_embed(db.get_all_registrations())],
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


def main():
    config.validate_config()
    db = RegistrationDB()
    result = publish_survey_message(db)
    print(
        f"Successfully sent survey message (ID: {result.get('id')}) "
        f"to channel {result.get('channel_id')}"
    )


if __name__ == "__main__":
    main()

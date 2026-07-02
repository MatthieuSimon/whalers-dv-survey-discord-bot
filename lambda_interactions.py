import base64
import json

import requests
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

import config
from db import RegistrationDB
from survey_payload import SURVEY_SELECT_CUSTOM_ID, build_survey_embed

DISCORD_API_BASE = "https://discord.com/api/v10"


def _normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in (headers or {}).items()}


def _get_body_bytes(event: dict) -> bytes:
    body = event.get("body", "")
    if isinstance(body, str):
        if event.get("isBase64Encoded"):
            return base64.b64decode(body)
        return body.encode("utf-8")
    if isinstance(body, bytes):
        return body
    return json.dumps(body).encode("utf-8")


def verify_discord_request(headers: dict[str, str], body: bytes) -> None:
    signature = headers.get("x-signature-ed25519")
    timestamp = headers.get("x-signature-timestamp")
    if not signature or not timestamp:
        raise ValueError("Missing Discord request signature headers.")

    verify_key = VerifyKey(bytes.fromhex(config.DISCORD_PUBLIC_KEY))
    try:
        verify_key.verify(timestamp.encode("utf-8") + body, bytes.fromhex(signature))
    except BadSignatureError as exc:
        raise ValueError("Invalid Discord request signature.") from exc


def _patch_message(channel_id: str, message_id: str, embed: dict) -> None:
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}"
    response = requests.patch(
        url,
        headers={
            "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"embeds": [embed]},
        timeout=10,
    )
    response.raise_for_status()


def _get_user_id(payload: dict) -> int:
    user = payload.get("member", {}).get("user") or payload.get("user")
    if not user or "id" not in user:
        raise ValueError("Unable to read user id from interaction payload.")
    return int(user["id"])


def _response(body: dict[str, object]) -> dict[str, object]:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    config.validate_config()
    headers = _normalize_headers(event.get("headers", {}))
    body_bytes = _get_body_bytes(event)
    verify_discord_request(headers, body_bytes)

    payload = json.loads(body_bytes)
    interaction_type = payload.get("type")

    if interaction_type == 1:
        return _response({"type": 1})

    if interaction_type != 3:
        return _response({"type": 4, "data": {"content": "Unsupported interaction type.", "flags": 64}})

    data = payload.get("data", {})
    if data.get("custom_id") != SURVEY_SELECT_CUSTOM_ID:
        return _response({"type": 4, "data": {"content": "Unknown interaction.", "flags": 64}})

    selected_zones = data.get("values", [])
    user_id = _get_user_id(payload)
    db = RegistrationDB()

    if "Clear" in selected_zones:
        db.clear_user_registration(user_id)
        reply_text = "🗑️ Your registration has been cleared."
    else:
        db.register_user_activities(user_id, selected_zones)
        zones_formatted = ", ".join([f"**{z}**" for z in selected_zones])
        reply_text = f"✅ Your registration has been updated for: {zones_formatted}"

    channel_id = payload.get("channel_id") or str(config.SURVEY_CHANNEL_ID)
    message_id = payload.get("message", {}).get("id")
    if not message_id:
        return _response({"type": 4, "data": {"content": "Unable to update survey message.", "flags": 64}})

    survey_date = db.get_current_survey_date()
    embed = build_survey_embed(db.get_all_registrations(survey_date=survey_date), survey_date)
    _patch_message(channel_id, message_id, embed)

    return _response({"type": 4, "data": {"content": reply_text, "flags": 64}})

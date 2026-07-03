from typing import Any

VALID_ZONES = ["Fire", "Water", "Earth", "Wind", "Whatever"]
EMOJI_MAP = {
    "Fire": "🔥",
    "Water": "💧",
    "Earth": "🪨",
    "Wind": "💨",
    "Whatever": "🤷",
}
SURVEY_SELECT_CUSTOM_ID = "survey_select"


def _normalize_user_id(user_id: Any) -> str:
    normalized = str(user_id)
    if isinstance(user_id, str) and normalized.startswith("<@") and normalized.endswith(">"):
        normalized = normalized[2:-1]
    return normalized


def format_zone_field(user_priorities: list[str] | dict[str, int]) -> str:
    if not user_priorities:
        return "*No registrations yet*"

    if isinstance(user_priorities, dict):
        ordered_users = sorted(user_priorities.items(), key=lambda pair: pair[1])
    else:
        ordered_users = [(user_id, index + 1) for index, user_id in enumerate(user_priorities)]

    mentions_list = ", ".join(
        f"<@{user_id}> ({priority})"
        for user_id, priority in ordered_users
    )
    return f"**Count:** {len(ordered_users)}\n**Registered:** {mentions_list}"


def build_survey_embed(registrations: dict[str, list[str] | dict[str, int]], survey_date: str) -> dict[str, Any]:
    fields = []
    for zone in VALID_ZONES:
        fields.append(
            {
                "name": f"{EMOJI_MAP.get(zone, '🔹')} {zone}",
                "value": format_zone_field(registrations.get(zone, [])),
                "inline": False,
            }
        )

    return {
        "title": f"Weekly Zone Registration Survey — {survey_date}",
        "description": "Select the zones you want to register for this week. You can choose multiple options from the dropdown below or clear your registration at any time.",
        "color": 0x5865F2,
        "fields": fields,
        "footer": {"text": "Updates automatically. Ephemeral confirmations will be sent for your selections."},
    }


def build_survey_components() -> list[dict[str, Any]]:
    options = [
        {"label": "Fire", "value": "Fire", "description": "Register for Fire zone", "emoji": {"name": "🔥"}},
        {"label": "Water", "value": "Water", "description": "Register for Water zone", "emoji": {"name": "💧"}},
        {"label": "Earth", "value": "Earth", "description": "Register for Earth zone", "emoji": {"name": "🪨"}},
        {"label": "Wind", "value": "Wind", "description": "Register for Wind zone", "emoji": {"name": "💨"}},
        {"label": "Whatever", "value": "Whatever", "description": "Register for Whatever (flexible)", "emoji": {"name": "🤷"}},
        {"label": "Clear Registration", "value": "Clear", "description": "Clear all your registered zones", "emoji": {"name": "🗑️"}},
    ]

    select = {
        "type": 3,
        "custom_id": SURVEY_SELECT_CUSTOM_ID,
        "placeholder": "Choose your zone(s)...",
        "min_values": 1,
        "max_values": 6,
        "options": options,
    }

    return [{"type": 1, "components": [select]}]

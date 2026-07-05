from typing import Any

VALID_ZONES = ["Fire", "Water", "Earth", "Wind", "Whatever"]
SURVEY_ROLE_MENTION = "<@&1440069423913242624>"
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


def build_survey_message_content(survey_date: str) -> str:
    return f"{SURVEY_ROLE_MENTION} choisissez votre zone pour cette semaine — {survey_date}"


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
        "title": f"Choisissez votre zone pour cette semaine — {survey_date}",
        "description": "Sélectionnez les zones pour lesquelles vous souhaitez vous inscrire cette semaine. Vous pouvez choisir plusieurs options dans le menu déroulant ci-dessous ou annuler votre inscription à tout moment.",
        "color": 0x5865F2,
        "fields": fields,
        "footer": {"text": "Mises à jour automatiquement. Des confirmations seront envoyées pour vos sélections."},
    }


def build_survey_components() -> list[dict[str, Any]]:
    options = [
        {"label": "Feu", "value": "Fire", "description": "S'inscrire à la zone Feu", "emoji": {"name": "🔥"}},
        {"label": "Eau", "value": "Water", "description": "S'inscrire à la zone Eau", "emoji": {"name": "💧"}},
        {"label": "Terre", "value": "Earth", "description": "S'inscrire à la zone Terre", "emoji": {"name": "🪨"}},
        {"label": "Vent", "value": "Wind", "description": "S'inscrire à la zone Vent", "emoji": {"name": "💨"}},
        {"label": "Peu importe", "value": "Whatever", "description": "S'inscrire à la zone Peu importe (flexible)", "emoji": {"name": "🤷"}},
        {"label": "Effacer l'inscription", "value": "Clear", "description": "Effacer toutes vos inscriptions", "emoji": {"name": "🗑️"}},
    ]

    select = {
        "type": 3,
        "custom_id": SURVEY_SELECT_CUSTOM_ID,
        "placeholder": "Choisissez votre zone(s)...",
        "min_values": 1,
        "max_values": 6,
        "options": options,
    }

    return [{"type": 1, "components": [select]}]

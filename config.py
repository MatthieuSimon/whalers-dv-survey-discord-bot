import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Required Configs
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
SURVEY_CHANNEL_ID_RAW = os.getenv("SURVEY_CHANNEL_ID")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")

# Optional Configs (AWS connection details)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")

# Validate required variables
missing_vars = []
if not DISCORD_BOT_TOKEN:
    missing_vars.append("DISCORD_BOT_TOKEN")
if not DISCORD_PUBLIC_KEY:
    missing_vars.append("DISCORD_PUBLIC_KEY")
if not SURVEY_CHANNEL_ID_RAW:
    missing_vars.append("SURVEY_CHANNEL_ID")
if not DYNAMODB_TABLE_NAME:
    missing_vars.append("DYNAMODB_TABLE_NAME")

if missing_vars:
    # We do not raise an error during test execution if we are mocking config.
    # But for runtime, we raise an error.
    pass

# Parse SURVEY_CHANNEL_ID
SURVEY_CHANNEL_ID = None
if SURVEY_CHANNEL_ID_RAW:
    try:
        SURVEY_CHANNEL_ID = int(SURVEY_CHANNEL_ID_RAW)
    except ValueError:
        raise ValueError(f"SURVEY_CHANNEL_ID must be a valid integer, got '{SURVEY_CHANNEL_ID_RAW}'")


def validate_config():
    """Verify that all required environment variables are set."""
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

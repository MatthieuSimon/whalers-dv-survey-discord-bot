# Whalers Discord Survey Bot

A lightweight Discord survey system for zone registration, now updated for serverless deployment.

## Overview

This repository contains:

- `survey_payload.py` — reusable survey embed and component JSON builders
- `send_survey.py` — publish the survey message via Discord REST
- `lambda_publish.py` — AWS Lambda handler for scheduled or triggered survey publishing
- `lambda_interactions.py` — AWS Lambda handler for Discord webhook interaction events
- `db.py` — DynamoDB-backed registration storage
- `config.py` — environment-driven configuration

## Architecture

The updated serverless design separates publish and receive responsibilities:

1. `lambda_publish.handler` sends the survey message to the Discord channel.
2. Discord users select zone(s) in the message dropdown.
3. Discord sends interaction events to `lambda_interactions.handler`.
4. The interaction handler verifies Discord signatures, updates DynamoDB, patches the survey embed, and sends an ephemeral confirmation.

## Required environment variables

Configure the following values in AWS Lambda or local `.env` for development:

- `DISCORD_BOT_TOKEN` — your Discord bot token
- `DISCORD_PUBLIC_KEY` — your Discord application's public key
- `SURVEY_CHANNEL_ID` — numeric ID of the target channel
- `DYNAMODB_TABLE_NAME` — DynamoDB table name
- `AWS_ACCESS_KEY_ID` — AWS credentials for DynamoDB access (optional when using Lambda execution role)
- `AWS_SECRET_ACCESS_KEY` — AWS credentials for DynamoDB access (optional when using Lambda execution role)
- `AWS_SESSION_TOKEN` — AWS session token for temporary credentials, required if using STS-based credentials
- `AWS_DEFAULT_REGION` — AWS region (default: `us-east-1`)
- `DYNAMODB_ENDPOINT_URL` — optional local DynamoDB endpoint for testing

## Local development

1. Create and activate your virtual environment.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

If the project does not include `requirements.txt`, use:

```powershell
python -m pip install discord.py boto3 python-dotenv requests PyNaCl
```

3. Copy `.env.example` to `.env` and fill in the values.

4. Run the send publisher directly:

```powershell
python send_survey.py
```

## Lambda deployment

### Publish Lambda

- Handler: `lambda_publish.handler`
- Trigger: scheduled CloudWatch Events / EventBridge or Step Functions
- Purpose: send the survey message to Discord

### Interaction Lambda

- Handler: `lambda_interactions.handler`
- Trigger: API Gateway or Lambda function URL
- Purpose: receive Discord interaction webhooks

### Discord app configuration

In the Discord Developer Portal, set the interaction endpoint URL to the API Gateway or function URL for `lambda_interactions`.

### Interaction endpoint flow

1. Discord sends a POST request to the endpoint.
2. `lambda_interactions` validates the request signature.
3. It processes survey component interactions and updates the embed.

## Notes

- `send_survey.py` is now REST-based and can be used as a local publisher or as a reference implementation for Lambda.
- The DynamoDB table stores survey registrations per zone.

## File summary

- `survey_payload.py` — build survey embed + component JSON
- `lambda_publish.py` — publish handler for scheduled Lambda
- `lambda_interactions.py` — interaction webhook handler
- `send_survey.py` — local REST publisher script
- `db.py` — DynamoDB access
- `config.py` — environment configuration

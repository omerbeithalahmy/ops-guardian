import requests
import json
from slack_sdk import WebClient
from app.core.config import settings

def send_alert(message: str, color: str = "#ff0000"):
    if not settings.SLACK_WEBHOOK_URL:
        from app.services.slack_listener import logger
        logger.warning("SLACK_WEBHOOK_URL is missing. Cannot send alert report.")
        return
    
    payload = {
        "attachments": [
            {
            "color": color,
            "text": message,
            "mrkdwn_in": ["text"]
            }
        ]
    }

    try:
        requests.post(
            settings.SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        from app.services.slack_listener import logger
        logger.error(f"Error sending Slack alert via Webhook: {e}")

def send_block_message(blocks: list):
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_CHANNEL_ID:
        return
    
    client = WebClient(token=settings.SLACK_BOT_TOKEN)
    try:
        client.chat_postMessage(
            channel=settings.SLACK_CHANNEL_ID,
            blocks=blocks,
            text="OpsGuardian Control Center"
        )
    except Exception as e:
        print(f"Error sending block message: {e}")

def send_control_center():
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "OpsGuardian Control Center"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Select a category to trigger a real-time AWS scan:"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Scan Costs"},
                    "action_id": "trigger_scan_costs",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Scan Security"},
                    "action_id": "trigger_scan_security",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Scan Hygiene"},
                    "action_id": "trigger_scan_hygiene",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Scan Network"},
                    "action_id": "trigger_scan_network",
                    "style": "primary"
                }
            ]
        }
    ]
    send_block_message(blocks)
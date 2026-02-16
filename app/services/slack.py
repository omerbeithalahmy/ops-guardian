import requests
import json
from app.core.config import settings

def send_alert(message: str, color: str = "#ff0000"):
    if not settings.SLACK_WEBHOOK_URL:
        print("No Slack Webhook URL found.")
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
        response = requests.post(
            settings.SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            print(f"Failed to send Slack alert: {response.text}")
    except Exception as e:
        print(f"Error sending Slack alert: {e}")
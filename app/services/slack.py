import requests
import json
from slack_sdk import WebClient
from app.core.config import settings

def purge_channel_history(channel_id):
    if not settings.SLACK_BOT_TOKEN:
        return
    
    client = WebClient(token=settings.SLACK_BOT_TOKEN)
    try:
        response = client.conversations_history(channel=channel_id, limit=30)
        if not response.get("ok"):
            from app.services.slack_listener import logger
            logger.error(f"Failed to fetch history: {response.get('error')}")
            return

        messages = response.get("messages", [])
        for msg in messages:
            ts = msg.get("ts")
            try:
                client.chat_delete(channel=channel_id, ts=ts)
            except Exception:
                continue
    except Exception as e:
        from app.services.slack_listener import logger
        logger.error(f"Critical error during channel purge: {e}")

def send_block_message(blocks: list):
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_CHANNEL_ID:
        return
    
    client = WebClient(token=settings.SLACK_BOT_TOKEN)
    try:
        client.chat_postMessage(
            channel=settings.SLACK_CHANNEL_ID,
            blocks=blocks,
            text="OpsGuardian Activity"
        )
    except Exception as e:
        print(f"Error sending block message: {e}")

def get_remediation_blocks(category, resources):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"OpsGuardian | {category.upper()} INVESTIGATION"}
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"*Environment:* AWS Production | *Region:* `{settings.AWS_REGION}`"}
            ]
        },
        {"type": "divider"}
    ]

    if resources:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{len(resources)} findings detected.* Please review and select resources for automatic resolution."}
        })
        
        options = []
        for res in resources:
            res_id = res.get("id") or res.get("name")
            res_type = res.get("type", category)
            res_display = res.get("display") or f"{res_type}: {res_id}"
            
            options.append({
                "text": {"type": "plain_text", "text": res_display},
                "value": f"{res_id}:{res_type}"
            })

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "checkboxes",
                    "action_id": "select_resources_to_delete",
                    "options": options[:10]
                }
            ]
        })
        
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Resolve Selected"},
                    "action_id": "remediate_selected",
                    "style": "danger"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Cancel Scan"},
                    "action_id": "cancel_to_control"
                }
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Zero findings. Your environment is currently compliant with our security and cost policies."}
        })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Return to Dashboard"},
                    "action_id": "cancel_to_control",
                    "style": "primary"
                }
            ]
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "Powered by OpsGuardian Interactive Resolution Engine"}
        ]
    })
    
    return blocks
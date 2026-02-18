import logging
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from app.core.config import settings
from app.routers import costs, security, hygiene, network
from app.services import slack, aws

logger = logging.getLogger("opsguardian")

def get_control_blocks(last_action_msg=None):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "OpsGuardian | CONTROL CENTER"}
        }
    ]
    
    if last_action_msg:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*System Alert:* {last_action_msg}"}
        })
        blocks.append({"type": "divider"})

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Welcome to your Cloud Security Hub. Select a category below to perform an automated investigation across your AWS environment."}
    })

    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Scan Costs"}, "action_id": "trigger_scan_costs", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "Scan Security"}, "action_id": "trigger_scan_security", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "Scan Hygiene"}, "action_id": "trigger_scan_hygiene", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "Scan Network"}, "action_id": "trigger_scan_network", "style": "primary"}
        ]
    })
    
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "OpsGuardian | Connected to Cloud Environment"}
        ]
    })
    
    return blocks

def start_slack_listener():
    if not settings.SLACK_APP_TOKEN or not settings.SLACK_BOT_TOKEN:
        logger.error("Tokens missing.")
        return

    app = App(token=settings.SLACK_BOT_TOKEN)

    @app.command("/opsguardian")
    def handle_command(ack, body, respond):
        ack()
        channel_id = body["channel_id"]
        
        logger.info(f"Purging channel {channel_id}...")
        slack.purge_channel_history(channel_id)
        
        respond(
            text="OpsGuardian Control Center", 
            blocks=get_control_blocks(),
            response_type="in_channel"
        )

    @app.action("trigger_scan_costs")
    def handle_scan_costs(ack, body, respond):
        ack()
        resources = costs.get_costs_resources()
        blocks = slack.get_remediation_blocks("costs", resources)
        respond(text="OpsGuardian Cost Report", blocks=blocks, replace_original=True)

    @app.action("trigger_scan_security")
    def handle_scan_security(ack, body, respond):
        ack()
        resources = security.get_security_resources()
        blocks = slack.get_remediation_blocks("security", resources)
        respond(text="OpsGuardian Security Report", blocks=blocks, replace_original=True)

    @app.action("trigger_scan_hygiene")
    def handle_scan_hygiene(ack, body, respond):
        ack()
        resources = hygiene.get_hygiene_resources()
        blocks = slack.get_remediation_blocks("hygiene", resources)
        respond(text="OpsGuardian Hygiene Report", blocks=blocks, replace_original=True)

    @app.action("trigger_scan_network")
    def handle_scan_network(ack, body, respond):
        ack()
        resources = network.get_network_resources()
        blocks = slack.get_remediation_blocks("network", resources)
        respond(text="OpsGuardian Network Report", blocks=blocks, replace_original=True)

    @app.action("select_resources_to_delete")
    def handle_selection(ack):
        ack()

    @app.action("remediate_selected")
    def handle_remediate_selected(ack, body, client):
        ack()
        selected_options = []
        state_vals = body.get("state", {}).get("values", {})
        for b_id, acts in state_vals.items():
            for a_id, act in acts.items():
                if a_id == "select_resources_to_delete":
                    selected_options = act.get("selected_options", [])
        
        if not selected_options:
            return

        items = [opt['value'] for opt in selected_options]
        
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "confirmation_modal",
                "private_metadata": json.dumps({"items": items, "response_url": body["response_url"]}),
                "title": {"type": "plain_text", "text": "Confirm Resolution"},
                "submit": {"type": "plain_text", "text": "Confirm and Delete"},
                "close": {"type": "plain_text", "text": "Cancel"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "Caution: You are about to permanently remove selected cloud resources from your environment. This action cannot be undone."}
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Selected Resources:*\n{', '.join(items[:5])}" + ("..." if len(items) > 5 else "")}
                    }
                ]
            }
        )

    @app.view("confirmation_modal")
    def handle_modal_submission(ack, body, view, client):
        ack()
        metadata = json.loads(view["private_metadata"])
        items = metadata["items"]
        response_url = metadata["response_url"]
        
        deletes = {}
        for item in items:
            parts = item.split(":")
            if len(parts) != 2: continue
            r_id, r_type = parts
            if r_type not in deletes: deletes[r_type] = []
            deletes[r_type].append(r_id)
        
        s_list, f_list = [], []
        for r_type, ids in deletes.items():
            try:
                s, f = [], []
                if r_type == "volume": s, f = aws.delete_volumes(ids)
                elif r_type == "eip": s, f = aws.release_elastic_ips(ids)
                elif r_type == "instance": s, f = aws.terminate_instances(ids)
                elif r_type == "sg": s, f = aws.delete_security_groups(ids)
                elif r_type == "s3": s, f = aws.delete_s3_buckets(ids)
                elif r_type == "iam": s, f = aws.delete_iam_users(ids)
                elif r_type == "vpc": s, f = aws.delete_vpcs(ids)
                
                if s: s_list.append(f"Successfully deleted {r_type}(s): {', '.join(s)}")
                if f: f_list.append(f"Failed to delete {r_type}(s): {', '.join(f)}")
            except Exception as e:
                f_list.append(f"System Error ({r_type}): {e}")

        msg = "Investigation Report - Resolution Complete\n"
        if s_list: msg += "\n".join(s_list) + "\n"
        if f_list: msg += "\n" + "\n".join(f_list)

        import requests
        payload = {
            "text": "OpsGuardian Control Center",
            "blocks": get_control_blocks(last_action_msg=msg),
            "replace_original": True
        }
        requests.post(response_url, json=payload)

    @app.action("cancel_to_control")
    def handle_cancel_to_control(ack, respond):
        ack()
        respond(text="OpsGuardian Control Center", blocks=get_control_blocks(), replace_original=True)

    logger.info("Connecting Listener...")
    handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
    handler.start()

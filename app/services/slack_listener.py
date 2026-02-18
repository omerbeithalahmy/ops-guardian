import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from app.core.config import settings
from app.routers import costs, security, hygiene, network
from app.services import slack

logger = logging.getLogger("opsguardian")

def get_control_blocks():
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "OpsGuardian Control Center"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Select a category to trigger a real-time AWS scan:"}
        },
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Scan Costs"}, "action_id": "trigger_scan_costs", "style": "primary"},
                {"type": "button", "text": {"type": "plain_text", "text": "Scan Security"}, "action_id": "trigger_scan_security", "style": "primary"},
                {"type": "button", "text": {"type": "plain_text", "text": "Scan Hygiene"}, "action_id": "trigger_scan_hygiene", "style": "primary"},
                {"type": "button", "text": {"type": "plain_text", "text": "Scan Network"}, "action_id": "trigger_scan_network", "style": "primary"}
            ]
        }
    ]

def start_slack_listener():
    if not settings.SLACK_APP_TOKEN or not settings.SLACK_BOT_TOKEN:
        logger.error("SLACK_APP_TOKEN or SLACK_BOT_TOKEN is missing!")
        return

    logger.info("Initializing Slack App...")
    try:
        app = App(token=settings.SLACK_BOT_TOKEN)

        @app.command("/opsguardian")
        def handle_command(ack, respond):
            ack()
            respond(text="OpsGuardian Control Center", blocks=get_control_blocks())

        @app.action("trigger_scan_costs")
        def handle_scan_costs(ack, body, respond):
            ack()
            logger.info("Button click: trigger_scan_costs")
            costs.scan_costs()
            respond(text="OpsGuardian Control Center", blocks=get_control_blocks(), replace_original=False)

        @app.action("trigger_scan_security")
        def handle_scan_security(ack, body, respond):
            ack()
            logger.info("Button click: trigger_scan_security")
            security.scan_security()
            respond(text="OpsGuardian Control Center", blocks=get_control_blocks(), replace_original=False)

        @app.action("trigger_scan_hygiene")
        def handle_scan_hygiene(ack, body, respond):
            ack()
            logger.info("Button click: trigger_scan_hygiene")
            hygiene.scan_hygiene()
            respond(text="OpsGuardian Control Center", blocks=get_control_blocks(), replace_original=False)

        @app.action("trigger_scan_network")
        def handle_scan_network(ack, body, respond):
            ack()
            logger.info("Button click: trigger_scan_network")
            network.scan_network()
            respond(text="OpsGuardian Control Center", blocks=get_control_blocks(), replace_original=False)

        logger.info("Connecting to Slack via Socket Mode...")
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        logger.info("Connected! OpsGuardian is listening for Slack commands.")
        handler.start()
    except Exception as e:
        logger.error(f"Error starting Slack listener: {e}")

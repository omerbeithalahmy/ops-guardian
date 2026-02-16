from fastapi import FastAPI
import boto3
import os
import requests
import json

app = FastAPI()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def get_ec2_client():
    return boto3.client('ec2', region_name='us-east-1')

def send_slack_alert(message: str, color: str = "#ff0000"):
    if not SLACK_WEBHOOK_URL:
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
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            print(f"Failed to send Slack alert: {response.text}")
    except Exception as e:
        print(f"Error sending Slack alert: {e}")

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "OpsGuardian is up and running!"}

@app.get("/scan/volumes")
def scan_volumes():
    ec2_client = get_ec2_client()
    response = ec2_client.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )

    orphan_volumes = []
    total_wasted_gb = 0
    for volume in response['Volumes']:
        vol_data = {
            "id": volume['VolumeId'],
            "size": volume['Size'],
            "type": volume['VolumeType'],
            "created": str(volume['CreateTime'])
        }
        orphan_volumes.append(vol_data)
        total_wasted_gb += volume['Size']

    count = len(orphan_volumes)
    if count > 0:
        msg = f"OpsGuardian Alert*\nFound *{count}* unattached volumes.\nWasted storage: *{total_wasted_gb}GB*"
        send_slack_alert(msg, color="#ff9900")
    else:
        send_slack_alert("OpsGuardian Scan: All clean! No wasted volumes found.", color="#36a64f")
    
    return {
        "count": len(orphan_volumes),
        "total_wasted_gb": total_wasted_gb,
        "volumes": orphan_volumes
    }

@app.post("/cleanup/volumes")
def cleanup_volumes(dry_run: bool = True):
    client = get_ec2_client()
    response = client.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )
    candidates = response['Volumes']
    report = {
        "deleted": [],
        "errors": [],
        "dry_run_mode": dry_run
    }

    if not candidates:
        return {"message": "No volumes to clean", "report": report}
    
    for volume in candidates:
        v_id = volume["VolumeId"]
        if dry_run:
            report['deleted'].append(f"DRY_RUN would delete {v_id}")
        else:
            try:
                client.delete_volume(VolumeId=v_id)
                report['deleted'].append(f"Successfully deleted {v_id}")
            except Exception as e:
                report['errors'].append(f"Failed to delete {v_id}: {str(e)}")

    mode_text = "[DRY RUN]" if dry_run else "[LIVE ACTION]"

    slack_msg = f"*OpsGuardian Cleanup Report* {mode_text}\n"
    slack_msg += "\n".join(report['deleted'])

    if report['errors']:
        slack_msg += "\n Errors: \n" + "\n".join(report['errors'])
        send_slack_alert(slack_msg, color="#ff0000")
    else:
        send_slack_alert(slack_msg, color="#36a64f" if not dry_run else "#439fe0")
    
    return {"status": "completed", "report": report}

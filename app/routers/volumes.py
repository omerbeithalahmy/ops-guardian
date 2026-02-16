from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/volumes", tags=["Volumes"])

@router.get("/scan") 
def scan_volumes():
    volumes = aws.list_available_volumes()
    
    orphan_volumes = []
    total_wasted_gb = 0
    
    for vol in volumes:
        orphan_volumes.append({
            "id": vol['VolumeId'],
            "size": vol['Size'],
            "type": vol['VolumeType'],
            "created": str(vol['CreateTime'])
        })
        total_wasted_gb += vol['Size']

    count = len(orphan_volumes)
    if count > 0:
        msg = f"OpsGuardian Alert*\nFound *{count}* unattached volumes.\nWasted storage: *{total_wasted_gb}GB*"
        slack.send_alert(msg, color="#ff9900")
    else:
        slack.send_alert("OpsGuardian Scan: All clean! No wasted volumes found.", color="#36a64f")
    
    return {
        "count": len(orphan_volumes),
        "total_wasted_gb": total_wasted_gb,
        "volumes": orphan_volumes
    }

@router.post("/cleanup") # הכתובת תהיה /volumes/cleanup
def cleanup_volumes(dry_run: bool = True):
    volumes = aws.list_available_volumes()
    
    report = {"deleted": [], "errors": [], "dry_run_mode": dry_run}

    if not volumes:
        return {"message": "No volumes to clean", "report": report}

    for vol in volumes:
        v_id = vol["VolumeId"]
        if dry_run:
            report['deleted'].append(f"[DRY RUN] Would delete {v_id}")
        else:
            try:
                aws.delete_volume(v_id)
                report['deleted'].append(f"Successfully deleted {v_id}")
            except Exception as e:
                report['errors'].append(f"Failed to delete {v_id}: {str(e)}")

        mode_text = "[DRY RUN]" if dry_run else "[LIVE ACTION]"

    slack_msg = f"*OpsGuardian Cleanup Report* {mode_text}\n"
    slack_msg += "\n".join(report['deleted'])

    if report['errors']:
        slack_msg += "\n Errors: \n" + "\n".join(report['errors'])
        slack.send_alert(slack_msg, color="#ff0000")
    else:
        slack.send_alert(slack_msg, color="#36a64f" if not dry_run else "#439fe0")
    
    return {"status": "completed", "report": report}

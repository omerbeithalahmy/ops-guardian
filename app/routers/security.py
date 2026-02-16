from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/security", tags=["Security"])

@router.get("/scan-open-ports")
def scan_open_ports():
    bad_sgs = aws.scan_security_groups()
    count = len(bad_sgs)

    if count > 0:
        msg = f"*Security Alert*\nFound *{count}* Security Groups with SSH open to the world"
        for sg in bad_sgs:
            msg += f"\n• `{sg['id']}` ({sg['name']})"
        slack.send_alert(msg, color="#ff0000")
    else:
        slack.send_alert("Security Scan: System is secure. No open SSH ports found.", color="#36a64f")
    return {"count": count, "issues": bad_sgs}
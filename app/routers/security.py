from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/security", tags=["Security"])

def get_security_resources():
    open_sgs = aws.scan_open_ssh_security_groups()
    public_buckets = aws.scan_public_s3_buckets()
    no_mfa = aws.scan_iam_users_without_mfa()

    all_resources = []
    for sg in open_sgs:
        all_resources.append({"id": sg['id'], "display": f"Security Group {sg['id']} (Open SSH)", "type": "sg"})
    for b in public_buckets:
        all_resources.append({"id": b['name'], "display": f"S3 Bucket {b['name']} (Public Access)", "type": "s3"})
    for u in no_mfa:
        all_resources.append({"id": u['username'], "display": f"IAM User {u['username']} (No MFA)", "type": "iam"})
    
    return all_resources

@router.get("")
def scan_security():
    resources = get_security_resources()
    blocks = slack.get_remediation_blocks("security", resources)
    slack.send_block_message(blocks)
    return {"resources": resources}

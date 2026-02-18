from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/hygiene", tags=["Hygiene"])

def get_hygiene_resources():
    untagged = aws.scan_untagged_instances()
    no_versioning = aws.scan_s3_buckets_without_versioning()
    stale_users = aws.scan_stale_iam_users()

    all_resources = []
    for i in untagged:
        all_resources.append({"id": i['id'], "display": f"Instance {i['id']} (Untagged)", "type": "instance"})
    for b in no_versioning:
        all_resources.append({"id": b['name'], "display": f"S3 Bucket {b['name']} (No Versioning)", "type": "s3"})
    for u in stale_users:
        all_resources.append({"id": u['username'], "display": f"IAM User {u['username']} (Stale)", "type": "iam"})
    
    return all_resources

@router.get("")
def scan_hygiene():
    resources = get_hygiene_resources()
    blocks = slack.get_remediation_blocks("hygiene", resources)
    slack.send_block_message(blocks)
    return {"resources": resources}

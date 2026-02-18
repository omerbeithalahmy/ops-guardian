from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/hygiene", tags=["Hygiene"])

@router.get("")
def scan_hygiene():
    untagged = aws.scan_untagged_instances()
    no_versioning = aws.scan_s3_buckets_without_versioning()
    stale_users = aws.scan_stale_iam_users()

    issues = []

    if untagged:
        instance_list = ", ".join(f"`{i['id']}`" for i in untagged)
        issues.append(f"*Untagged Instances*: {len(untagged)} found ({instance_list})")

    if no_versioning:
        bucket_list = ", ".join(f"`{b['name']}`" for b in no_versioning)
        issues.append(f"*S3 Without Versioning*: {len(no_versioning)} buckets ({bucket_list})")

    if stale_users:
        user_list = ", ".join(f"`{u['username']}`" for u in stale_users)
        issues.append(f"*Stale IAM Users (90+ days)*: {len(stale_users)} found ({user_list})")

    if issues:
        msg = "*OpsGuardian Hygiene Report*\n" + "\n".join(f"- {i}" for i in issues)
        slack.send_alert(msg, color="#439fe0")
    else:
        slack.send_alert("*OpsGuardian Hygiene Report*\nNo hygiene issues found.", color="#36a64f")

    return {
        "untagged_instances": untagged,
        "s3_without_versioning": no_versioning,
        "stale_iam_users": stale_users
    }

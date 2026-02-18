from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/security", tags=["Security"])

@router.get("")
def scan_security():
    open_sgs = aws.scan_open_ssh_security_groups()
    public_buckets = aws.scan_public_s3_buckets()
    no_mfa = aws.scan_iam_users_without_mfa()

    issues = []

    if open_sgs:
        sg_list = ", ".join(f"`{sg['id']}`" for sg in open_sgs)
        issues.append(f"*Open SSH (port 22)*: {len(open_sgs)} security groups ({sg_list})")

    if public_buckets:
        bucket_list = ", ".join(f"`{b['name']}`" for b in public_buckets)
        issues.append(f"*Public S3 Buckets*: {len(public_buckets)} found ({bucket_list})")

    if no_mfa:
        user_list = ", ".join(f"`{u['username']}`" for u in no_mfa)
        issues.append(f"*IAM Users Without MFA*: {len(no_mfa)} found ({user_list})")

    if issues:
        msg = "*OpsGuardian Security Report*\n" + "\n".join(f"- {i}" for i in issues)
        slack.send_alert(msg, color="#ff0000")
    else:
        slack.send_alert("*OpsGuardian Security Report*\nNo security issues found.", color="#36a64f")

    return {
        "open_ssh_security_groups": open_sgs,
        "public_s3_buckets": public_buckets,
        "iam_users_without_mfa": no_mfa
    }

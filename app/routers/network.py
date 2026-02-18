from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/network", tags=["Network"])

@router.get("")
def scan_network():
    unused_vpcs = aws.scan_unused_vpcs()
    unattached_sgs = aws.scan_unattached_security_groups()
    public_ip_subnets = aws.scan_public_ip_subnets()

    issues = []

    if unused_vpcs:
        vpc_list = ", ".join(f"`{v['id']}`" for v in unused_vpcs)
        issues.append(f"*Unused VPCs*: {len(unused_vpcs)} found ({vpc_list})")

    if unattached_sgs:
        sg_list = ", ".join(f"`{sg['id']}`" for sg in unattached_sgs)
        issues.append(f"*Unattached Security Groups*: {len(unattached_sgs)} found ({sg_list})")

    if public_ip_subnets:
        subnet_list = ", ".join(f"`{s['id']}`" for s in public_ip_subnets)
        issues.append(f"*Subnets With Auto Public IP*: {len(public_ip_subnets)} found ({subnet_list})")

    if issues:
        msg = "*OpsGuardian Network Report*\n" + "\n".join(f"- {i}" for i in issues)
        slack.send_alert(msg, color="#ff9900")
    else:
        slack.send_alert("*OpsGuardian Network Report*\nNo network issues found.", color="#36a64f")

    return {
        "unused_vpcs": unused_vpcs,
        "unattached_security_groups": unattached_sgs,
        "public_ip_subnets": public_ip_subnets
    }

from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/costs", tags=["Costs"])

@router.get("")
def scan_costs():
    volumes = aws.scan_unattached_volumes()
    eips = aws.scan_unused_elastic_ips()
    stopped = aws.scan_stopped_instances()

    issues = []

    if volumes:
        total_gb = sum(v['size_gb'] for v in volumes)
        issues.append(f"*Unattached Volumes*: {len(volumes)} found, {total_gb}GB wasted")

    if eips:
        eip_list = ", ".join(f"`{e['ip']}`" for e in eips)
        issues.append(f"*Unused Elastic IPs*: {len(eips)} found ({eip_list})")

    if stopped:
        instance_list = ", ".join(f"`{i['id']}`" for i in stopped)
        issues.append(f"*Stopped Instances*: {len(stopped)} found ({instance_list})")

    if issues:
        msg = "*OpsGuardian Cost Report*\n" + "\n".join(f"- {i}" for i in issues)
        slack.send_alert(msg, color="#ff9900")
    else:
        slack.send_alert("*OpsGuardian Cost Report*\nNo cost issues found.", color="#36a64f")

    return {
        "unattached_volumes": volumes,
        "unused_elastic_ips": eips,
        "stopped_instances": stopped
    }

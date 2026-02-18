from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/network", tags=["Network"])

def get_network_resources():
    unused_vpcs = aws.scan_unused_vpcs()
    unattached_sgs = aws.scan_unattached_security_groups()
    public_ip_subnets = aws.scan_public_ip_subnets()

    all_resources = []
    for v in unused_vpcs:
        all_resources.append({"id": v['id'], "display": f"VPC {v['id']} (Unused)", "type": "vpc"})
    for sg in unattached_sgs:
        all_resources.append({"id": sg['id'], "display": f"Security Group {sg['id']} (Unattached)", "type": "sg"})
    for s in public_ip_subnets:
        all_resources.append({"id": s['id'], "display": f"Subnet {s['id']} (Auto Public IP)", "type": "subnet"})
    
    return all_resources

@router.get("")
def scan_network():
    resources = get_network_resources()
    blocks = slack.get_remediation_blocks("network", resources)
    slack.send_block_message(blocks)
    return {"resources": resources}

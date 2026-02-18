from fastapi import APIRouter
from app.services import aws, slack

router = APIRouter(prefix="/scan/costs", tags=["Costs"])

def get_costs_resources():
    volumes = aws.scan_unattached_volumes()
    eips = aws.scan_unused_elastic_ips()
    stopped = aws.scan_stopped_instances()

    all_resources = []
    for v in volumes:
        all_resources.append({"id": v['id'], "display": f"Volume {v['id']} ({v['size_gb']}GB)", "type": "volume"})
    for e in eips:
        all_resources.append({"id": e['allocation_id'], "display": f"Elastic IP {e['ip']}", "type": "eip"})
    for i in stopped:
        all_resources.append({"id": i['id'], "display": f"Instance {i['id']} (Stopped)", "type": "instance"})
    
    return all_resources

@router.get("")
def scan_costs():
    resources = get_costs_resources()
    blocks = slack.get_remediation_blocks("costs", resources)
    slack.send_block_message(blocks)
    return {"resources": resources}

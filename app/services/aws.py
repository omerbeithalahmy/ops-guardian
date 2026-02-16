import boto3
from app.core.config import settings

def get_ec2_client():
    return boto3.client('ec2', region_name='us-east-1')

def list_available_volumes():
    client = get_ec2_client()
    response = client.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )
    return response['Volumes']

def delete_volume(volume_id: str):
    client = get_ec2_client()
    client.delete_volume(VolumeId=volume_id)

def get_security_groups():
    client = get_ec2_client()
    return client.describe_security_groups()['SecurityGroups']

def scan_security_groups():
    sgs = get_security_groups()
    bad_sgs = []

    for sg in sgs:
        for permission in sg.get('IpPermissions', []):
            from_port = permission.get('FromPort')
            to_port = permission.get('ToPort')

            if from_port is None or to_port is None:
                continue
            if from_port <= 22 <= to_port:
                for range in permission.get('IpRanges', []):
                    if range.get('CiderIp') == '0.0.0.0/0':
                        bad_sgs.append({
                            "id": sg['GroupId'],
                            "name": sg['GroupName'],
                            "reason": "Port 22 (SSH) is open to the world (0.0.0.0/0)"
                        })
                    
    return bad_sgs
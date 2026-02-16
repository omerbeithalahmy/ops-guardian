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
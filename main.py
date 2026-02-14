from fastapi import FastAPI
import boto3

app = FastAPI()

def get_ec2_client():
    return boto3.client('ec2', region_name='us-east-1')

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "OpsGuardian is up and running!"}

@app.get("/scan/volumes")
def scan_volumes():
    ec2_client = get_ec2_client()
    response = ec2_client.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )

    orphan_volumes = []
    total_wasted_gb = 0
    for volume in response['Volumes']:
        vol_data = {
            "id": volume['VolumeId'],
            "size": volume['Size'],
            "type": volume['VolumeType'],
            "created": str(volume['CreateTime'])
        }
        orphan_volumes.append(vol_data)
        total_wasted_gb += volume['Size']
    
    return {
        "count": len(orphan_volumes),
        "total_wasted_gb": total_wasted_gb,
        "volumes": orphan_volumes
    }

@app.post("/cleanup/volumes")
def cleanup_volumes(dry_run: bool = True):
    client = get_ec2_client()
    response = client.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )
    candidates = response['Volumes']
    report = {
        "deleted": [],
        "errors": [],
        "dry_run_mode": dry_run
    }

    if not candidates:
        return {"message": "No volumes to clean", "report": report}
    
    for volume in candidates:
        v_id = volume["VolumeId"]
        if dry_run:
            report['deleted'].append(f"DRY_RUN would delete {v_id}")
        else:
            try:
                client.delete_volume(VolumeId=v_id)
                report['deleted'].append(f"Successfully deleted {v_id}")
            except Exception as e:
                report['errors'].append(f"Failed to delete {v_id}: {str(e)}")
    
    return {"status": "completed", "report": report}

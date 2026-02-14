import boto3

def main():
    print("Initializing OpsGuardian Volume Inspector...")

    DRY_RUN = True

    ec2_client = boto3.client('ec2', region_name='us-east-1')
    response = ec2_client.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )

    volumes = response['Volumes']
    print(f"Found {len(volumes)} unattached volumes")
    if len(volumes) == 0:
        print("Clean! Nothing to delete.")
        return
    
    for volume in volumes:
        volume_id = volume["VolumeId"]
        size = volume["Size"]

        print(f"Target acquired: {volume_id} ({size}GB)")

        if DRY_RUN:
            print(f"DRY RUN would delete {volume_id} now. (Safe mode)")
        else:
            try:
                ec2_client.delete_volume(VolumeId=volume_id)
                print(f"Deleted {volume_id} successfully!")
            except Exception as e:
                print(f"Error deleting {volume_id}: {e}")
    
    if DRY_RUN:
        print("Finished in DRY RUN mode. No data was lost.")
        print("To verify deletion, set DRY_RUN = False in the code.")
    else:
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
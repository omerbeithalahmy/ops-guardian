import boto3

def main():
    print("Initializing OpsGuardian Volume Inspector...")

    ec2_client = boto3.client('ec2', region_name='us-east-1')
    response = ec2_client.describe_volumes()

    print("Scanning for unattached volumes...")

    orphan_count = 0
    total_size_gb = 0
    for volume in response['Volumes']:
        volume_id = volume['VolumeId']
        state = volume['State']
        size = volume['Size']
        volume_type = volume['VolumeType']
        
        if state == 'available':
            print(f"Found ORPHAN: {volume_id} | Size: {size}GB | Type: {volume_type}")
            orphan_count += 1
            total_size_gb += size
    
    if orphan_count == 0:
        print("Clean! No unattached volume found.")
    else:
        print(f"Alert: found {orphan_count} unattached volumes")
        print(f"Potential waste: {total_size_gb}GB of storage.")

if __name__ == "__main__":
    main()
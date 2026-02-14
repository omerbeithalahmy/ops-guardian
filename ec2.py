import boto3

def main():
    print("Initializing OpsGuardian...")
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    sts_client = boto3.client('sts', region_name='us-east-1')
    identitiy = sts_client.get_caller_identity()
    account_id = identitiy['Account']
    print(f"Connected to AWS account id: {account_id}")
    response = ec2_client.describe_instances()
    
    instance_count = 0
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            instance_type = instance['InstanceType']

            print(f"Found Instance: {instance_id} | Type: {instance_type} | State: {state}")

            instance_count += 1
    if instance_count == 0:
        print("No ec2 instances found in us-east-1")
    else:
        print(f"Total instances found: {instance_count}")

if __name__ == "__main__":
    main()
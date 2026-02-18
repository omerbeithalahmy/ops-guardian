import boto3
from datetime import datetime, timezone, timedelta
from app.core.config import settings


def get_ec2_client():
    return boto3.client('ec2', region_name=settings.AWS_REGION)


def get_s3_client():
    return boto3.client('s3', region_name=settings.AWS_REGION)


def get_iam_client():
    return boto3.client('iam', region_name=settings.AWS_REGION)


def scan_unattached_volumes():
    client = get_ec2_client()
    volumes = client.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )['Volumes']
    return [
        {"id": v['VolumeId'], "size_gb": v['Size'], "type": v['VolumeType']}
        for v in volumes
    ]


def scan_unused_elastic_ips():
    client = get_ec2_client()
    addresses = client.describe_addresses()['Addresses']
    return [
        {"ip": a.get('PublicIp'), "allocation_id": a.get('AllocationId')}
        for a in addresses
        if 'AssociationId' not in a
    ]


def scan_stopped_instances():
    client = get_ec2_client()
    reservations = client.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
    )['Reservations']
    instances = []
    for r in reservations:
        for i in r['Instances']:
            name = next((t['Value'] for t in i.get('Tags', []) if t['Key'] == 'Name'), 'N/A')
            instances.append({"id": i['InstanceId'], "type": i['InstanceType'], "name": name})
    return instances


def scan_open_ssh_security_groups():
    client = get_ec2_client()
    sgs = client.describe_security_groups()['SecurityGroups']
    bad_sgs = []
    for sg in sgs:
        for permission in sg.get('IpPermissions', []):
            from_port = permission.get('FromPort')
            to_port = permission.get('ToPort')
            if from_port is None or to_port is None:
                continue
            if from_port <= 22 <= to_port:
                for ip_range in permission.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        bad_sgs.append({"id": sg['GroupId'], "name": sg['GroupName']})
    return bad_sgs


def scan_public_s3_buckets():
    client = get_s3_client()
    buckets = client.list_buckets()['Buckets']
    public_buckets = []
    for bucket in buckets:
        name = bucket['Name']
        try:
            acl = client.get_bucket_acl(Bucket=name)
            for grant in acl['Grants']:
                if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                    public_buckets.append({"name": name})
                    break
        except Exception:
            pass
    return public_buckets


def scan_iam_users_without_mfa():
    client = get_iam_client()
    users = client.list_users()['Users']
    return [
        {"username": u['UserName']}
        for u in users
        if not client.list_mfa_devices(UserName=u['UserName'])['MFADevices']
    ]


def scan_untagged_instances():
    client = get_ec2_client()
    reservations = client.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}]
    )['Reservations']
    untagged = []
    for r in reservations:
        for i in r['Instances']:
            tags = i.get('Tags', [])
            has_name = any(t['Key'] == 'Name' for t in tags)
            if not has_name:
                untagged.append({"id": i['InstanceId'], "type": i['InstanceType']})
    return untagged


def scan_s3_buckets_without_versioning():
    client = get_s3_client()
    buckets = client.list_buckets()['Buckets']
    no_versioning = []
    for bucket in buckets:
        name = bucket['Name']
        try:
            versioning = client.get_bucket_versioning(Bucket=name)
            if versioning.get('Status') != 'Enabled':
                no_versioning.append({"name": name})
        except Exception:
            pass
    return no_versioning


def scan_stale_iam_users():
    client = get_iam_client()
    users = client.list_users()['Users']
    stale = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    for user in users:
        last_used = user.get('PasswordLastUsed')
        if last_used is None or last_used < cutoff:
            stale.append({"username": user['UserName']})
    return stale


def scan_unused_vpcs():
    client = get_ec2_client()
    vpcs = client.describe_vpcs(
        Filters=[{'Name': 'isDefault', 'Values': ['false']}]
    )['Vpcs']
    unused = []
    for vpc in vpcs:
        subnets = client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
        )['Subnets']
        instances = client.describe_instances(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
        )['Reservations']
        if not instances:
            name = next((t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'), 'N/A')
            unused.append({"id": vpc['VpcId'], "name": name, "subnets": len(subnets)})
    return unused


def scan_unattached_security_groups():
    client = get_ec2_client()
    all_sgs = client.describe_security_groups()['SecurityGroups']
    used_sg_ids = set()

    interfaces = client.describe_network_interfaces()['NetworkInterfaces']
    for iface in interfaces:
        for group in iface.get('Groups', []):
            used_sg_ids.add(group['GroupId'])

    return [
        {"id": sg['GroupId'], "name": sg['GroupName']}
        for sg in all_sgs
        if sg['GroupId'] not in used_sg_ids and sg['GroupName'] != 'default'
    ]


def scan_public_ip_subnets():
    client = get_ec2_client()
    subnets = client.describe_subnets()['Subnets']
    return [
        {"id": s['SubnetId'], "cidr": s['CidrBlock'], "az": s['AvailabilityZone']}
        for s in subnets
        if s.get('MapPublicIpOnLaunch')
    ]
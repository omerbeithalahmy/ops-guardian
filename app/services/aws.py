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
    volumes = client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])['Volumes']
    return [{"id": v['VolumeId'], "size_gb": v['Size'], "type": "volume"} for v in volumes]

def scan_unused_elastic_ips():
    client = get_ec2_client()
    addresses = client.describe_addresses()['Addresses']
    return [{"ip": a.get('PublicIp'), "allocation_id": a.get('AllocationId'), "type": "eip"} for a in addresses if 'AssociationId' not in a]

def scan_stopped_instances():
    client = get_ec2_client()
    reservations = client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])['Reservations']
    instances = []
    for r in reservations:
        for i in r['Instances']:
            name = next((t['Value'] for t in i.get('Tags', []) if t['Key'] == 'Name'), i['InstanceId'])
            instances.append({"id": i['InstanceId'], "name": name, "type": "instance"})
    return instances

def scan_open_ssh_security_groups():
    client = get_ec2_client()
    sgs = client.describe_security_groups()['SecurityGroups']
    bad_sgs = []
    for sg in sgs:
        for permission in sg.get('IpPermissions', []):
            f, t = permission.get('FromPort'), permission.get('ToPort')
            if f is not None and t is not None and f <= 22 <= t:
                for ip_range in permission.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        bad_sgs.append({"id": sg['GroupId'], "name": sg['GroupName'], "type": "sg"})
                        break
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
                    public_buckets.append({"name": name, "type": "s3"})
                    break
        except: pass
    return public_buckets

def scan_iam_users_without_mfa():
    client = get_iam_client()
    users = client.list_users()['Users']
    res = []
    for u in users:
        if not client.list_mfa_devices(UserName=u['UserName'])['MFADevices']:
            res.append({"username": u['UserName'], "type": "iam"})
    return res

def scan_untagged_instances():
    client = get_ec2_client()
    reservations = client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])['Reservations']
    untagged = []
    for r in reservations:
        for i in r['Instances']:
            if not any(t['Key'] == 'Name' for t in i.get('Tags', [])):
                untagged.append({"id": i['InstanceId'], "type": "instance"})
    return untagged

def scan_s3_buckets_without_versioning():
    client = get_s3_client()
    buckets = client.list_buckets()['Buckets']
    no_versioning = []
    for bucket in buckets:
        name = bucket['Name']
        try:
            if client.get_bucket_versioning(Bucket=name).get('Status') != 'Enabled':
                no_versioning.append({"name": name, "type": "s3"})
        except: pass
    return no_versioning

def scan_stale_iam_users():
    client = get_iam_client()
    users = client.list_users()['Users']
    stale = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    for u in users:
        last_used = u.get('PasswordLastUsed')
        if last_used is None or last_used < cutoff:
            stale.append({"username": u['UserName'], "type": "iam"})
    return stale

def scan_unused_vpcs():
    client = get_ec2_client()
    vpcs = client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['false']}])['Vpcs']
    unused = []
    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        subnets = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        instances = client.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Reservations']
        if not instances:
            name = next((t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'), vpc_id)
            unused.append({"id": vpc_id, "name": name, "type": "vpc"})
    return unused

def scan_unattached_security_groups():
    client = get_ec2_client()
    all_sgs = client.describe_security_groups()['SecurityGroups']
    interfaces = client.describe_network_interfaces()['NetworkInterfaces']
    used_sg_ids = {g['GroupId'] for iface in interfaces for g in iface.get('Groups', [])}
    return [{"id": sg['GroupId'], "name": sg['GroupName'], "type": "sg"} for sg in all_sgs if sg['GroupId'] not in used_sg_ids and sg['GroupName'] != 'default']

def scan_public_ip_subnets():
    client = get_ec2_client()
    subnets = client.describe_subnets()['Subnets']
    return [{"id": s['SubnetId'], "type": "subnet"} for s in subnets if s.get('MapPublicIpOnLaunch')]

def delete_volumes(volume_ids):
    client = get_ec2_client()
    success, failed = [], []
    for vid in volume_ids:
        try:
            client.delete_volume(VolumeId=vid)
            success.append(vid)
        except Exception as e:
            failed.append(f"{vid} ({e})")
    return success, failed

def release_elastic_ips(allocation_ids):
    client = get_ec2_client()
    success, failed = [], []
    for aid in allocation_ids:
        try:
            client.release_address(AllocationId=aid)
            success.append(aid)
        except Exception as e:
            failed.append(f"{aid} ({e})")
    return success, failed

def terminate_instances(instance_ids):
    client = get_ec2_client()
    success, failed = [], []
    if not instance_ids: return success, failed
    try:
        client.terminate_instances(InstanceIds=instance_ids)
        success.extend(instance_ids)
    except Exception as e:
        failed.append(f"{instance_ids} ({e})")
    return success, failed

def delete_security_groups(sg_ids):
    client = get_ec2_client()
    success, failed = [], []
    for sgid in sg_ids:
        try:
            client.delete_security_group(GroupId=sgid)
            success.append(sgid)
        except Exception as e:
            failed.append(f"{sgid} ({e})")
    return success, failed

def delete_s3_buckets(bucket_names):
    client = get_s3_client()
    success, failed = [], []
    for name in bucket_names:
        try:
            client.delete_bucket(Bucket=name)
            success.append(name)
        except Exception as e:
            failed.append(f"{name} ({e})")
    return success, failed

def delete_iam_users(usernames):
    client = get_iam_client()
    success, failed = [], []
    for user in usernames:
        try:
            client.delete_user(UserName=user)
            success.append(user)
        except Exception as e:
            failed.append(f"{user} ({e})")
    return success, failed

def delete_vpcs(vpc_ids):
    client = get_ec2_client()
    success, failed = [], []
    for vpcid in vpc_ids:
        try:
            client.delete_vpc(VpcId=vpcid)
            success.append(vpcid)
        except Exception as e:
            failed.append(f"{vpcid} ({e})")
    return success, failed
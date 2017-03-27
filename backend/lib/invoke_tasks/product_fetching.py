import invoke
from invoke import task

from pony.orm import *
import lib.models

from lib.product_fetchers.steam_product_fetcher import SteamProductFetcher

from lib.config import config

import boto3
import uuid
import time

import subprocess
import shlex


@task
def start_product_fetching(ctx):
    aws_session = boto3.Session(profile_name="serpent")

    #create_database(aws_session)
    #create_rq_broker(aws_session)
    create_rq_workers(aws_session, quantity=10)

    # Steam Products
    spf = SteamProductFetcher()
    spf.discover_all(product_type="Games")


def create_database(aws_session):
    rds_client = aws_session.client("rds", region_name="ca-central-1")
    route53_client = aws_session.client("route53")

    database_identifier = "serpentpm"

    rds_client.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier="serpentpm",
        DBSnapshotIdentifier="serpentpm-latest",
        DBInstanceClass="db.m4.xlarge",
        Port=5432,
        AvailabilityZone="ca-central-1a",
        DBSubnetGroupName="default-vpc-455a872c",
        MultiAZ=False,
        PubliclyAccessible=True,
        AutoMinorVersionUpgrade=True,
        LicenseModel="postgresql-license",
        Engine="postgres",
        Tags=[
            {
                "Key": "Name",
                "Value": "Playthrough Manager DB"
            },
        ],
        StorageType="gp2",
        CopyTagsToSnapshot=True
    )

    database_public_dns = None

    while database_public_dns is None:
        database_instances = rds_client.describe_db_instances()

        for database_instance in database_instances["DBInstances"]:
            if database_instance.get("DBInstanceIdentifier") == database_identifier:
                if database_instance.get("Endpoint") is not None:
                    database_public_dns = database_instance["Endpoint"].get("Address")
                    break

        time.sleep(5)

    route53_client.change_resource_record_sets(
        HostedZoneId=config["aws"]["route53"]["hosted_zone_id"],
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "db.playthroughmanager.com.",
                        "Type": "CNAME",
                        "TTL": 300,
                        "ResourceRecords": [
                            {
                                "Value": database_public_dns
                            }
                        ]
                    }
                }
            ]
        }
    )


def create_rq_broker(aws_session):
    ec2_resource = aws_session.resource("ec2", region_name="ca-central-1")
    route53_client = aws_session.client("route53")

    response = ec2_resource.meta.client.run_instances(
        ImageId="ami-7b74c91f",
        MinCount=1,
        MaxCount=1,
        KeyName="serpent",
        InstanceType="t2.medium",
        Placement={
            "AvailabilityZone": "ca-central-1a",
            "Tenancy": "default",
        },
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 16,
                    "DeleteOnTermination": True,
                    "VolumeType": "gp2"
                }
            }
        ],
        Monitoring={
            "Enabled": False
        },
        DisableApiTermination=False,
        InstanceInitiatedShutdownBehavior="terminate",
        ClientToken=str(uuid.uuid4()),
        NetworkInterfaces=[
            {
                "DeviceIndex": 0,
                "SubnetId": "subnet-8af229e3",
                "AssociatePublicIpAddress": True
            }
        ]
    )

    instance_id = response["Instances"][0]["InstanceId"]

    ec2_resource.meta.client.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=[
            "sg-4014a729"
        ]
    )

    instance = ec2_resource.Instance(instance_id)

    route53_client.change_resource_record_sets(
        HostedZoneId=config["aws"]["route53"]["hosted_zone_id"],
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "rq.playthroughmanager.com.",
                        "Type": "CNAME",
                        "TTL": 300,
                        "ResourceRecords": [
                            {
                                "Value": instance.public_dns_name
                            }
                        ]
                    }
                }
            ]
        }
    )

    while ec2_resource.Instance(instance_id).state.get("Code") != 16:
        time.sleep(5)

    time.sleep(30)

    subprocess.call(shlex.split(f"fab setup_rq_broker -H {instance.public_dns_name}"))


def create_rq_workers(aws_session, quantity=1):
    ec2_resource = aws_session.resource("ec2", region_name="ca-central-1")

    response = ec2_resource.meta.client.run_instances(
        ImageId="ami-7b74c91f",
        MinCount=quantity,
        MaxCount=quantity,
        KeyName="serpent",
        InstanceType="t2.xlarge",
        Placement={
            "AvailabilityZone": "ca-central-1a",
            "Tenancy": "default",
        },
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 16,
                    "DeleteOnTermination": True,
                    "VolumeType": "gp2"
                }
            }
        ],
        Monitoring={
            "Enabled": False
        },
        DisableApiTermination=False,
        InstanceInitiatedShutdownBehavior="terminate",
        ClientToken=str(uuid.uuid4()),
        NetworkInterfaces=[
            {
                "DeviceIndex": 0,
                "SubnetId": "subnet-8af229e3",
                "AssociatePublicIpAddress": True
            }
        ]
    )

    instances = response["Instances"]
    instance_ids = list(map(lambda i: i.get("InstanceId"), instances))

    for instance_id in instance_ids:
        ec2_resource.meta.client.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[
                "sg-67f0420e"
            ]
        )

    while ec2_resource.Instance(instance_ids[0]).state.get("Code") != 16:
        time.sleep(5)

    time.sleep(30)

    instance_public_dns_names = list(map(lambda i: ec2_resource.Instance(i).public_dns_name, instance_ids))

    subprocess.call(shlex.split(f"fab setup_rq_worker -H {','.join(instance_public_dns_names)}"))

namespace = invoke.Collection("product_fetching")

namespace.add_task(start_product_fetching)

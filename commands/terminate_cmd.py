"""terminate — terminate or delete one resource, with safety confirmation.

WHAT YOU MUST BUILD
-------------------
4 dispatch functions, one per resource type, that:
  - Ask `confirm(...)` before doing the destructive call (unless --force)
  - Perform the right boto3 API call
  - Handle ClientError gracefully (no stack trace dump)

Safety contract — DO NOT break this:
  - `terminate` MUST ask y/N confirmation by default
  - `--force` bypasses confirm (for CI / scripted use)
  - S3 MUST refuse to delete buckets that still contain objects
  - Any AWS error MUST print a friendly message, not a Python traceback

HELPERS YOU CAN USE
-------------------
From commands._common:
  confirm(prompt, force=False) -> bool
    # If force=True, returns True. Otherwise asks "<prompt> [y/N] " on stdin.

AWS APIS YOU'LL NEED
--------------------
- EC2: ec2.terminate_instances(InstanceIds=[id])
- RDS: rds.stop_db_instance(DBInstanceIdentifier=id)  # full delete needs final snapshot
- S3:  s3.list_objects_v2(Bucket=name).get("KeyCount", 0)  # check empty first
       s3.delete_bucket(Bucket=name)
- EBS: ec2.delete_volume(VolumeId=id)

ERROR HANDLING
--------------
Wrap the dispatch call in `try: ... except ClientError as e: print(...)`. Extract
e.response["Error"]["Code"] and e.response["Error"]["Message"] for the message.

EXPECTED OUTPUT
---------------
On success:
    Terminated EC2 i-0abc123

On user abort:
    Aborted.

On refuse (S3 non-empty):
    Refusing — bucket my-bucket has 12 object(s). Empty it first.

On AWS error:
    AWS error [InvalidInstanceID.NotFound]: The instance ID 'i-xxx' does not exist

VERIFY
------
    pytest tests/test_terminate.py -v
"""
import boto3
from botocore.exceptions import ClientError

from commands._common import confirm


def _terminate_ec2(rid, force):
    """Terminate one EC2 instance after confirmation."""
    if not confirm(f"Terminate EC2 {rid}?", force=force):
        print("Aborted.")
        return
    
    ec2 = boto3.client("ec2")
    try:
        ec2.terminate_instances(InstanceIds=[rid])
        print(f"Terminated EC2 {rid}")
    except ClientError as e:
        print(f"AWS error [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")


def _terminate_rds(rid, force):
    """Stop one RDS instance after confirmation.

    Full delete (delete_db_instance) requires a final snapshot decision —
    out of scope for this challenge. Stop is enough to stop billing.
    """
    if not confirm(f"Stop RDS {rid}?", force=force):
        print("Aborted.")
        return
    
    rds = boto3.client("rds")
    try:
        rds.stop_db_instance(DBInstanceIdentifier=rid)
        print(f"Stopped RDS {rid}")
    except ClientError as e:
        print(f"AWS error [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")


def _terminate_s3(rid, force):
    """Delete one S3 bucket — refuse if it has any objects."""
    s3 = boto3.client("s3")
    
    # Check if bucket has objects
    try:
        key_count = s3.list_objects_v2(Bucket=rid).get("KeyCount", 0)
    except ClientError as e:
        print(f"AWS error [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")
        return
    
    if key_count > 0:
        print(f"Refusing — bucket {rid} has {key_count} object(s). Empty it first.")
        return
    
    if not confirm(f"Delete S3 {rid}?", force=force):
        print("Aborted.")
        return
    
    try:
        s3.delete_bucket(Bucket=rid)
        print(f"Deleted S3 {rid}")
    except ClientError as e:
        print(f"AWS error [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")


def _terminate_volume(rid, force):
    """Delete one EBS volume after confirmation."""
    if not confirm(f"Delete volume {rid}?", force=force):
        print("Aborted.")
        return
    
    ec2 = boto3.client("ec2")
    try:
        ec2.delete_volume(VolumeId=rid)
        print(f"Deleted volume {rid}")
    except ClientError as e:
        print(f"AWS error [{e.response['Error']['Code']}]: {e.response['Error']['Message']}")


DISPATCH = {
    "ec2": _terminate_ec2,
    "rds": _terminate_rds,
    "s3": _terminate_s3,
    "volume": _terminate_volume,
}


def run(args):
    """Entry point.

    Args set by argparse:
        args.type   — one of "ec2", "rds", "s3", "volume"
        args.id     — resource identifier
        args.force  — bool, skip confirm if True
    """
    func = DISPATCH[args.type]
    func(args.id, args.force)

"""clean — (stretch) bulk terminate resources matching a tag.

WARNING — DESIGN-FOR-SAFETY
---------------------------
This is the most dangerous command in the CLI. Get the contract right:

  1. DEFAULT IS DRY-RUN. Without --apply the command MUST NOT touch resources.
     It only lists what WOULD be deleted.
  2. Even with --apply, you should consider printing a summary count first
     ("about to terminate N EC2 + M volumes — proceed?"), though for this
     starter a hard `--apply` flag is enough.
  3. Never use this with a tag you don't fully own. Reflection prompt in
     README covers the blast-radius scenario.

WHAT YOU MUST BUILD
-------------------
1. `_find_targets(tag_key, tag_val)` — return a dict like:
     {"ec2": [<instance ids in non-terminal state>],
      "volume": [<volume ids in 'available' state only>]}
   Skip terminated/shutting-down instances (already gone).
   Skip in-use volumes (can't delete while attached — would error anyway).

2. `run(args)` — call _find_targets, print the plan, then either:
     - bail with "(dry-run — pass --apply to ...)"  (default)
     - or actually terminate (when --apply)

HELPERS YOU CAN USE
-------------------
From commands._common:
  parse_kv(s) -> (k, v)

AWS APIS YOU'LL NEED
--------------------
- ec2.describe_instances() + describe_volumes() — same as list_cmd
- ec2.terminate_instances(InstanceIds=[...])
- ec2.delete_volume(VolumeId=...)  (per volume, no bulk API)

VERIFY
------
    pytest tests/test_clean.py -v
"""
import boto3

from commands._common import parse_kv


def _find_targets(tag_key, tag_val):
    """Return {"ec2": [...], "volume": [...]} matching tag in non-terminal state."""
    ec2 = boto3.client("ec2")
    
    targets = {"ec2": [], "volume": []}
    
    # Find EC2 instances
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                state = instance["State"]["Name"]
                # Skip terminated/shutting-down instances
                if state in ("terminated", "shutting-down"):
                    continue
                
                # Check tags
                tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                if tags.get(tag_key) == tag_val:
                    targets["ec2"].append(instance["InstanceId"])
    
    # Find volumes
    paginator = ec2.get_paginator("describe_volumes")
    for page in paginator.paginate():
        for volume in page["Volumes"]:
            # Only available volumes (not in-use)
            if volume["State"] != "available":
                continue
            
            # Check tags
            tags = {t["Key"]: t["Value"] for t in volume.get("Tags", [])}
            if tags.get(tag_key) == tag_val:
                targets["volume"].append(volume["VolumeId"])
    
    return targets


def run(args):
    """Entry point.

    Args set by argparse:
        args.tag    — "key=value" string (REQUIRED)
        args.apply  — bool, must be True to actually delete (default False = dry-run)
    """
    tag_key, tag_val = parse_kv(args.tag)
    targets = _find_targets(tag_key, tag_val)
    
    # Print plan
    ec2_count = len(targets["ec2"])
    vol_count = len(targets["volume"])
    
    if ec2_count == 0 and vol_count == 0:
        print(f"Nothing to clean — no resources with {tag_key}={tag_val}")
        return
    
    print(f"Will terminate {ec2_count} EC2 + {vol_count} volumes with {tag_key}={tag_val}:")
    
    for iid in targets["ec2"]:
        print(f"  - EC2 {iid}")
    
    for vid in targets["volume"]:
        print(f"  - Volume {vid}")
    
    # Dry-run or apply
    if not args.apply:
        print("\n(dry-run — pass --apply to actually delete)")
        return
    
    # Apply: terminate
    if targets["ec2"]:
        ec2 = boto3.client("ec2")
        ec2.terminate_instances(InstanceIds=targets["ec2"])
        print(f"\nTerminated {ec2_count} EC2 instance(s)")
    
    if targets["volume"]:
        ec2 = boto3.client("ec2")
        for vid in targets["volume"]:
            ec2.delete_volume(VolumeId=vid)
        print(f"Deleted {vol_count} volume(s)")

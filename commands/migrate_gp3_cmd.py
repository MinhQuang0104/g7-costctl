"""migrate-gp3 — (stretch) plan or apply gp2 → gp3 EBS migration.

WHY THIS MATTERS
----------------
gp3 is cheaper than gp2 ($0.08 vs $0.10 per GB-month) AND faster
(3000 IOPS baseline vs 3 IOPS/GB scaling). Most gp2 volumes should migrate.
EBS supports live modification — no downtime, no detach.

WHAT YOU MUST BUILD
-------------------
1. Dry-run mode (default):
   - List all gp2 volumes in the account
   - Show size, attached instance, and projected monthly savings per volume
   - Print total savings if all migrated

2. Apply mode (--apply):
   - With --volume-id: migrate just that one
   - Without --volume-id: migrate ALL gp2 volumes
   - Use ec2.modify_volume(...) — the modification runs in the background

AWS APIS YOU'LL NEED
--------------------
ec2.describe_volumes(Filters=[{"Name": "volume-type", "Values": ["gp2"]}])
ec2.modify_volume(
    VolumeId=vid,
    VolumeType="gp3",
    Iops=3000,        # baseline included free
    Throughput=125,   # baseline included free
)

After calling modify_volume, the volume goes through state transitions:
    in-use → modifying → optimizing → in-use (now gp3)
The app stays online throughout. Optimization takes ~30 min for a 100GB
volume; longer for larger volumes.

EXPECTED OUTPUT FORMAT (dry-run)
--------------------------------
    gp2 volumes (price delta $0.020/GB-month):
    ------------------------------------------------------------------------------
      vol-0abc123def456789a    100GB  attached=i-0aaa            $2.00/mo savings
      vol-0bbb456ef789012345     50GB  attached=(none)            $1.00/mo savings
    ------------------------------------------------------------------------------

    (dry-run — pass --apply --volume-id <id> to migrate one, or --apply to migrate ALL)

EXPECTED OUTPUT FORMAT (apply)
------------------------------
      → modify_volume issued for vol-0abc123def456789a (gp3, 3000 IOPS, 125 MiB/s)

    Volume(s) entering 'modifying' → 'optimizing' state. App stays online.
    Use `costctl list volume` after ~30 minutes to confirm 'in-use' + gp3.

VERIFY MANUALLY (no test file for this command)
-----------------------------------------------
    ./costctl.py migrate-gp3                           # dry-run, no side effects
    ./costctl.py migrate-gp3 --apply --volume-id vol-xxx  # migrate ONE

Pick a small volume first. Confirm via:
    ./costctl.py list volume --tag <something>
or AWS Console → EC2 → Volumes.

PRICING NOTE
------------
Constants below assume us-east-1 on-demand pricing. If your account is in
a different region, the dollar figure displayed is rough — but the migration
itself works the same anywhere.
"""
import boto3

# us-east-1 on-demand pricing per GB-month. Override if you care about exact $.
GP2_PRICE = 0.10
GP3_PRICE = 0.08


def run(args):
    """Entry point.

    Args set by argparse:
        args.apply       — bool, default False (dry-run)
        args.volume_id   — optional str, only migrate this volume when --apply
    """
    ec2 = boto3.client("ec2")
    
    # Get all gp2 volumes
    response = ec2.describe_volumes(
        Filters=[{"Name": "volume-type", "Values": ["gp2"]}]
    )
    
    volumes = response.get("Volumes", [])
    
    if not volumes:
        print("No gp2 volumes found.")
        return
    
    # Calculate savings per volume
    price_diff = GP2_PRICE - GP3_PRICE  # $0.02/GB-month
    
    print(f"gp2 volumes (price delta ${price_diff:.3f}/GB-month):")
    print("-" * 80)
    
    total_savings = 0
    volumes_to_migrate = []
    
    for volume in volumes:
        vid = volume["VolumeId"]
        size = volume["Size"]
        state = volume["State"]
        
        # Skip if not in-use or available
        if state not in ("in-use", "available"):
            continue
        
        # Check if already migrating
        if any(m["VolumeModification"]["State"] in ("modifying", "optimizing") 
               for m in volume.get("VolumeModifications", [])):
            continue
        
        # Get attached instance (if any)
        attachments = volume.get("Attachments", [])
        if attachments:
            instance_id = attachments[0]["InstanceId"]
        else:
            instance_id = "(none)"
        
        # Calculate monthly savings
        monthly_savings = size * price_diff
        total_savings += monthly_savings
        
        # Check if this volume should be migrated
        should_migrate = args.apply and (args.volume_id is None or vid == args.volume_id)
        
        print(f"  {vid:<25} {size:>4}GB  attached={instance_id:<20} ${monthly_savings:>7.2f}/mo savings")
        
        if should_migrate:
            volumes_to_migrate.append(vid)
    
    print("-" * 80)
    
    if not args.apply:
        print(f"\n(dry-run — pass --apply --volume-id <id> to migrate one, or --apply to migrate ALL)")
        print(f"Total potential savings: ${total_savings:.2f}/month")
        return
    
    # Apply mode: migrate volumes
    if args.volume_id:
        volumes_to_migrate = [args.volume_id]
    
    if not volumes_to_migrate:
        print("No volumes to migrate.")
        return
    
    for vid in volumes_to_migrate:
        try:
            ec2.modify_volume(
                VolumeId=vid,
                VolumeType="gp3",
                Iops=3000,
                Throughput=125,
            )
            print(f"\n  → modify_volume issued for {vid} (gp3, 3000 IOPS, 125 MiB/s)")
        except Exception as e:
            print(f"  ✗ Error modifying {vid}: {e}")
    
    print("\nVolume(s) entering 'modifying' → 'optimizing' state. App stays online.")
    print("Use `costctl list volume` after ~30 minutes to confirm 'in-use' + gp3.")

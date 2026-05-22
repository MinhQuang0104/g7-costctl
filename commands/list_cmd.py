"""list — list AWS resources by type, filter by tag / missing-tag.

WHAT YOU MUST BUILD
-------------------
Support 4 resource types: ec2, rds, s3, volume.
Each takes:
- `want` — list of (key, value) tag pairs the resource MUST have
- `missing` — list of tag keys the resource MUST NOT have

Print a formatted table to stdout. Test cases are in tests/test_list.py.

HELPERS YOU CAN USE
-------------------
From commands._common:
  parse_kv(s) -> (k, v)            # "Owner=alice" -> ("Owner", "alice")
  tags_to_dict(items) -> dict       # boto3 [{"Key","Value"}] -> {k: v}
  tags_match(tags, want, missing) -> bool

AWS APIS YOU'LL NEED
--------------------
- EC2: ec2.describe_instances() with get_paginator
- RDS: rds.describe_db_instances(), then list_tags_for_resource(ResourceName=arn)
- S3:  s3.list_buckets(), then get_bucket_tagging(Bucket=name)
       (catch ClientError when bucket has no tagging config — treat as {})
- EBS: ec2.describe_volumes() with get_paginator

EXPECTED OUTPUT FORMAT (when run from CLI)
------------------------------------------
    EC2 Environment=dev — 1 found:
    ------------------------------------------------------------------------------
      i-0abc123def456789a       t3.micro       running       Environment=dev

VERIFY
------
    pytest tests/test_list.py -v
"""
import boto3

from commands._common import parse_kv, tags_to_dict, tags_match


def _list_ec2(want, missing):
    ec2 = boto3.client("ec2")

    rows = []
    # Dùng paginator để lấy ALL instances (không chỉ 100 cái đầu)
    paginator = ec2.get_paginator("describe_instances")
    
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                tags = tags_to_dict(instance.get("Tags", []))
                
                if not tags_match(tags, want, missing):
                    continue
                
                row = (
                    instance["InstanceId"],
                    instance["InstanceType"],
                    instance["State"]["Name"],
                    tags
                )
                rows.append(row)
    
    return rows


def _list_rds(want, missing):
    rds = boto3.client("rds")
    
    rows = []
    
    # RDS không có paginator, list trực tiếp
    response = rds.describe_db_instances()
    
    for db in response["DBInstances"]:
        # Lấy tags từ ARN
        tags_response = rds.list_tags_for_resource(
            ResourceName=db["DBInstanceArn"]
        )
        tags = tags_to_dict(tags_response["TagList"])
        
        if not tags_match(tags, want, missing):
            continue
        
        row = (
            db["DBInstanceIdentifier"],
            db["DBInstanceClass"],
            db["DBInstanceStatus"],
            tags
        )
        rows.append(row)
    
    return rows

def _list_s3(want, missing):
    s3 = boto3.client("s3")
    
    rows = []
    buckets = s3.list_buckets()["Buckets"]
    
    for bucket in buckets:
        bucket_name = bucket["Name"]
        
        # Lấy tags, nếu không có config thì treat as empty
        try:
            tag_set = s3.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
            tags = tags_to_dict(tag_set)
        except s3.exceptions.ClientError:
            # Bucket không có tagging config → empty tags
            tags = {}
        
        if not tags_match(tags, want, missing):
            continue
        
        row = (
            bucket_name,
            "bucket",
            "active",
            tags
        )
        rows.append(row)
    
    return rows


def _list_volume(want, missing):
    ec2 = boto3.client("ec2")
    
    rows = []
    paginator = ec2.get_paginator("describe_volumes")
    
    for page in paginator.paginate():
        for volume in page["Volumes"]:
            tags = tags_to_dict(volume.get("Tags", []))
            
            if not tags_match(tags, want, missing):
                continue
            
            # Format: "gp2-100GB"
            type_size = f"{volume['VolumeType']}-{volume['Size']}GB"
            
            row = (
                volume["VolumeId"],
                type_size,
                volume["State"],
                tags
            )
            rows.append(row)
    
    return rows

DISPATCH = {
    "ec2": _list_ec2,
    "rds": _list_rds,
    "s3": _list_s3,
    "volume": _list_volume,
}


def run(args):
    # Parse các tag arguments thành want pairs
    want = [parse_kv(tag_str) for tag_str in (args.tag or [])]
    missing = args.missing_tag or []
    
    # Gọi hàm phù hợp
    func = DISPATCH[args.type]
    rows = func(want, missing)
    
    # In header
    print(f"{args.type.upper()} {', '.join(f'{k}={v}' for k,v in want)} — {len(rows)} found:")
    print("-" * 80)
    
    # In từng row
    for row in rows:
        resource_id, detail1, detail2, tags = row
        tags_str = " ".join(f"{k}={v}" for k, v in tags.items())
        print(f"  {resource_id:<30} {detail1:<20} {detail2:<15} {tags_str}")
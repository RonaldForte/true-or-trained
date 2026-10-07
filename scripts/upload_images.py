"""Upload the built image set to Cloudflare R2 (S3-compatible API).

Credentials come from environment variables, never from arguments or files in the repo:

    R2_ENDPOINT            https://<account-id>.r2.cloudflarestorage.com
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY

Only images/*.webp are uploaded. The manifest is NOT uploaded: it says which image in each
pair is real, and the bucket is public.

Safe to re-run: images already in the bucket are skipped (ids are random, so a given name
always refers to the same image).
"""

import argparse
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Filenames are random and never reused, so browsers and Cloudflare can cache them forever.
CACHE_CONTROL = "public, max-age=31536000, immutable"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images-dir", type=Path, required=True, help="data/build/images")
    parser.add_argument("--bucket", default="true-or-trained-images")
    args = parser.parse_args()

    missing = [name for name in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if not os.environ.get(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

    existing = set()
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=args.bucket):
        existing.update(obj["Key"] for obj in page.get("Contents", []))

    files = sorted(args.images_dir.glob("*.webp"))
    uploaded = 0
    for path in files:
        if path.name in existing:
            continue
        try:
            s3.upload_file(
                str(path),
                args.bucket,
                path.name,
                ExtraArgs={"ContentType": "image/webp", "CacheControl": CACHE_CONTROL},
            )
        except ClientError as exc:
            sys.exit(f"Upload failed for {path.name}: {exc}")
        uploaded += 1
        print(f"  {uploaded} uploaded ({path.name})")

    print(f"Done: {uploaded} uploaded, {len(files) - uploaded} already present, {len(files)} total")


if __name__ == "__main__":
    main()

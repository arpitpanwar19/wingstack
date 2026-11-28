import os
import re
import json
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "wingstack-data")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "wingstack-resumes")


def _has_aws_creds() -> bool:
    return bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))


def _get_clients():
    if not _has_aws_creds():
        return None, None
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=AWS_REGION,
    )
    return session.resource("dynamodb"), session.client("s3")


def _ensure_dynamodb_table(dynamodb):
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        table.load()
        return table
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        table = dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        return table


def _ensure_s3_bucket(s3_client):
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
    except ClientError:
        params = {"Bucket": S3_BUCKET_NAME}
        if AWS_REGION != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": AWS_REGION}
        s3_client.create_bucket(**params)


def _to_dynamo_safe(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    if isinstance(obj, dict):
        return {k: _to_dynamo_safe(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_to_dynamo_safe(v) for v in obj]
    return obj


def _from_dynamo_safe(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _from_dynamo_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_dynamo_safe(v) for v in obj]
    return obj


def generate_resume_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    if not s3_key:
        return ""
    _, s3_client = _get_clients()
    if not s3_client:
        return ""
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expires_in,
        )
    except Exception:
        return ""


def upload_resume_to_s3(user_id: int | str, filename: str, pdf_bytes: bytes) -> dict:
    if not pdf_bytes:
        return {"s3_key": "", "resume_url": "", "aws_s3_stored": False}
    _, s3_client = _get_clients()
    if not s3_client:
        return {"s3_key": "", "resume_url": "", "aws_s3_stored": False}

    try:
        _ensure_s3_bucket(s3_client)
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "resume.pdf")
        s3_key = f"resumes/{user_id}/{safe_name}"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        return {
            "s3_key": s3_key,
            "resume_url": generate_resume_presigned_url(s3_key),
            "aws_s3_stored": True,
        }
    except Exception as exc:
        return {"s3_key": "", "resume_url": "", "aws_s3_stored": False, "s3_error": str(exc)}


def save_profile_to_dynamodb(profile_record: dict) -> dict:
    dynamodb, _ = _get_clients()
    if not dynamodb:
        return {"aws_dynamo_stored": False}

    try:
        table = _ensure_dynamodb_table(dynamodb)
        item = _to_dynamo_safe({
            **profile_record,
            "user_id": str(profile_record["user_id"]),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        table.put_item(Item=item)
        return {"aws_dynamo_stored": True, "table": DYNAMODB_TABLE_NAME, "region": AWS_REGION}
    except Exception as exc:
        return {"aws_dynamo_stored": False, "dynamo_error": str(exc)}


def get_profile_from_dynamodb(user_id: int | str) -> dict | None:
    dynamodb, _ = _get_clients()
    if not dynamodb:
        return None
    try:
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        resp = table.get_item(Key={"user_id": str(user_id)})
        item = resp.get("Item")
        if not item:
            return None
        clean = _from_dynamo_safe(item)
        if clean.get("resume_s3_key"):
            clean["resume_url"] = generate_resume_presigned_url(clean["resume_s3_key"])
        return clean
    except Exception:
        return None

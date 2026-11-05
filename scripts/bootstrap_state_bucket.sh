#!/usr/bin/env bash
set -euo pipefail

BUCKET="cms-terraform-state-store"
REGION="ap-southeast-1"
export AWS_PROFILE="${AWS_PROFILE:-3tier}"
export AWS_REGION="$REGION"
# Keep read-back output non-interactive, including on the Owner's local shell.
export AWS_PAGER=""

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if HEAD_RESULT=$(aws s3api head-bucket --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" 2>&1); then
  printf 'Bucket %s already exists in account %s; re-applying its settings.\n' "$BUCKET" "$ACCOUNT_ID"
elif [[ "$HEAD_RESULT" == *"(404)"* ]]; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION" \
    --object-ownership BucketOwnerEnforced >/dev/null
  aws s3api wait bucket-exists --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID"
else
  printf '%s\n' "$HEAD_RESULT" >&2
  exit 1
fi

aws s3api put-public-access-block --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-ownership-controls --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
aws s3api put-bucket-encryption --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-versioning --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-policy --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"DenyInsecureTransport\",\"Effect\":\"Deny\",\"Principal\":\"*\",\"Action\":\"s3:*\",\"Resource\":[\"arn:aws:s3:::$BUCKET\",\"arn:aws:s3:::$BUCKET/*\"],\"Condition\":{\"Bool\":{\"aws:SecureTransport\":\"false\"}}}]}"
aws s3api put-bucket-tagging --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --tagging 'TagSet=[{Key=Project,Value=cms},{Key=ManagedBy,Value=bootstrap-script}]'

aws s3api get-bucket-versioning --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --query Status --output text
aws s3api get-bucket-encryption --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text
aws s3api get-public-access-block --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID" \
  --query PublicAccessBlockConfiguration --output json
printf 'State bucket %s is ready (versioning Enabled).\n' "$BUCKET"

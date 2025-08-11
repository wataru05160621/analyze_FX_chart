#!/bin/bash
# Apply S3 lifecycle configuration for analyze-fx bucket

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
S3_BUCKET="analyze-fx-455931011903-apne1"
AWS_REGION="ap-northeast-1"
LIFECYCLE_FILE="s3/lifecycle.json"

echo -e "${GREEN}=== S3 Lifecycle Configuration ===${NC}"
echo "Bucket: $S3_BUCKET"
echo "Region: $AWS_REGION"
echo ""

# Check if lifecycle configuration file exists
if [ ! -f "$LIFECYCLE_FILE" ]; then
    echo -e "${RED}Error: Lifecycle configuration file not found: $LIFECYCLE_FILE${NC}"
    exit 1
fi

# Step 1: Backup existing lifecycle configuration (if any)
echo -e "${YELLOW}Step 1: Backing up existing lifecycle configuration...${NC}"

BACKUP_FILE="s3/lifecycle-backup-$(date +%Y%m%d-%H%M%S).json"
if aws s3api get-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET" \
    --region "$AWS_REGION" > "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ Existing configuration backed up to: $BACKUP_FILE${NC}"
else
    echo "No existing lifecycle configuration found (this is normal for new buckets)"
    rm -f "$BACKUP_FILE"
fi

# Step 2: Apply new lifecycle configuration
echo -e "${YELLOW}Step 2: Applying new lifecycle configuration...${NC}"

aws s3api put-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET" \
    --lifecycle-configuration file://"$LIFECYCLE_FILE" \
    --region "$AWS_REGION"

echo -e "${GREEN}✓ Lifecycle configuration applied successfully${NC}"

# Step 3: Verify configuration
echo -e "${YELLOW}Step 3: Verifying configuration...${NC}"

echo ""
echo "Current lifecycle rules:"
aws s3api get-bucket-lifecycle-configuration \
    --bucket "$S3_BUCKET" \
    --region "$AWS_REGION" \
    --query 'Rules[].{ID:ID,Status:Status,Prefix:Filter.Prefix,Glacier:Transitions[0].Days,Expire:Expiration.Days}' \
    --output table

echo ""
echo -e "${GREEN}=== S3 Lifecycle Configuration Complete ===${NC}"
echo ""
echo "Applied rules:"
echo "  • charts/: Move to Glacier after 30 days, delete after 90 days"
echo "  • results/: Delete after 180 days"
echo "  • stats/: Delete after 365 days"
#!/usr/bin/env python
"""AWS environment setup script for FX Analysis system."""

import json
import sys
import time
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

# Configuration
AWS_REGION = "ap-northeast-1"
ACCOUNT_ID = "455931011903"

# Resource names
ECR_REPOSITORY = "analyze-fx"
ECS_CLUSTER = "analyze-fx-cluster"
ECS_TASK_FAMILY = "analyze-fx"
TASK_ROLE_NAME = "analyze-fx-task-role"
EXECUTION_ROLE_NAME = "analyze-fx-execution-role"
SCHEDULER_ROLE_NAME = "analyze-fx-scheduler-role"
LOG_GROUP = "/ecs/analyze-fx"
S3_BUCKET = f"analyze-fx-{ACCOUNT_ID}-apne1"

# Network configuration
SUBNETS = ["subnet-06fba36a849bb6647", "subnet-02aef8bf85b9ceb0d"]
SECURITY_GROUP = "sg-03cb601e40f6e32ac"

class AWSSetup:
    """AWS environment setup."""
    
    def __init__(self, region: str = AWS_REGION, dry_run: bool = False):
        """Initialize AWS clients."""
        self.region = region
        self.account_id = ACCOUNT_ID
        self.dry_run = dry_run
        
        if dry_run:
            print("🔸 DRY RUN MODE - No resources will be created")
        
        # Initialize clients
        self.ecr = boto3.client('ecr', region_name=region)
        self.ecs = boto3.client('ecs', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.scheduler = boto3.client('scheduler', region_name=region)
        self.secrets = boto3.client('secretsmanager', region_name=region)
    
    def create_ecr_repository(self) -> bool:
        """Create ECR repository."""
        print(f"\n📦 Creating ECR repository: {ECR_REPOSITORY}")
        
        if self.dry_run:
            print("  [DRY RUN] Would create ECR repository")
            return True
        
        try:
            # Check if repository exists
            self.ecr.describe_repositories(repositoryNames=[ECR_REPOSITORY])
            print(f"  ✓ Repository already exists")
            return True
        except self.ecr.exceptions.RepositoryNotFoundException:
            # Create repository
            try:
                response = self.ecr.create_repository(
                    repositoryName=ECR_REPOSITORY,
                    imageScanningConfiguration={'scanOnPush': True},
                    imageTagMutability='MUTABLE',
                    encryptionConfiguration={
                        'encryptionType': 'AES256'
                    }
                )
                print(f"  ✅ Created ECR repository: {response['repository']['repositoryUri']}")
                
                # Set lifecycle policy
                lifecycle_policy = {
                    "rules": [
                        {
                            "rulePriority": 1,
                            "description": "Keep last 10 images",
                            "selection": {
                                "tagStatus": "any",
                                "countType": "imageCountMoreThan",
                                "countNumber": 10
                            },
                            "action": {
                                "type": "expire"
                            }
                        }
                    ]
                }
                
                self.ecr.put_lifecycle_policy(
                    repositoryName=ECR_REPOSITORY,
                    lifecyclePolicyText=json.dumps(lifecycle_policy)
                )
                print(f"  ✓ Set lifecycle policy (keep last 10 images)")
                
                return True
            except Exception as e:
                print(f"  ❌ Failed to create repository: {e}")
                return False
    
    def create_iam_roles(self) -> bool:
        """Create IAM roles."""
        print(f"\n👤 Creating IAM roles")
        
        # Task Role
        task_role_created = self._create_task_role()
        
        # Execution Role
        execution_role_created = self._create_execution_role()
        
        # Scheduler Role
        scheduler_role_created = self._create_scheduler_role()
        
        return all([task_role_created, execution_role_created, scheduler_role_created])
    
    def _create_task_role(self) -> bool:
        """Create ECS task role."""
        print(f"  Creating task role: {TASK_ROLE_NAME}")
        
        if self.dry_run:
            print("    [DRY RUN] Would create task role")
            return True
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role exists
            self.iam.get_role(RoleName=TASK_ROLE_NAME)
            print(f"    ✓ Task role already exists")
        except self.iam.exceptions.NoSuchEntityException:
            # Create role
            try:
                self.iam.create_role(
                    RoleName=TASK_ROLE_NAME,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Task role for FX Analysis ECS tasks",
                    MaxSessionDuration=3600
                )
                print(f"    ✅ Created task role")
            except Exception as e:
                print(f"    ❌ Failed to create task role: {e}")
                return False
        
        # Attach policies
        policies = [
            {
                "name": f"{TASK_ROLE_NAME}-s3-policy",
                "document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject",
                                "s3:PutObjectAcl",
                                "s3:GetObject",
                                "s3:DeleteObject"
                            ],
                            "Resource": f"arn:aws:s3:::{S3_BUCKET}/*"
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:ListBucket"
                            ],
                            "Resource": f"arn:aws:s3:::{S3_BUCKET}"
                        }
                    ]
                }
            },
            {
                "name": f"{TASK_ROLE_NAME}-secrets-policy",
                "document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "secretsmanager:GetSecretValue"
                            ],
                            "Resource": [
                                f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:*"
                            ]
                        }
                    ]
                }
            }
        ]
        
        for policy in policies:
            try:
                self.iam.put_role_policy(
                    RoleName=TASK_ROLE_NAME,
                    PolicyName=policy["name"],
                    PolicyDocument=json.dumps(policy["document"])
                )
                print(f"    ✓ Attached policy: {policy['name']}")
            except Exception as e:
                print(f"    ⚠️  Failed to attach policy {policy['name']}: {e}")
        
        return True
    
    def _create_execution_role(self) -> bool:
        """Create ECS execution role."""
        print(f"  Creating execution role: {EXECUTION_ROLE_NAME}")
        
        if self.dry_run:
            print("    [DRY RUN] Would create execution role")
            return True
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role exists
            self.iam.get_role(RoleName=EXECUTION_ROLE_NAME)
            print(f"    ✓ Execution role already exists")
        except self.iam.exceptions.NoSuchEntityException:
            # Create role
            try:
                self.iam.create_role(
                    RoleName=EXECUTION_ROLE_NAME,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Execution role for FX Analysis ECS tasks"
                )
                print(f"    ✅ Created execution role")
                
                # Attach managed policy
                self.iam.attach_role_policy(
                    RoleName=EXECUTION_ROLE_NAME,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
                )
                print(f"    ✓ Attached AmazonECSTaskExecutionRolePolicy")
                
            except Exception as e:
                print(f"    ❌ Failed to create execution role: {e}")
                return False
        
        # Add secrets access policy
        secrets_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:*"
                }
            ]
        }
        
        try:
            self.iam.put_role_policy(
                RoleName=EXECUTION_ROLE_NAME,
                PolicyName="SecretsAccess",
                PolicyDocument=json.dumps(secrets_policy)
            )
            print(f"    ✓ Added secrets access policy")
        except Exception as e:
            print(f"    ⚠️  Failed to add secrets policy: {e}")
        
        return True
    
    def _create_scheduler_role(self) -> bool:
        """Create EventBridge Scheduler role."""
        print(f"  Creating scheduler role: {SCHEDULER_ROLE_NAME}")
        
        if self.dry_run:
            print("    [DRY RUN] Would create scheduler role")
            return True
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "scheduler.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role exists
            self.iam.get_role(RoleName=SCHEDULER_ROLE_NAME)
            print(f"    ✓ Scheduler role already exists")
        except self.iam.exceptions.NoSuchEntityException:
            # Create role
            try:
                self.iam.create_role(
                    RoleName=SCHEDULER_ROLE_NAME,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Role for EventBridge Scheduler to run ECS tasks"
                )
                print(f"    ✅ Created scheduler role")
            except Exception as e:
                print(f"    ❌ Failed to create scheduler role: {e}")
                return False
        
        # Attach ECS run task policy
        ecs_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecs:RunTask"
                    ],
                    "Resource": [
                        f"arn:aws:ecs:{self.region}:{self.account_id}:task-definition/{ECS_TASK_FAMILY}:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": [
                        f"arn:aws:iam::{self.account_id}:role/{TASK_ROLE_NAME}",
                        f"arn:aws:iam::{self.account_id}:role/{EXECUTION_ROLE_NAME}"
                    ]
                }
            ]
        }
        
        try:
            self.iam.put_role_policy(
                RoleName=SCHEDULER_ROLE_NAME,
                PolicyName="ECSRunTask",
                PolicyDocument=json.dumps(ecs_policy)
            )
            print(f"    ✓ Attached ECS run task policy")
        except Exception as e:
            print(f"    ⚠️  Failed to attach policy: {e}")
        
        return True
    
    def create_ecs_task_definition(self) -> bool:
        """Create ECS task definition."""
        print(f"\n🐳 Creating ECS task definition: {ECS_TASK_FAMILY}")
        
        if self.dry_run:
            print("  [DRY RUN] Would create task definition")
            return True
        
        # Get role ARNs
        try:
            task_role = self.iam.get_role(RoleName=TASK_ROLE_NAME)
            task_role_arn = task_role['Role']['Arn']
            
            execution_role = self.iam.get_role(RoleName=EXECUTION_ROLE_NAME)
            execution_role_arn = execution_role['Role']['Arn']
        except Exception as e:
            print(f"  ❌ Failed to get role ARNs: {e}")
            return False
        
        # Task definition
        task_definition = {
            "family": ECS_TASK_FAMILY,
            "taskRoleArn": task_role_arn,
            "executionRoleArn": execution_role_arn,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "256",
            "memory": "512",
            "containerDefinitions": [
                {
                    "name": "analyze-fx",
                    "image": f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{ECR_REPOSITORY}:latest",
                    "essential": True,
                    "environment": [
                        {"name": "APP_NAME", "value": "analyze-fx"},
                        {"name": "TZ", "value": "Asia/Tokyo"},
                        {"name": "PAIR", "value": "USDJPY"},
                        {"name": "SYMBOL", "value": "USD/JPY"},
                        {"name": "TIMEFRAMES", "value": "5m,1h"},
                        {"name": "S3_PREFIX", "value": "charts"},
                        {"name": "LOG_LEVEL", "value": "INFO"},
                        {"name": "DATA_SOURCE", "value": "twelvedata"},
                        {"name": "AWS_DEFAULT_REGION", "value": self.region}
                    ],
                    "secrets": [
                        {
                            "name": "NOTION_API_KEY",
                            "valueFrom": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:NOTION_API_KEY"
                        },
                        {
                            "name": "NOTION_DB_ID",
                            "valueFrom": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:NOTION_DB_ID"
                        },
                        {
                            "name": "SLACK_WEBHOOK_URL",
                            "valueFrom": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:SLACK_WEBHOOK_URL"
                        },
                        {
                            "name": "S3_BUCKET",
                            "valueFrom": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:S3_BUCKET"
                        },
                        {
                            "name": "TWELVEDATA_API_KEY",
                            "valueFrom": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:TWELVEDATA_API_KEY"
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": LOG_GROUP,
                            "awslogs-region": self.region,
                            "awslogs-stream-prefix": "ecs"
                        }
                    }
                }
            ]
        }
        
        try:
            response = self.ecs.register_task_definition(**task_definition)
            revision = response['taskDefinition']['revision']
            print(f"  ✅ Created task definition (revision: {revision})")
            return True
        except Exception as e:
            print(f"  ❌ Failed to create task definition: {e}")
            return False
    
    def create_cloudwatch_log_group(self) -> bool:
        """Create CloudWatch log group."""
        print(f"\n📊 Creating CloudWatch log group: {LOG_GROUP}")
        
        if self.dry_run:
            print("  [DRY RUN] Would create log group")
            return True
        
        try:
            # Check if log group exists
            self.logs.describe_log_groups(logGroupNamePrefix=LOG_GROUP)
            print(f"  ✓ Log group already exists")
            return True
        except:
            pass
        
        try:
            self.logs.create_log_group(
                logGroupName=LOG_GROUP,
                tags={
                    'Application': 'analyze-fx',
                    'Environment': 'production'
                }
            )
            print(f"  ✅ Created log group")
            
            # Set retention (optional - 30 days)
            self.logs.put_retention_policy(
                logGroupName=LOG_GROUP,
                retentionInDays=30
            )
            print(f"  ✓ Set retention to 30 days")
            
            return True
        except Exception as e:
            print(f"  ❌ Failed to create log group: {e}")
            return False
    
    def create_eventbridge_schedulers(self) -> bool:
        """Create EventBridge schedulers."""
        print(f"\n⏰ Creating EventBridge schedulers")
        
        # Get scheduler role ARN
        try:
            role = self.iam.get_role(RoleName=SCHEDULER_ROLE_NAME)
            role_arn = role['Role']['Arn']
        except Exception as e:
            print(f"  ❌ Failed to get scheduler role: {e}")
            return False
        
        schedulers = [
            {
                "name": "fx-analyzer-0800-jst-dev",
                "expression": "cron(0 23 ? * MON-FRI *)",  # 8:00 JST = 23:00 UTC
                "description": "FX Analysis - Development (8:00 JST weekdays)"
            },
            {
                "name": "fx-analyzer-0800-jst",
                "expression": "cron(0 23 ? * MON-FRI *)",  # 8:00 JST = 23:00 UTC
                "description": "FX Analysis - Production (8:00 JST weekdays)"
            }
        ]
        
        success = True
        for scheduler in schedulers:
            print(f"  Creating scheduler: {scheduler['name']}")
            
            if self.dry_run:
                print("    [DRY RUN] Would create scheduler")
                continue
            
            try:
                # Check if scheduler exists
                self.scheduler.get_schedule(Name=scheduler['name'])
                print(f"    ✓ Scheduler already exists")
                continue
            except self.scheduler.exceptions.ResourceNotFoundException:
                pass
            
            # Create scheduler
            try:
                self.scheduler.create_schedule(
                    Name=scheduler['name'],
                    Description=scheduler['description'],
                    ScheduleExpression=scheduler['expression'],
                    Target={
                        'Arn': f"arn:aws:ecs:{self.region}:{self.account_id}:cluster/{ECS_CLUSTER}",
                        'RoleArn': role_arn,
                        'EcsParameters': {
                            'TaskDefinitionArn': f"arn:aws:ecs:{self.region}:{self.account_id}:task-definition/{ECS_TASK_FAMILY}",
                            'NetworkConfiguration': {
                                'awsvpcConfiguration': {
                                    'Subnets': SUBNETS,
                                    'SecurityGroups': [SECURITY_GROUP],
                                    'AssignPublicIp': 'ENABLED'
                                }
                            },
                            'LaunchType': 'FARGATE',
                            'PlatformVersion': 'LATEST'
                        },
                        'RetryPolicy': {
                            'MaximumRetryAttempts': 2,
                            'MaximumEventAge': 3600
                        }
                    },
                    State='DISABLED',  # Start in disabled state
                    FlexibleTimeWindow={
                        'Mode': 'OFF'
                    }
                )
                print(f"    ✅ Created scheduler (DISABLED state)")
            except Exception as e:
                print(f"    ❌ Failed to create scheduler: {e}")
                success = False
        
        return success
    
    def create_twelvedata_secret(self) -> bool:
        """Create TWELVEDATA_API_KEY secret."""
        print(f"\n🔐 Creating TWELVEDATA_API_KEY secret")
        
        if self.dry_run:
            print("  [DRY RUN] Would create secret")
            return True
        
        try:
            # Check if secret exists
            self.secrets.describe_secret(SecretId="TWELVEDATA_API_KEY")
            print(f"  ✓ Secret already exists")
            print(f"  ℹ️  Please update the secret value manually:")
            print(f"     aws secretsmanager put-secret-value --secret-id TWELVEDATA_API_KEY --secret-string 'your-api-key'")
            return True
        except self.secrets.exceptions.ResourceNotFoundException:
            # Create secret
            try:
                response = self.secrets.create_secret(
                    Name="TWELVEDATA_API_KEY",
                    Description="TwelveData API key for FX Analysis",
                    SecretString="REPLACE_WITH_ACTUAL_KEY"
                )
                print(f"  ✅ Created secret (placeholder value)")
                print(f"  ⚠️  IMPORTANT: Update the secret with your actual API key:")
                print(f"     aws secretsmanager put-secret-value --secret-id TWELVEDATA_API_KEY --secret-string 'your-api-key'")
                return True
            except Exception as e:
                print(f"  ❌ Failed to create secret: {e}")
                return False
    
    def verify_ecs_cluster(self) -> bool:
        """Verify ECS cluster exists."""
        print(f"\n🐳 Verifying ECS cluster: {ECS_CLUSTER}")
        
        try:
            clusters = self.ecs.describe_clusters(clusters=[ECS_CLUSTER])
            if clusters['clusters']:
                print(f"  ✓ Cluster exists and is {clusters['clusters'][0]['status']}")
                return True
            else:
                print(f"  ❌ Cluster not found")
                print(f"  ℹ️  Create cluster manually or use:")
                print(f"     aws ecs create-cluster --cluster-name {ECS_CLUSTER}")
                return False
        except Exception as e:
            print(f"  ❌ Failed to check cluster: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete setup."""
        print("\n🚀 Starting AWS Environment Setup")
        print("=" * 60)
        
        results = {
            "ECR Repository": self.create_ecr_repository(),
            "IAM Roles": self.create_iam_roles(),
            "CloudWatch Logs": self.create_cloudwatch_log_group(),
            "ECS Cluster": self.verify_ecs_cluster(),
            "ECS Task Definition": self.create_ecs_task_definition(),
            "TwelveData Secret": self.create_twelvedata_secret(),
            "EventBridge Schedulers": self.create_eventbridge_schedulers()
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 SETUP SUMMARY")
        print("=" * 60)
        
        for item, status in results.items():
            symbol = "✅" if status else "❌"
            print(f"{symbol} {item}: {'Success' if status else 'Failed'}")
        
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"\nCompleted: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("\n✅ Setup completed successfully!")
            print("\n📝 Next steps:")
            print("1. Update TWELVEDATA_API_KEY secret with your actual API key")
            print("2. Build and push Docker image:")
            print("   make ecr-push")
            print("3. Enable schedulers when ready:")
            print("   aws scheduler update-schedule --name fx-analyzer-0800-jst --state ENABLED")
            print("4. Run audit to verify:")
            print("   make audit")
            return True
        else:
            print("\n⚠️  Setup completed with some failures")
            print("Please review the errors above and run setup again if needed")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Environment Setup for FX Analysis')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without creating resources')
    parser.add_argument('--region', default=AWS_REGION, help=f'AWS region (default: {AWS_REGION})')
    args = parser.parse_args()
    
    print(f"🏢 Account: {ACCOUNT_ID}")
    print(f"📍 Region: {args.region}")
    
    try:
        setup = AWSSetup(region=args.region, dry_run=args.dry_run)
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
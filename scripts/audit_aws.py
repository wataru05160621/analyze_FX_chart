#!/usr/bin/env python
"""AWS configuration audit script for FX Analysis system."""

import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from tabulate import tabulate

# Configuration
AWS_REGION = "ap-northeast-1"
ACCOUNT_ID = "455931011903"
S3_BUCKET = f"analyze-fx-{ACCOUNT_ID}-apne1"

# Required resources
REQUIRED_SECRETS = [
    "NOTION_API_KEY",
    "NOTION_DB_ID", 
    "SLACK_WEBHOOK_URL",
    "S3_BUCKET",
    "TWELVEDATA_API_KEY"
]

REQUIRED_SUBNETS = [
    "subnet-06fba36a849bb6647",
    "subnet-02aef8bf85b9ceb0d"
]

SECURITY_GROUP = "sg-03cb601e40f6e32ac"
ECS_CLUSTER = "analyze-fx-cluster"
ECS_TASK_DEFINITION = "analyze-fx"
ECR_REPOSITORY = "analyze-fx"
LOG_GROUP = "/ecs/analyze-fx"

SCHEDULERS = [
    "fx-analyzer-0800-jst-dev",
    "fx-analyzer-0800-jst"
]

class AWSAuditor:
    """AWS configuration auditor."""
    
    def __init__(self, region: str = AWS_REGION):
        """Initialize AWS clients."""
        self.region = region
        self.account_id = ACCOUNT_ID
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "region": region,
            "account_id": self.account_id,
            "checks": {}
        }
        
        try:
            # Initialize AWS clients
            self.sts = boto3.client('sts', region_name=region)
            self.secrets = boto3.client('secretsmanager', region_name=region)
            self.s3 = boto3.client('s3', region_name=region)
            self.ecs = boto3.client('ecs', region_name=region)
            self.scheduler = boto3.client('scheduler', region_name=region)
            self.ecr = boto3.client('ecr', region_name=region)
            self.iam = boto3.client('iam', region_name=region)
            self.ec2 = boto3.client('ec2', region_name=region)
            self.logs = boto3.client('logs', region_name=region)
        except NoCredentialsError:
            print("❌ No AWS credentials found. Please configure AWS CLI or set environment variables.")
            sys.exit(1)
    
    def check_caller_identity(self) -> Dict:
        """Check STS caller identity."""
        try:
            identity = self.sts.get_caller_identity()
            result = {
                "status": "OK",
                "account": identity['Account'],
                "arn": identity['Arn'],
                "user_id": identity['UserId']
            }
            
            # Verify account ID
            if identity['Account'] != self.account_id:
                result["status"] = "WARNING"
                result["message"] = f"Account mismatch. Expected: {self.account_id}, Got: {identity['Account']}"
            
            return result
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def check_secrets(self) -> Dict:
        """Check Secrets Manager secrets."""
        results = {}
        
        for secret_name in REQUIRED_SECRETS:
            try:
                response = self.secrets.describe_secret(SecretId=secret_name)
                results[secret_name] = {
                    "status": "OK",
                    "arn": response['ARN'],
                    "last_changed": response.get('LastChangedDate', '').isoformat() if 'LastChangedDate' in response else 'N/A',
                    "rotation_enabled": response.get('RotationEnabled', False),
                    "description": response.get('Description', '')
                }
            except self.secrets.exceptions.ResourceNotFoundException:
                results[secret_name] = {
                    "status": "MISSING",
                    "message": f"Secret '{secret_name}' not found"
                }
            except Exception as e:
                results[secret_name] = {
                    "status": "ERROR",
                    "message": str(e)
                }
        
        return results
    
    def check_s3_bucket(self) -> Dict:
        """Check S3 bucket configuration."""
        result = {"bucket": S3_BUCKET}
        
        try:
            # Check bucket exists
            self.s3.head_bucket(Bucket=S3_BUCKET)
            result["exists"] = True
            
            # Check encryption
            try:
                encryption = self.s3.get_bucket_encryption(Bucket=S3_BUCKET)
                result["encryption"] = {
                    "status": "OK",
                    "type": encryption['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                }
            except self.s3.exceptions.ServerSideEncryptionConfigurationNotFoundError:
                result["encryption"] = {"status": "WARNING", "message": "No encryption configured"}
            
            # Check public access block
            try:
                pab = self.s3.get_public_access_block(Bucket=S3_BUCKET)
                config = pab['PublicAccessBlockConfiguration']
                all_blocked = all([
                    config.get('BlockPublicAcls', False),
                    config.get('IgnorePublicAcls', False),
                    config.get('BlockPublicPolicy', False),
                    config.get('RestrictPublicBuckets', False)
                ])
                result["public_access_block"] = {
                    "status": "OK" if all_blocked else "WARNING",
                    "all_blocked": all_blocked
                }
            except self.s3.exceptions.NoSuchPublicAccessBlockConfiguration:
                result["public_access_block"] = {"status": "WARNING", "message": "No public access block configured"}
            
            # Check lifecycle rules
            try:
                lifecycle = self.s3.get_bucket_lifecycle_configuration(Bucket=S3_BUCKET)
                charts_rule = None
                for rule in lifecycle.get('Rules', []):
                    if 'charts/' in str(rule.get('Filter', {}).get('Prefix', '')):
                        charts_rule = rule
                        break
                
                result["lifecycle"] = {
                    "status": "OK" if charts_rule else "WARNING",
                    "charts_rule": bool(charts_rule),
                    "rule_status": charts_rule.get('Status') if charts_rule else None
                }
            except self.s3.exceptions.NoSuchLifecycleConfiguration:
                result["lifecycle"] = {"status": "INFO", "message": "No lifecycle rules configured"}
            
            result["status"] = "OK"
            
        except self.s3.exceptions.NoSuchBucket:
            result["status"] = "ERROR"
            result["exists"] = False
            result["message"] = f"Bucket '{S3_BUCKET}' does not exist"
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)
        
        return result
    
    def check_ecs(self) -> Dict:
        """Check ECS cluster and task definition."""
        result = {}
        
        # Check cluster
        try:
            clusters = self.ecs.describe_clusters(clusters=[ECS_CLUSTER])
            if clusters['clusters']:
                cluster = clusters['clusters'][0]
                result["cluster"] = {
                    "status": "OK",
                    "name": cluster['clusterName'],
                    "status_value": cluster['status'],
                    "running_tasks": cluster.get('runningTasksCount', 0),
                    "pending_tasks": cluster.get('pendingTasksCount', 0)
                }
            else:
                result["cluster"] = {
                    "status": "ERROR",
                    "message": f"Cluster '{ECS_CLUSTER}' not found"
                }
        except Exception as e:
            result["cluster"] = {"status": "ERROR", "message": str(e)}
        
        # Check task definition
        try:
            task_def = self.ecs.describe_task_definition(taskDefinition=ECS_TASK_DEFINITION)
            td = task_def['taskDefinition']
            
            # Check container definitions for secrets
            container_secrets = {}
            for container in td.get('containerDefinitions', []):
                secrets = container.get('secrets', [])
                for secret in secrets:
                    container_secrets[secret['name']] = secret['valueFrom']
            
            # Check if required secrets are referenced
            missing_secrets = []
            for secret in REQUIRED_SECRETS:
                if secret not in container_secrets:
                    missing_secrets.append(secret)
            
            # Check logging configuration
            log_config = None
            for container in td.get('containerDefinitions', []):
                if container.get('logConfiguration'):
                    log_config = container['logConfiguration']
                    break
            
            result["task_definition"] = {
                "status": "OK" if not missing_secrets else "WARNING",
                "family": td['family'],
                "revision": td['revision'],
                "cpu": td.get('cpu'),
                "memory": td.get('memory'),
                "secrets_configured": len(container_secrets),
                "missing_secrets": missing_secrets,
                "log_driver": log_config.get('logDriver') if log_config else None,
                "log_group": log_config.get('options', {}).get('awslogs-group') if log_config else None
            }
            
        except Exception as e:
            result["task_definition"] = {"status": "ERROR", "message": str(e)}
        
        return result
    
    def check_eventbridge_schedulers(self) -> Dict:
        """Check EventBridge Scheduler configurations."""
        results = {}
        
        for scheduler_name in SCHEDULERS:
            try:
                schedule = self.scheduler.get_schedule(Name=scheduler_name)
                
                # Extract target configuration
                target = schedule.get('Target', {})
                ecs_params = target.get('EcsParameters', {})
                network_config = ecs_params.get('NetworkConfiguration', {}).get('awsvpcConfiguration', {})
                
                results[scheduler_name] = {
                    "status": "OK",
                    "state": schedule.get('State'),
                    "schedule_expression": schedule.get('ScheduleExpression'),
                    "role_arn": target.get('RoleArn'),
                    "task_definition": ecs_params.get('TaskDefinitionArn'),
                    "subnets": network_config.get('Subnets', []),
                    "security_groups": network_config.get('SecurityGroups', []),
                    "assign_public_ip": network_config.get('AssignPublicIp')
                }
                
                # Validate configuration
                warnings = []
                if set(network_config.get('Subnets', [])) != set(REQUIRED_SUBNETS):
                    warnings.append("Subnet mismatch")
                if SECURITY_GROUP not in network_config.get('SecurityGroups', []):
                    warnings.append(f"Security group {SECURITY_GROUP} not configured")
                if network_config.get('AssignPublicIp') != 'ENABLED':
                    warnings.append("Public IP not enabled")
                
                if warnings:
                    results[scheduler_name]["status"] = "WARNING"
                    results[scheduler_name]["warnings"] = warnings
                    
            except self.scheduler.exceptions.ResourceNotFoundException:
                results[scheduler_name] = {
                    "status": "MISSING",
                    "message": f"Scheduler '{scheduler_name}' not found"
                }
            except Exception as e:
                results[scheduler_name] = {
                    "status": "ERROR",
                    "message": str(e)
                }
        
        return results
    
    def check_ecr(self) -> Dict:
        """Check ECR repository."""
        result = {"repository": ECR_REPOSITORY}
        
        try:
            # Check repository exists
            repos = self.ecr.describe_repositories(repositoryNames=[ECR_REPOSITORY])
            
            if repos['repositories']:
                repo = repos['repositories'][0]
                result["status"] = "OK"
                result["uri"] = repo['repositoryUri']
                result["created_at"] = repo['createdAt'].isoformat()
                
                # Check for latest tag
                try:
                    images = self.ecr.describe_images(
                        repositoryName=ECR_REPOSITORY,
                        imageIds=[{'imageTag': 'latest'}]
                    )
                    if images['imageDetails']:
                        latest = images['imageDetails'][0]
                        result["latest_tag"] = {
                            "exists": True,
                            "pushed_at": latest['imagePushedAt'].isoformat(),
                            "size_mb": round(latest['imageSizeInBytes'] / (1024 * 1024), 2)
                        }
                    else:
                        result["latest_tag"] = {"exists": False}
                except self.ecr.exceptions.ImageNotFoundException:
                    result["latest_tag"] = {"exists": False, "message": "No 'latest' tag found"}
                    
        except self.ecr.exceptions.RepositoryNotFoundException:
            result["status"] = "ERROR"
            result["message"] = f"Repository '{ECR_REPOSITORY}' not found"
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)
        
        return result
    
    def check_iam_roles(self) -> Dict:
        """Check IAM roles and policies."""
        results = {}
        
        # Check task role
        task_role_name = "analyze-fx-task-role"
        try:
            role = self.iam.get_role(RoleName=task_role_name)
            
            # Get attached policies
            attached_policies = self.iam.list_attached_role_policies(RoleName=task_role_name)
            policy_names = [p['PolicyName'] for p in attached_policies['AttachedPolicies']]
            
            # Check for required permissions (simplified check)
            has_secrets = any('Secret' in p for p in policy_names)
            has_s3 = any('S3' in p for p in policy_names)
            
            results["task_role"] = {
                "status": "OK" if (has_secrets or has_s3) else "WARNING",
                "arn": role['Role']['Arn'],
                "policies": policy_names,
                "has_secrets_access": has_secrets,
                "has_s3_access": has_s3
            }
        except self.iam.exceptions.NoSuchEntityException:
            results["task_role"] = {
                "status": "WARNING",
                "message": f"Role '{task_role_name}' not found"
            }
        except Exception as e:
            results["task_role"] = {"status": "ERROR", "message": str(e)}
        
        # Check EventBridge Scheduler role
        try:
            # List roles with specific pattern
            roles = self.iam.list_roles(PathPrefix='/service-role/')
            scheduler_roles = [r for r in roles['Roles'] if 'EventBridge_Scheduler_ECS' in r['RoleName']]
            
            if scheduler_roles:
                role = scheduler_roles[0]
                # Check trust policy
                trust_policy = role['AssumeRolePolicyDocument']
                has_scheduler_trust = any(
                    'scheduler.amazonaws.com' in str(statement.get('Principal', {}))
                    for statement in trust_policy.get('Statement', [])
                )
                
                results["scheduler_role"] = {
                    "status": "OK" if has_scheduler_trust else "WARNING",
                    "arn": role['Arn'],
                    "has_scheduler_trust": has_scheduler_trust
                }
            else:
                results["scheduler_role"] = {
                    "status": "WARNING",
                    "message": "No EventBridge Scheduler role found"
                }
                
        except Exception as e:
            results["scheduler_role"] = {"status": "ERROR", "message": str(e)}
        
        return results
    
    def check_vpc_resources(self) -> Dict:
        """Check VPC resources (subnets and security groups)."""
        result = {}
        
        # Check subnets
        try:
            subnets = self.ec2.describe_subnets(SubnetIds=REQUIRED_SUBNETS)
            result["subnets"] = {
                "status": "OK",
                "count": len(subnets['Subnets']),
                "details": []
            }
            
            for subnet in subnets['Subnets']:
                result["subnets"]["details"].append({
                    "id": subnet['SubnetId'],
                    "availability_zone": subnet['AvailabilityZone'],
                    "cidr": subnet['CidrBlock'],
                    "available_ips": subnet['AvailableIpAddressCount']
                })
                
        except self.ec2.exceptions.ClientError as e:
            if 'InvalidSubnetID.NotFound' in str(e):
                result["subnets"] = {
                    "status": "ERROR",
                    "message": "One or more subnets not found"
                }
            else:
                result["subnets"] = {"status": "ERROR", "message": str(e)}
        
        # Check security group
        try:
            sgs = self.ec2.describe_security_groups(GroupIds=[SECURITY_GROUP])
            if sgs['SecurityGroups']:
                sg = sgs['SecurityGroups'][0]
                result["security_group"] = {
                    "status": "OK",
                    "id": sg['GroupId'],
                    "name": sg.get('GroupName'),
                    "vpc_id": sg['VpcId'],
                    "ingress_rules": len(sg.get('IpPermissions', [])),
                    "egress_rules": len(sg.get('IpPermissionsEgress', []))
                }
        except self.ec2.exceptions.ClientError as e:
            if 'InvalidGroup.NotFound' in str(e):
                result["security_group"] = {
                    "status": "ERROR",
                    "message": f"Security group '{SECURITY_GROUP}' not found"
                }
            else:
                result["security_group"] = {"status": "ERROR", "message": str(e)}
        
        return result
    
    def check_cloudwatch_logs(self) -> Dict:
        """Check CloudWatch Logs configuration."""
        result = {"log_group": LOG_GROUP}
        
        try:
            response = self.logs.describe_log_groups(logGroupNamePrefix=LOG_GROUP)
            
            log_group_found = None
            for lg in response.get('logGroups', []):
                if lg['logGroupName'] == LOG_GROUP:
                    log_group_found = lg
                    break
            
            if log_group_found:
                result["status"] = "OK"
                result["arn"] = log_group_found['arn']
                result["retention_days"] = log_group_found.get('retentionInDays', 'Never expire')
                result["stored_bytes"] = log_group_found.get('storedBytes', 0)
                
                # Check for recent log streams
                streams = self.logs.describe_log_streams(
                    logGroupName=LOG_GROUP,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=1
                )
                
                if streams['logStreams']:
                    latest_stream = streams['logStreams'][0]
                    if 'lastEventTimestamp' in latest_stream:
                        result["last_event"] = datetime.fromtimestamp(
                            latest_stream['lastEventTimestamp'] / 1000
                        ).isoformat()
                    
            else:
                result["status"] = "ERROR"
                result["message"] = f"Log group '{LOG_GROUP}' not found"
                
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)
        
        return result
    
    def run_audit(self) -> Dict:
        """Run all audit checks."""
        print("\n🔍 Starting AWS Configuration Audit...")
        print("=" * 60)
        
        # STS Check
        print("\n📌 Checking AWS Identity...")
        self.report["checks"]["identity"] = self.check_caller_identity()
        self._print_check_result("AWS Identity", self.report["checks"]["identity"])
        
        # Secrets Manager Check
        print("\n🔐 Checking Secrets Manager...")
        self.report["checks"]["secrets"] = self.check_secrets()
        self._print_secrets_table(self.report["checks"]["secrets"])
        
        # S3 Check
        print("\n📦 Checking S3 Bucket...")
        self.report["checks"]["s3"] = self.check_s3_bucket()
        self._print_check_result("S3 Bucket", self.report["checks"]["s3"])
        
        # ECS Check
        print("\n🐳 Checking ECS Resources...")
        self.report["checks"]["ecs"] = self.check_ecs()
        self._print_ecs_results(self.report["checks"]["ecs"])
        
        # EventBridge Scheduler Check
        print("\n⏰ Checking EventBridge Schedulers...")
        self.report["checks"]["schedulers"] = self.check_eventbridge_schedulers()
        self._print_scheduler_results(self.report["checks"]["schedulers"])
        
        # ECR Check
        print("\n🗄️ Checking ECR Repository...")
        self.report["checks"]["ecr"] = self.check_ecr()
        self._print_check_result("ECR Repository", self.report["checks"]["ecr"])
        
        # IAM Check
        print("\n👤 Checking IAM Roles...")
        self.report["checks"]["iam"] = self.check_iam_roles()
        self._print_iam_results(self.report["checks"]["iam"])
        
        # VPC Check
        print("\n🌐 Checking VPC Resources...")
        self.report["checks"]["vpc"] = self.check_vpc_resources()
        self._print_vpc_results(self.report["checks"]["vpc"])
        
        # CloudWatch Logs Check
        print("\n📊 Checking CloudWatch Logs...")
        self.report["checks"]["logs"] = self.check_cloudwatch_logs()
        self._print_check_result("CloudWatch Logs", self.report["checks"]["logs"])
        
        return self.report
    
    def _print_check_result(self, name: str, result: Dict):
        """Print individual check result."""
        status = result.get("status", "UNKNOWN")
        symbol = self._get_status_symbol(status)
        
        print(f"{symbol} {name}: {status}")
        
        if status == "ERROR":
            print(f"   ❗ {result.get('message', 'Unknown error')}")
        elif status == "WARNING" and "message" in result:
            print(f"   ⚠️  {result['message']}")
        elif status == "OK":
            # Print key details
            for key, value in result.items():
                if key not in ["status", "message"] and not isinstance(value, dict):
                    print(f"   • {key}: {value}")
    
    def _print_secrets_table(self, secrets: Dict):
        """Print secrets in table format."""
        table_data = []
        for name, info in secrets.items():
            status_symbol = self._get_status_symbol(info["status"])
            table_data.append([
                name,
                status_symbol,
                info.get("last_changed", "N/A")[:10] if info.get("last_changed") != "N/A" else "N/A",
                "✓" if info.get("rotation_enabled") else "✗",
                info.get("message", "")[:30] if "message" in info else ""
            ])
        
        headers = ["Secret Name", "Status", "Last Changed", "Rotation", "Notes"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def _print_ecs_results(self, ecs: Dict):
        """Print ECS check results."""
        # Cluster
        cluster = ecs.get("cluster", {})
        print(f"{self._get_status_symbol(cluster.get('status'))} Cluster: {cluster.get('status')}")
        if cluster.get("status") == "OK":
            print(f"   • Running tasks: {cluster.get('running_tasks')}")
            print(f"   • Pending tasks: {cluster.get('pending_tasks')}")
        
        # Task Definition
        task_def = ecs.get("task_definition", {})
        print(f"{self._get_status_symbol(task_def.get('status'))} Task Definition: {task_def.get('status')}")
        if task_def.get("status") in ["OK", "WARNING"]:
            print(f"   • Family: {task_def.get('family')}")
            print(f"   • Revision: {task_def.get('revision')}")
            print(f"   • CPU/Memory: {task_def.get('cpu')}/{task_def.get('memory')}")
            print(f"   • Secrets configured: {task_def.get('secrets_configured')}")
            if task_def.get("missing_secrets"):
                print(f"   ⚠️  Missing secrets: {', '.join(task_def['missing_secrets'])}")
    
    def _print_scheduler_results(self, schedulers: Dict):
        """Print scheduler check results."""
        for name, info in schedulers.items():
            status_symbol = self._get_status_symbol(info.get("status"))
            print(f"{status_symbol} {name}: {info.get('status')}")
            
            if info.get("status") in ["OK", "WARNING"]:
                print(f"   • State: {info.get('state')}")
                print(f"   • Schedule: {info.get('schedule_expression')}")
                if info.get("warnings"):
                    for warning in info["warnings"]:
                        print(f"   ⚠️  {warning}")
    
    def _print_iam_results(self, iam: Dict):
        """Print IAM check results."""
        for role_type, info in iam.items():
            status_symbol = self._get_status_symbol(info.get("status"))
            role_name = "Task Role" if role_type == "task_role" else "Scheduler Role"
            print(f"{status_symbol} {role_name}: {info.get('status')}")
            
            if info.get("status") in ["OK", "WARNING"]:
                if "policies" in info:
                    print(f"   • Policies: {len(info['policies'])} attached")
                if "has_secrets_access" in info:
                    print(f"   • Secrets access: {'✓' if info['has_secrets_access'] else '✗'}")
                if "has_s3_access" in info:
                    print(f"   • S3 access: {'✓' if info['has_s3_access'] else '✗'}")
    
    def _print_vpc_results(self, vpc: Dict):
        """Print VPC check results."""
        # Subnets
        subnets = vpc.get("subnets", {})
        print(f"{self._get_status_symbol(subnets.get('status'))} Subnets: {subnets.get('status')}")
        if subnets.get("details"):
            for subnet in subnets["details"]:
                print(f"   • {subnet['id']}: {subnet['availability_zone']} ({subnet['available_ips']} IPs available)")
        
        # Security Group
        sg = vpc.get("security_group", {})
        print(f"{self._get_status_symbol(sg.get('status'))} Security Group: {sg.get('status')}")
        if sg.get("status") == "OK":
            print(f"   • ID: {sg.get('id')}")
            print(f"   • Rules: {sg.get('ingress_rules')} ingress, {sg.get('egress_rules')} egress")
    
    def _get_status_symbol(self, status: str) -> str:
        """Get status symbol for display."""
        symbols = {
            "OK": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "MISSING": "🔍",
            "INFO": "ℹ️"
        }
        return symbols.get(status, "❓")
    
    def save_report(self, filename: str = "audit_report.json"):
        """Save audit report to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\n💾 Report saved to {filename}")
    
    def print_summary(self):
        """Print audit summary."""
        print("\n" + "=" * 60)
        print("📋 AUDIT SUMMARY")
        print("=" * 60)
        
        # Count statuses
        status_counts = {}
        for check_name, check_data in self.report["checks"].items():
            if isinstance(check_data, dict):
                if "status" in check_data:
                    status = check_data["status"]
                    status_counts[status] = status_counts.get(status, 0) + 1
                else:
                    # For nested checks like secrets
                    for item_name, item_data in check_data.items():
                        if isinstance(item_data, dict) and "status" in item_data:
                            status = item_data["status"]
                            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"✅ OK: {status_counts.get('OK', 0)}")
        print(f"⚠️  WARNING: {status_counts.get('WARNING', 0)}")
        print(f"❌ ERROR: {status_counts.get('ERROR', 0)}")
        print(f"🔍 MISSING: {status_counts.get('MISSING', 0)}")
        
        # Overall status
        if status_counts.get('ERROR', 0) > 0 or status_counts.get('MISSING', 0) > 0:
            print("\n🚨 Action Required: Critical issues found!")
            print("   Please review ERROR and MISSING items above.")
        elif status_counts.get('WARNING', 0) > 0:
            print("\n⚠️  Review Recommended: Some warnings detected.")
            print("   System may work but review warnings for best practices.")
        else:
            print("\n✅ All Checks Passed: System is properly configured!")


def main():
    """Main entry point."""
    print("🚀 FX Analysis System - AWS Configuration Audit")
    print(f"📍 Region: {AWS_REGION}")
    print(f"🏢 Account: {ACCOUNT_ID}")
    
    try:
        auditor = AWSAuditor()
        report = auditor.run_audit()
        auditor.save_report()
        auditor.print_summary()
        
        # Exit with appropriate code
        has_errors = any(
            item.get("status") in ["ERROR", "MISSING"]
            for check in report["checks"].values()
            if isinstance(check, dict)
            for item in ([check] if "status" in check else check.values())
            if isinstance(item, dict)
        )
        
        sys.exit(1 if has_errors else 0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
from typing import Dict, Any, List
import time
import logging
from backend.connectors.base import BaseConnector
from backend.connectors.schemas import ConnectorResult
from backend.graph.schemas import Observation, AssetObservation, ServiceObservation, IdentityObservation, AssetRef

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

class AWSConnector(BaseConnector):
    """Production AWS Connector."""
    
    @property
    def connector_type(self) -> str:
        return "AWS"

    def __init__(self, **config):
        self.config = config
        self.account_id = config.get("account_id", "unknown")
        self.region = config.get("region", "us-east-1")
        self.role_arn = config.get("role_arn")

    def _get_session(self):
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 is not installed.")
        
        if self.role_arn:
            sts = boto3.client('sts')
            assumed = sts.assume_role(RoleArn=self.role_arn, RoleSessionName="AegisDiscovery")
            creds = assumed['Credentials']
            return boto3.Session(
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken'],
                region_name=self.region
            )
        return boto3.Session(region_name=self.region)

    def collect(self, observed_at: float, context: str = "default") -> ConnectorResult:
        observations = []
        errors = []
        
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available. Falling back to explicit failure.")
            return ConnectorResult(
                connector_id=f"aws-{self.account_id}",
                observed_at=observed_at,
                observations=tuple(),
                metadata={"error": "boto3 not installed", "status": "FAILED"}
            )

        try:
            session = self._get_session()
            
            # 1. Discover VPCs
            ec2 = session.client('ec2')
            vpcs = ec2.describe_vpcs().get('Vpcs', [])
            for vpc in vpcs:
                vpc_id = vpc['VpcId']
                observations.append(AssetObservation(
                    ref=AssetRef(cloud_id=vpc_id),
                    source="aws",
                    evidence=("aws:ec2:describe-vpcs",),
                    observed_at=observed_at,
                    attributes={"cloud_provider": "aws", "region": self.region, "vpc_id": vpc_id, "is_default": vpc.get('IsDefault', False)}
                ))

            # 2. Discover EC2 Instances
            paginator = ec2.get_paginator('describe_instances')
            for page in paginator.paginate():
                for res in page.get('Reservations', []):
                    for inst in res.get('Instances', []):
                        inst_id = inst['InstanceId']
                        vpc_id = inst.get('VpcId', 'unknown')
                        observations.append(AssetObservation(
                            ref=AssetRef(cloud_id=inst_id),
                            source="aws",
                            evidence=("aws:ec2:describe-instances",),
                            observed_at=observed_at,
                            attributes={
                                "cloud_provider": "aws", 
                                "instance_type": inst.get('InstanceType'), 
                                "vpc_id": vpc_id, 
                                "state": inst.get('State', {}).get('Name')
                            }
                        ))

            # 3. Discover RDS Instances
            rds = session.client('rds')
            db_paginator = rds.get_paginator('describe_db_instances')
            for page in db_paginator.paginate():
                for db in page.get('DBInstances', []):
                    db_id = db['DBInstanceIdentifier']
                    port = db.get('Endpoint', {}).get('Port', 5432)
                    observations.append(ServiceObservation(
                        host=AssetRef(cloud_id=db_id),
                        port=port,
                        product_signature=db.get('Engine', 'unknown'),
                        source="aws",
                        evidence=("aws:rds:describe-db-instances",),
                        observed_at=observed_at,
                        metadata={"cloud_provider": "aws", "status": db.get('DBInstanceStatus'), "public": db.get('PubliclyAccessible', False)}
                    ))

            # 4. Discover IAM Roles
            iam = session.client('iam')
            iam_paginator = iam.get_paginator('list_roles')
            for page in iam_paginator.paginate():
                for role in page.get('Roles', []):
                    role_name = role['RoleName']
                    role_arn = role['Arn']
                    observations.append(IdentityObservation(
                        iam_id=role_arn,
                        identity_type="role",
                        source="aws",
                        evidence=("aws:iam:list-roles",),
                        observed_at=observed_at,
                        attributes={"cloud_provider": "aws", "name": role_name}
                    ))

            # Fetch account ID dynamically if unknown
            if self.account_id == "unknown":
                sts = session.client('sts')
                self.account_id = sts.get_caller_identity().get('Account', 'unknown')

        except NoCredentialsError:
            errors.append("No AWS credentials found. Running in dry/unauthenticated mode.")
            logger.error("AWS authentication failed.")
        except ClientError as e:
            errors.append(f"AWS ClientError: {str(e)}")
            logger.error(f"AWS API Error: {e}")
        except Exception as e:
            errors.append(f"AWS Unexpected Error: {str(e)}")
            logger.error(f"AWS General Error: {e}")

        status = "COMPLETED" if not errors else ("PARTIAL" if observations else "FAILED")

        return ConnectorResult(
            connector_id=f"aws-{self.account_id}",
            observed_at=observed_at,
            observations=tuple(observations),
            metadata={
                "account_id": self.account_id, 
                "region": self.region,
                "entities_discovered": len(observations),
                "errors": errors,
                "status": status
            }
        )

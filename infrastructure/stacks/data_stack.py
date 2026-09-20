"""Phase 1 durable data resources for TheManager."""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
    aws_dynamodb as dynamodb,
    aws_budgets as budgets,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class DataStack(Stack):
    """Creates encrypted stores with an explicit demo/production retention switch."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        application: str,
        deployment_environment: str,
        cost_center: str,
        aws_region: str,
        retain_data: bool,
        budget_notification_email: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        removal_policy = RemovalPolicy.RETAIN if retain_data else RemovalPolicy.DESTROY
        Tags.of(self).add("Application", application)
        Tags.of(self).add("Environment", deployment_environment)
        Tags.of(self).add("ManagedBy", "AWS-CDK")
        Tags.of(self).add("CostCenter", cost_center)

        self.report_bucket = s3.Bucket(
            self,
            "Reports",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=removal_policy,
            auto_delete_objects=not retain_data,
        )
        budgets.CfnBudget(
            self,
            "MonthlyCostBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name=f"{application}-{deployment_environment}-monthly",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=50, unit="USD"),
                budget_type="COST",
                time_unit="MONTHLY",
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[budgets.CfnBudget.SubscriberProperty(address=budget_notification_email, subscription_type="EMAIL")],
                )
            ],
        )

        self.tables = {
            name: self._table(name, partition_key, ttl_attribute, removal_policy)
            for name, partition_key, ttl_attribute in (
                ("Sessions", "session_id", "expires_at"),
                ("Events", "event_id", "expires_at"),
                ("ThinkingLogs", "thinking_log_id", "expires_at"),
                ("Alerts", "alert_id", "expires_at"),
                ("Actions", "action_id", "expires_at"),
                ("RiskSnapshots", "snapshot_id", "expires_at"),
                ("WorkflowRuns", "workflow_id", "expires_at"),
            )
        }

        self.database_secret = secretsmanager.Secret(
            self,
            "AuroraCredentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"themanager_admin"}',
                generate_string_key="password",
                exclude_punctuation=True,
            ),
            removal_policy=removal_policy,
        )

        vpc = ec2.Vpc(
            self,
            "DatabaseVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                )
            ],
        )
        db_security_group = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=vpc,
            allow_all_outbound=False,
            description="TheManager Aurora access is granted explicitly by application stacks.",
        )
        subnet_group = rds.CfnDBSubnetGroup(
            self,
            "AuroraSubnetGroup",
            db_subnet_group_description="TheManager Aurora isolated subnets",
            subnet_ids=[subnet.subnet_id for subnet in vpc.isolated_subnets],
        )
        self.database_cluster = rds.CfnDBCluster(
            self,
            "AuroraCluster",
            engine="aurora-postgresql",
            database_name="themanager",
            db_subnet_group_name=subnet_group.ref,
            vpc_security_group_ids=[db_security_group.security_group_id],
            master_username=self.database_secret.secret_value_from_json("username").unsafe_unwrap(),
            master_user_password=self.database_secret.secret_value_from_json("password").unsafe_unwrap(),
            enable_http_endpoint=True,
            backup_retention_period=7,
            storage_encrypted=True,
            serverless_v2_scaling_configuration=rds.CfnDBCluster.ServerlessV2ScalingConfigurationProperty(
                min_capacity=0.5,
                max_capacity=1.0,
            ),
            deletion_protection=retain_data,
        )
        self.database_cluster.apply_removal_policy(removal_policy)
        self.database_cluster.add_dependency(subnet_group)
        instance = rds.CfnDBInstance(
            self,
            "AuroraServerlessInstance",
            db_cluster_identifier=self.database_cluster.ref,
            db_instance_class="db.serverless",
            engine="aurora-postgresql",
        )
        instance.add_dependency(self.database_cluster)
        instance.apply_removal_policy(removal_policy)

        CfnOutput(self, "ReportBucketName", value=self.report_bucket.bucket_name)
        CfnOutput(self, "DatabaseSecretArn", value=self.database_secret.secret_arn)
        CfnOutput(self, "DatabaseClusterArn", value=self.database_cluster.attr_db_cluster_arn)

    def _table(
        self,
        name: str,
        partition_key: str,
        ttl_attribute: str | None,
        removal_policy: RemovalPolicy,
    ) -> dynamodb.Table:
        return dynamodb.Table(
            self,
            name,
            partition_key=dynamodb.Attribute(name=partition_key, type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            time_to_live_attribute=ttl_attribute,
            removal_policy=removal_policy,
        )

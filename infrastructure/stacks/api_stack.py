"""Containerized FastAPI runtime exposed through a Lambda Function URL."""

from aws_cdk import CfnOutput, Duration, Stack, Tags, aws_iam as iam, aws_lambda as lambda_
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, data, agents, workflow, application: str, deployment_environment: str, cost_center: str, aws_region: str, supervisor_model_id: str, routine_model_id: str, tavily_secret_name: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)
        for key, value in {"Application": application, "Environment": deployment_environment, "ManagedBy": "AWS-CDK", "CostCenter": cost_center}.items(): Tags.of(self).add(key, value)
        self.api_role = iam.Role(self, "ApiRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        self.api_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        self.api_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess"))
        supervisor_model_resource = supervisor_model_id if supervisor_model_id.startswith("arn:") else self.format_arn(service="bedrock", region=aws_region, resource=f"inference-profile/{supervisor_model_id}")
        routine_model_resource = routine_model_id if routine_model_id.startswith("arn:") else self.format_arn(service="bedrock", region=aws_region, resource=f"inference-profile/{routine_model_id}")
        self.api_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    supervisor_model_resource,
                    routine_model_resource,
                    "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-northeast-2::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-northeast-3::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-south-2::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-southeast-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:ap-southeast-4::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                ],
            )
        )

        self.api_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:ApplyGuardrail"],
                resources=[agents.guardrail.attr_guardrail_arn],
            )
        )
        self.api_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "aws-marketplace:ViewSubscriptions",
                    "aws-marketplace:Subscribe",
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "aws:CalledViaLast": "bedrock.amazonaws.com",
                    }
                },
            )
        )
        self.function = lambda_.DockerImageFunction(self, "Api", code=lambda_.DockerImageCode.from_image_asset("../backend", file="Dockerfile.api"), role=self.api_role, memory_size=2048, timeout=Duration.minutes(15), tracing=lambda_.Tracing.ACTIVE, environment={
            "THEMANAGER_AWS_REGION": self.region, "BEDROCK_SUPERVISOR_MODEL_ID": supervisor_model_id, "BEDROCK_ROUTINE_MODEL_ID": routine_model_id, "BEDROCK_GUARDRAIL_ID": agents.guardrail.attr_guardrail_arn,
            "REPORT_BUCKET": data.report_bucket.bucket_name, "AURORA_CLUSTER_ARN": data.database_cluster.attr_db_cluster_arn, "AURORA_SECRET_ARN": data.database_secret.secret_arn, "TAVILY_SECRET_NAME": tavily_secret_name,
            "SESSIONS_TABLE": data.tables["Sessions"].table_name, "EVENTS_TABLE": data.tables["Events"].table_name, "WORKFLOW_RUNS_TABLE": data.tables["WorkflowRuns"].table_name,
            "WORKFLOW_STATE_MACHINE_ARN": workflow.state_machine.state_machine_arn, "COGNITO_USER_POOL_ID": agents.user_pool.user_pool_id, "COGNITO_CLIENT_ID": agents.user_pool_client.user_pool_client_id,
        })
        data.report_bucket.grant_read_write(self.api_role)
        data.database_secret.grant_read(self.api_role)
        agents.tavily_secret.grant_read(self.api_role)
        for table in data.tables.values(): table.grant_read_write_data(self.api_role)
        self.api_role.add_to_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement"], resources=[data.database_cluster.attr_db_cluster_arn]))
        workflow.state_machine.grant_start_execution(self.api_role)
        self.url = self.function.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE, cors=lambda_.FunctionUrlCorsOptions(allowed_origins=["*"], allowed_methods=[lambda_.HttpMethod.ALL], allowed_headers=["Authorization", "Content-Type"]))
        CfnOutput(self, "ApiUrl", value=self.url.url)

"""Phase 1 identity and observability resources for Bedrock agents."""

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    Tags,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class AgentsStack(Stack):
    """Defines the least-privilege execution role; model access is scoped later."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        application: str,
        deployment_environment: str,
        cost_center: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        Tags.of(self).add("Application", application)
        Tags.of(self).add("Environment", deployment_environment)
        Tags.of(self).add("ManagedBy", "AWS-CDK")
        Tags.of(self).add("CostCenter", cost_center)
        self.agent_log_group = logs.LogGroup(
            self,
            "AgentLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.agent_role = iam.Role(
            self,
            "AgentExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for TheManager agent compute.",
        )
        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[self.agent_log_group.log_group_arn],
            )
        )
        self.tavily_secret = secretsmanager.Secret.from_secret_name_v2(self, "TavilySecret", "themanager/tavily")
        self.tavily_secret.grant_read(self.agent_role)
        self.user_pool = cognito.UserPool(
            self,
            "Users",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            prevent_user_existence_errors=True,
        )
        CfnOutput(self, "AgentRoleArn", value=self.agent_role.role_arn)
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)

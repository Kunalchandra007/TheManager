"""Phase 1 identity and observability resources for Bedrock agents."""

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    Tags,
    aws_cognito as cognito,
    aws_bedrock as bedrock,
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
        aws_region: str,
        supervisor_model_id: str,
        routine_model_id: str,
        tavily_secret_name: str,
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

        self.agent_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        self.agent_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSXRayDaemonWriteAccess"
            )
        )

        self.tavily_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "TavilySecret",
            tavily_secret_name,
        )

        self.tavily_secret.grant_read(self.agent_role)

        self.guardrail = bedrock.CfnGuardrail(
            self,
            "AgentGuardrail",
            name=f"{application}-{deployment_environment}-guardrail",
            description=(
                "Blocks harmful content and prompt attacks "
                "in TheManager agent calls."
            ),
            blocked_input_messaging="This request cannot be processed.",
            blocked_outputs_messaging=(
                "The generated response was blocked by safety controls."
            ),
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength=(
                            "NONE" if kind == "PROMPT_ATTACK" else "MEDIUM"
                        ),
                        type=kind,
                    )
                    for kind in (
                        "HATE",
                        "INSULTS",
                        "SEXUAL",
                        "VIOLENCE",
                        "PROMPT_ATTACK",
                    )
                ]
            ),
        )

        routine_model_resource = (
            routine_model_id
            if routine_model_id.startswith("arn:")
            else self.format_arn(
                service="bedrock",
                region=aws_region,
                resource=f"inference-profile/{routine_model_id}",
            )
        )

        self.agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ApplyGuardrail",
                ],
                resources=[
                    supervisor_model_id,
                    routine_model_resource,
                    self.guardrail.attr_guardrail_arn,
                ],
            )
        )

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
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            prevent_user_existence_errors=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[
                    "https://main.d21imlkj49tuxf.amplifyapp.com",
                ],
                logout_urls=[
                    "https://main.d21imlkj49tuxf.amplifyapp.com",
                ],
            ),
        )

        CfnOutput(
            self,
            "AgentRoleArn",
            value=self.agent_role.role_arn,
        )

        CfnOutput(
            self,
            "UserPoolId",
            value=self.user_pool.user_pool_id,
        )

        CfnOutput(
            self,
            "UserPoolClientId",
            value=self.user_pool_client.user_pool_client_id,
        )

        CfnOutput(
            self,
            "GuardrailArn",
            value=self.guardrail.attr_guardrail_arn,
        )
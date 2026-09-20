"""Amplify Hosting foundation; repository connection is authorized by the owner in AWS."""

from aws_cdk import CfnOutput, Stack, Tags, aws_amplify as amplify
from constructs import Construct


class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, api, agents, application: str, deployment_environment: str, cost_center: str, aws_region: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)
        for key, value in {"Application": application, "Environment": deployment_environment, "ManagedBy": "AWS-CDK", "CostCenter": cost_center}.items(): Tags.of(self).add(key, value)
        self.app = amplify.CfnApp(self, "Hosting", name=f"{application}-{deployment_environment}", platform="WEB_COMPUTE", environment_variables=[amplify.CfnApp.EnvironmentVariableProperty(name="THEMANAGER_API_URL", value=api.url.url), amplify.CfnApp.EnvironmentVariableProperty(name="NEXT_PUBLIC_COGNITO_USER_POOL_ID", value=agents.user_pool.user_pool_id), amplify.CfnApp.EnvironmentVariableProperty(name="NEXT_PUBLIC_COGNITO_CLIENT_ID", value=agents.user_pool_client.user_pool_client_id)])
        self.branch = amplify.CfnBranch(self, "MainBranch", app_id=self.app.attr_app_id, branch_name="main", enable_auto_build=True, stage="PRODUCTION")
        CfnOutput(self, "AmplifyAppId", value=self.app.attr_app_id)

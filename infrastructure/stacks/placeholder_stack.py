"""Phase 0 CDK stack placeholders with a stable target-stack layout."""

from aws_cdk import CfnOutput, Stack, Tags
from constructs import Construct


class MigrationPlaceholderStack(Stack):
    """A resource-free stack that reserves an independently deployable boundary."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        responsibility: str,
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
        CfnOutput(self, "MigrationResponsibility", value=responsibility)

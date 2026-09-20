"""Tests for Phase 0 stack boundaries and mandatory tags."""

import unittest

import aws_cdk as cdk
from aws_cdk import assertions

from stacks.placeholder_stack import MigrationPlaceholderStack
from stacks.data_stack import DataStack
from stacks.agents_stack import AgentsStack
from stacks.workflow_stack import WorkflowStack


class MigrationPlaceholderStackTests(unittest.TestCase):
    @staticmethod
    def settings() -> dict[str, object]:
        return {
            "env": cdk.Environment(account="125474112843", region="ap-south-1"),
            "application": "themanager",
            "deployment_environment": "test",
            "cost_center": "demo",
            "aws_region": "ap-south-1",
        }

    def test_stack_has_migration_output_and_standard_tags(self) -> None:
        app = cdk.App()
        stack = MigrationPlaceholderStack(
            app,
            "TestStack",
            responsibility="Test boundary",
            application="themanager",
            deployment_environment="test",
            cost_center="demo",
        )

        template = assertions.Template.from_stack(stack)
        template.has_output(
            "MigrationResponsibility",
            {"Value": "Test boundary"},
        )

    def test_data_stack_has_encrypted_durable_foundation_resources(self) -> None:
        app = cdk.App()
        stack = DataStack(app, "DataTestStack", retain_data=False, budget_notification_email="budget@example.test", **self.settings())
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::DynamoDB::Table", 7)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketEncryption": {"ServerSideEncryptionConfiguration": assertions.Match.any_value()},
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                },
                "VersioningConfiguration": {"Status": "Enabled"},
            },
        )
        template.resource_count_is("AWS::SecretsManager::Secret", 1)
        template.resource_count_is("AWS::RDS::DBCluster", 1)
        template.resource_count_is("AWS::RDS::DBInstance", 1)
        template.resource_count_is("AWS::Budgets::Budget", 1)
        template.has_resource_properties("AWS::RDS::DBCluster", {
            "DeletionProtection": False,
            "ServerlessV2ScalingConfiguration": {"MinCapacity": 0.5, "MaxCapacity": 1.0},
        })

    def test_agents_stack_has_identity_and_observability_resources(self) -> None:
        app = cdk.App()
        stack = AgentsStack(
            app,
            "AgentsTestStack",
            supervisor_model_id="arn:aws:bedrock:ap-south-1:125474112843:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0",
            routine_model_id="apac.amazon.nova-pro-v1:0",
            tavily_secret_name="themanager/tavily",
            **self.settings(),
        )
        template = assertions.Template.from_stack(stack)

        template.resource_count_is("AWS::Cognito::UserPool", 1)
        template.resource_count_is("AWS::Cognito::UserPoolClient", 1)
        template.resource_count_is("AWS::Logs::LogGroup", 1)
        template.resource_count_is("AWS::IAM::Role", 1)

    def test_workflow_stack_has_schedule_state_machine_and_dead_letter_queue(self) -> None:
        app = cdk.App()
        data = DataStack(app, "WorkflowDataTestStack", retain_data=False, budget_notification_email="budget@example.test", **self.settings())
        agents = AgentsStack(app, "WorkflowAgentsTestStack", supervisor_model_id="arn:aws:bedrock:ap-south-1:125474112843:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0", routine_model_id="apac.amazon.nova-pro-v1:0", tavily_secret_name="themanager/tavily", **self.settings())
        stack = WorkflowStack(app, "WorkflowTestStack", data=data, agents=agents, supervisor_model_id="arn:aws:bedrock:ap-south-1:125474112843:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0", routine_model_id="apac.amazon.nova-pro-v1:0", tavily_secret_name="themanager/tavily", **self.settings())
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::StepFunctions::StateMachine", 1)
        template.resource_count_is("AWS::Events::Rule", 1)
        template.resource_count_is("AWS::SQS::Queue", 1)
        template.resource_count_is("AWS::SNS::Topic", 1)


if __name__ == "__main__":
    unittest.main()

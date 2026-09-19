#!/usr/bin/env python3
"""CDK entry point for the TheManager AWS migration."""

import aws_cdk as cdk

from stacks.placeholder_stack import MigrationPlaceholderStack
from stacks.agents_stack import AgentsStack
from stacks.data_stack import DataStack
from stacks.workflow_stack import WorkflowStack


app = cdk.App()
application = app.node.try_get_context("application") or "themanager"
environment = app.node.try_get_context("environment") or "dev"
cost_center = app.node.try_get_context("costCenter") or "demo"

common_properties = {
    "application": application,
    "deployment_environment": environment,
    "cost_center": cost_center,
}

DataStack(app, "TheManagerData", **common_properties)
AgentsStack(app, "TheManagerAgents", **common_properties)
WorkflowStack(app, "TheManagerWorkflow", **common_properties)

for stack_name, responsibility in (
    ("TheManagerApi", "FastAPI compute, ingress, and observability"),
    ("TheManagerFrontend", "Amplify hosting and Cognito integration"),
):
    MigrationPlaceholderStack(
        app,
        stack_name,
        responsibility=responsibility,
        **common_properties,
    )

app.synth()

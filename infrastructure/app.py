#!/usr/bin/env python3
"""CDK entry point for the TheManager AWS migration."""

import os

import aws_cdk as cdk

from stacks.agents_stack import AgentsStack
from stacks.data_stack import DataStack
from stacks.workflow_stack import WorkflowStack
from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack


app = cdk.App()
application = app.node.try_get_context("application") or "themanager"
environment = app.node.try_get_context("environment") or "dev"
cost_center = app.node.try_get_context("costCenter") or "demo"
aws_region = app.node.try_get_context("awsRegion") or "ap-south-1"
retain_data = str(app.node.try_get_context("retainData") or "false").lower() == "true"
budget_notification_email = os.environ.get("BUDGET_NOTIFICATION_EMAIL")

if not budget_notification_email:
    raise ValueError("Set BUDGET_NOTIFICATION_EMAIL before synthesizing or deploying the Data stack.")

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
supervisor_model_id = os.environ.get("BEDROCK_SUPERVISOR_MODEL_ID") or "apac.amazon.nova-pro-v1:0"
routine_model_id = os.environ.get("BEDROCK_ROUTINE_MODEL_ID") or "apac.amazon.nova-pro-v1:0"
tavily_secret_name = os.environ.get("TAVILY_SECRET_NAME") or "themanager/tavily"

common_properties = {
    "application": application,
    "deployment_environment": environment,
    "cost_center": cost_center,
    "aws_region": aws_region,
}

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=aws_region,
)

data = DataStack(app, "TheManagerData", env=env, retain_data=retain_data, budget_notification_email=budget_notification_email, **common_properties)
agents = AgentsStack(app, "TheManagerAgents", env=env, supervisor_model_id=supervisor_model_id, routine_model_id=routine_model_id, tavily_secret_name=tavily_secret_name, **common_properties)
workflow = WorkflowStack(app, "TheManagerWorkflow", data=data, agents=agents, env=env, supervisor_model_id=supervisor_model_id, routine_model_id=routine_model_id, tavily_secret_name=tavily_secret_name, **common_properties)
api = ApiStack(app, "TheManagerApi", data=data, agents=agents, workflow=workflow, env=env, supervisor_model_id=supervisor_model_id, routine_model_id=routine_model_id, tavily_secret_name=tavily_secret_name, **common_properties)
FrontendStack(app, "TheManagerFrontend", api=api, agents=agents, env=env, **common_properties)

app.synth()

"""EventBridge/Step Functions workflow with a real Lambda task worker."""

from aws_cdk import CfnOutput, Duration, Stack, Tags, aws_events as events, aws_events_targets as targets, aws_iam as iam, aws_lambda as lambda_, aws_sns as sns, aws_sqs as sqs, aws_stepfunctions as sfn, aws_stepfunctions_tasks as tasks
from constructs import Construct


class WorkflowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, data, agents, application: str, deployment_environment: str, cost_center: str, aws_region: str, supervisor_model_id: str, routine_model_id: str, tavily_secret_name: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)
        for key, value in {"Application": application, "Environment": deployment_environment, "ManagedBy": "AWS-CDK", "CostCenter": cost_center}.items():
            Tags.of(self).add(key, value)
        self.alert_topic = sns.Topic(self, "TheManagerAlerts", display_name="TheManager alerts")
        self.dead_letter_queue = sqs.Queue(self, "WorkflowDeadLetterQueue", encryption=sqs.QueueEncryption.SQS_MANAGED, retention_period=Duration.days(14))
        self.worker_role = self._execution_role("WorkflowWorkerRole", agents, aws_region, supervisor_model_id, routine_model_id)
        self.worker = lambda_.DockerImageFunction(
            self,
            "WorkflowWorker",
            code=lambda_.DockerImageCode.from_image_asset("../backend", file="Dockerfile.worker"),
            role=self.worker_role,
            memory_size=2048,
            timeout=Duration.minutes(15),
            tracing=lambda_.Tracing.ACTIVE,
            environment=self._environment(data, agents, supervisor_model_id, routine_model_id, tavily_secret_name),
        )
        self._grant_data_access(data, agents)
        task = tasks.LambdaInvoke(self, "RunRiskAnalysis", lambda_function=self.worker, output_path="$.Payload")
        self.state_machine = sfn.StateMachine(self, "TheManagerWorkflow", definition_body=sfn.DefinitionBody.from_chainable(task), timeout=Duration.minutes(15), tracing_enabled=True)
        self.schedule = events.Rule(self, "DailyTheManager", schedule=events.Schedule.cron(minute="0", hour="5"), targets=[targets.SfnStateMachine(self.state_machine, dead_letter_queue=self.dead_letter_queue)])
        CfnOutput(self, "WorkflowStateMachineArn", value=self.state_machine.state_machine_arn)
        CfnOutput(self, "AlertsTopicArn", value=self.alert_topic.topic_arn)

    def _environment(self, data, agents, supervisor_model_id: str, routine_model_id: str, tavily_secret_name: str) -> dict[str, str]:
        return {
            "THEMANAGER_AWS_REGION": self.region, "BEDROCK_SUPERVISOR_MODEL_ID": supervisor_model_id, "BEDROCK_ROUTINE_MODEL_ID": routine_model_id, "BEDROCK_GUARDRAIL_ID": agents.guardrail.attr_guardrail_arn,
            "REPORT_BUCKET": data.report_bucket.bucket_name, "AURORA_CLUSTER_ARN": data.database_cluster.attr_db_cluster_arn, "AURORA_SECRET_ARN": data.database_secret.secret_arn,
            "TAVILY_SECRET_NAME": tavily_secret_name, "SESSIONS_TABLE": data.tables["Sessions"].table_name, "EVENTS_TABLE": data.tables["Events"].table_name, "WORKFLOW_RUNS_TABLE": data.tables["WorkflowRuns"].table_name,
        }

    def _grant_data_access(self, data, agents) -> None:
        data.report_bucket.grant_read_write(self.worker_role)
        data.database_secret.grant_read(self.worker_role)
        agents.tavily_secret.grant_read(self.worker_role)
        for table in data.tables.values():
            table.grant_read_write_data(self.worker_role)
        self.worker_role.add_to_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement", "rds-data:BeginTransaction", "rds-data:CommitTransaction", "rds-data:RollbackTransaction"], resources=[data.database_cluster.attr_db_cluster_arn]))

    def _execution_role(self, name: str, agents, aws_region: str, supervisor_model_id: str, routine_model_id: str) -> iam.Role:
        role = iam.Role(self, name, assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess"))
        routine_model_resource = routine_model_id if routine_model_id.startswith("arn:") else self.format_arn(service="bedrock", region=aws_region, resource=f"inference-profile/{routine_model_id}")
        role.add_to_policy(iam.PolicyStatement(actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream", "bedrock:ApplyGuardrail"], resources=[supervisor_model_id, routine_model_resource, agents.guardrail.attr_guardrail_arn]))
        return role

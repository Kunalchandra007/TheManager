"""Phase 5 EventBridge/Step Functions workflow infrastructure."""

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, Tags, aws_events as events, aws_events_targets as targets, aws_iam as iam, aws_sns as sns, aws_sqs as sqs, aws_stepfunctions as sfn
from constructs import Construct


class WorkflowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, application: str, deployment_environment: str, cost_center: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)
        for key, value in {"Application": application, "Environment": deployment_environment, "ManagedBy": "AWS-CDK", "CostCenter": cost_center}.items():
            Tags.of(self).add(key, value)

        self.alert_topic = sns.Topic(self, "TheManagerAlerts", display_name="TheManager alerts")
        self.dead_letter_queue = sqs.Queue(self, "WorkflowDeadLetterQueue", encryption=sqs.QueueEncryption.SQS_MANAGED, retention_period=Duration.days(14))
        definition = sfn.Pass(self, "AnalyseSchedule", result=sfn.Result.from_object({"stage": "analysis"})).next(
            sfn.Pass(self, "GenerateReport", result=sfn.Result.from_object({"stage": "report"}))
        )
        self.state_machine = sfn.StateMachine(self, "TheManagerWorkflow", definition_body=sfn.DefinitionBody.from_chainable(definition), timeout=Duration.minutes(15))
        self.schedule = events.Rule(
            self,
            "DailyTheManager",
            schedule=events.Schedule.cron(minute="0", hour="5"),
            targets=[targets.SfnStateMachine(self.state_machine, dead_letter_queue=self.dead_letter_queue)],
        )
        CfnOutput(self, "WorkflowStateMachineArn", value=self.state_machine.state_machine_arn)
        CfnOutput(self, "AlertsTopicArn", value=self.alert_topic.topic_arn)

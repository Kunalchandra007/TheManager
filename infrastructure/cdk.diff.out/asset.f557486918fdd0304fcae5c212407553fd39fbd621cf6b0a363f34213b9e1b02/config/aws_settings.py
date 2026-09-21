"""AWS runtime configuration loaded from environment references, never committed secrets."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AwsSettings:
    region: str
    supervisor_model_id: str
    report_bucket: str
    database_cluster_arn: str
    database_secret_arn: str
    tavily_secret_name: str

    @classmethod
    def from_environment(cls) -> "AwsSettings":
        configured_region = os.getenv("THEMANAGER_AWS_REGION") or os.getenv("AWS_REGION")
        runtime_region = os.getenv("AWS_REGION")
        if configured_region and runtime_region and configured_region != runtime_region:
            raise ValueError("THEMANAGER_AWS_REGION must match the Lambda AWS_REGION")
        required = {key: os.getenv(key) for key in ("BEDROCK_SUPERVISOR_MODEL_ID", "REPORT_BUCKET", "AURORA_CLUSTER_ARN", "AURORA_SECRET_ARN")}
        required["AWS_REGION"] = configured_region
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing AWS runtime configuration: {', '.join(missing)}")
        return cls(required["AWS_REGION"] or "", required["BEDROCK_SUPERVISOR_MODEL_ID"] or "", required["REPORT_BUCKET"] or "", required["AURORA_CLUSTER_ARN"] or "", required["AURORA_SECRET_ARN"] or "", os.getenv("TAVILY_SECRET_NAME", "themanager/tavily"))

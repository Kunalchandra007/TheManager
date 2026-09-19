# TheManager AWS infrastructure

This CDK application is the Phase 0 foundation for the TheManager AWS migration. It deliberately creates no billable resources yet; Phase 1 will populate the stacks after AWS account, region, Bedrock model access, and budget ownership are confirmed.

## Stack boundaries

| Stack | Planned responsibility |
|---|---|
| `TheManagerData` | Aurora PostgreSQL, DynamoDB, S3, secrets, backups |
| `TheManagerAgents` | Bedrock permissions, Guardrails, search integration |
| `TheManagerApi` | FastAPI Lambda/container, API endpoint, CloudWatch |
| `TheManagerWorkflow` | EventBridge Scheduler, Step Functions, SNS, DLQ |
| `TheManagerFrontend` | Amplify Hosting, Cognito integration and DNS |

All stacks receive shared `Application`, `Environment`, `ManagedBy`, and `CostCenter` tags. Set these through CDK context, not source edits.

## Prerequisites

- Python 3.11+
- Node.js 18+ and AWS CDK CLI (`npm install -g aws-cdk`)
- AWS credentials for the intended account and region
- Bedrock model access approved in the intended region before Phase 3
- A budget alarm created by the account owner before Phase 1 deployment

## Local verification

```powershell
cd infrastructure
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cdk synth
python -m unittest discover -s tests -v
```

Synthesizing does not deploy resources. Do not run `cdk deploy` until account readiness in [`docs/aws-account-readiness.md`](../docs/aws-account-readiness.md) is signed off. When deploying later, use explicit AWS credentials and an explicit `environment` context value, for example `cdk synth -c environment=dev`.

Secrets never belong in CDK context, source files, or committed `.env` files. Phase 1 will create empty Secrets Manager references; values are supplied out of band.

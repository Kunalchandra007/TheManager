# AWS account readiness checklist

This checklist blocks Phase 1 deployment. It is intentionally operational rather than a source-code configuration file.

- [ ] Choose the AWS account and deployment region.
- [ ] Create a budget and an email budget alert; record the owner and monthly limit outside this repository.
- [ ] Confirm access to the Bedrock models selected for supervisor/reporting and simple tasks in the selected region.
- [ ] Identify the Cognito owner, SES sender identity, and SNS recipients.
- [ ] Confirm Aurora Serverless v2 capacity limits and the data-retention policy.
- [ ] Confirm a Secrets Manager/SSM operator and secret rotation policy.
- [ ] Bootstrap the account with `cdk bootstrap aws://ACCOUNT_ID/REGION` using an approved deployment role.

Do not record account IDs, ARNs, credentials, sender addresses, budget amounts, or search-provider keys in this repository.

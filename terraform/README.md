# terraform/

Infrastructure-as-code for the **optional AWS reference architecture** (S3, IAM, Glue, and optionally Redshift).

**Important:** this Terraform is provided so the AWS design can be explained and, if desired, deployed — it is not applied automatically by any pipeline or CI job in this repository. Redshift in particular is not free; deploying it is a deliberate, manual, cost-aware decision documented in `docs/architecture/aws_reference_architecture.md`, including teardown (`terraform destroy`) instructions. No AWS credentials are ever hard-coded here — configuration uses variables and standard AWS credential resolution (profiles/environment variables/IAM roles).

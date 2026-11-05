# container_registry

Creates the persistent CMS API image repository.

## Purpose

Keep API images available between check sessions.

## Layer and callers

Singleton layer; called by `awsenv/dev/singleton`.

## Resources

`aws_ecr_repository.this` stores images; `aws_ecr_lifecycle_policy.this` expires untagged images after one day (priority 1), then expires images beyond the most recent `images_to_keep` (priority 2, any tag status).

## Inputs

| Input | Type | Default | Validation |
| --- | --- | --- | --- |
| `repository_name` | `string` | Required | `^cms-[a-z0-9-]+$` |
| `images_to_keep` | `number` | `5` | Positive integer |

## Outputs

| Output | Meaning |
| --- | --- |
| `repository_name` | Repository name |
| `repository_arn` | Repository ARN |
| `repository_url` | Image push URL |

## Example

```hcl
module "container_registry" {
  source          = "../../../modules/container_registry"
  repository_name = "cms-api"
}
```

## Security

Immutable tags prevent overwriting a commit image; scan on push is enabled. Images use AES256 encryption (Q-D9). Common tags are inherited from provider `default_tags`. No repository policy or IAM is created. US06 must check whether a SHA tag already exists and treat it as a successful push, skipping build and push for that tag.

## Cost

Plan estimate: [ECR storage](https://aws.amazon.com/ecr/pricing/) about $0.10 per GB-month, with five images retained by default; untagged images expire after one day. Storage is billed between sessions.

## Teardown

`force_delete = true` deletes the repository even with images (Q-D12). Keep singleton between sessions; destroy only for final teardown.

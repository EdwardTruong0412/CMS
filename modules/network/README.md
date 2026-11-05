# network

Creates the two-zone public, private and isolated CMS network.

## Purpose

Provide the group network shared by session resources, with NAT sizing selected through tfvars.

## Layer and callers

Group layer; called by `awsenv/dev/group`. It does not read singleton. Later env resources consume group outputs.

## Resources

VPC, closed default security group, internet gateway, six subnets, NAT EIPs and gateways, four route tables, separate public/private default routes, and six subnet associations.

| Tier | ap-southeast-1a | ap-southeast-1b | Name tags |
| --- | --- | --- | --- |
| Public | `10.20.0.0/24` | `10.20.1.0/24` | `cms-public-a/b` |
| Private | `10.20.10.0/24` | `10.20.11.0/24` | `cms-private-a/b` |
| Isolated | `10.20.20.0/24` | `10.20.21.0/24` | `cms-isolated-a/b` |

The caller supplies `10.20.0.0/16`; the module adds eight prefix bits, at offsets 0/1, 10/11 and 20/21. Public subnets use the internet gateway. Private subnets have separate route tables: lean routes both through NAT a; full routes each through its own NAT. Isolated subnets share a table with only the implicit local route.

## Inputs

| Input | Type | Default | Validation |
| --- | --- | --- | --- |
| `name_prefix` | `string` | Required | `^[a-z][a-z0-9-]*$` |
| `vpc_cidr` | `string` | Required | Valid CIDR; caller supplies IPv4 `/16` |
| `availability_zones` | `list(string)` | Required | Exactly two zones, a then b |
| `nat_gateway_count` | `number` | Required | `1` or `2` |

## Outputs

| Output | Meaning |
| --- | --- |
| `vpc_id` | VPC ID |
| `vpc_cidr_block` | VPC CIDR |
| `availability_zones` | Ordered zones |
| `public_subnet_ids` | Public subnet IDs |
| `private_subnet_ids` | Private subnet IDs |
| `isolated_subnet_ids` | Isolated subnet IDs |
| `nat_gateway_ids` | NAT gateway IDs |
| `nat_public_ips` | NAT public IPv4 addresses |

All lists follow input availability-zone order (a then b); lean NAT lists contain only zone a.

## Example

```hcl
module "network" {
  source             = "../../../modules/network"
  name_prefix        = "cms"
  vpc_cidr           = "10.20.0.0/16"
  availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
  nat_gateway_count  = var.nat_gateway_count
}
```

Select `tfvars/lean.tfvars` (1 NAT) or `tfvars/full.tfvars` (2 NATs) in the group root; no `.tf` changes are needed.

## Security

Isolated subnets have no internet route. All subnets disable public IP assignment on launch; the default security group has no ingress or egress rules. Resource tags hold only `Name`; common tags come from provider `default_tags`. No endpoints, NACL changes or flow logs are added. The expected Trivy MEDIUM finding AWS-0178 (no flow logs) is accepted by the plan; IAC-AC11 gates HIGH and CRITICAL.

## Cost

Plan estimates in ap-southeast-1: [NAT gateway](https://aws.amazon.com/vpc/pricing/) about $0.059 per hour per gateway plus $0.005 per hour per public IPv4 address; data processing and transfer are additional. Lean is about $0.064 per hour before traffic; full doubles the gateway/address charge. Group exists only during sessions (Q-O57).

## Teardown

Destroy env first, then group at every session end, using the same profile file: `terraform destroy -var-file=tfvars/lean.tfvars` (or `full.tfvars`). NATs, EIPs and the VPC are removed; singleton stays.

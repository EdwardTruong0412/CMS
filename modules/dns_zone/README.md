# dns_zone

Creates the public DNS zone delegated from Namecheap.

## Purpose

Own the CMS subdomain while leaving the parent domain at Namecheap.

## Layer and callers

Singleton layer; called by `awsenv/dev/singleton`.

## Resources

`aws_route53_zone.this` creates the public hosted zone. No application records are created here.

## Inputs

| Input | Type | Default |
| --- | --- | --- |
| `zone_name` | `string` | Required |

## Outputs

| Output | Meaning |
| --- | --- |
| `zone_id` | Hosted zone ID |
| `zone_name` | Hosted zone name |
| `name_servers` | Four servers for the parent delegation |

## Example

```hcl
module "dns_zone" {
  source    = "../../../modules/dns_zone"
  zone_name = "cms.imaprof.ink"
}
```

## Security

This is a public zone with no DNSSEC in this story. Common tags come from provider `default_tags`. Only `cms` is delegated; parent and other subdomains remain at Namecheap.

## Cost

Plan estimate: [Route 53 hosted zone](https://aws.amazon.com/route53/pricing/) $0.50 per month, plus DNS query charges. Singleton stays active between sessions.

## Teardown

`force_destroy = false` prevents deleting a zone with leftover records. Remove all records except NS and SOA before destroying singleton. The Owner removes the four Namecheap NS records at final teardown (TDN-AC05).

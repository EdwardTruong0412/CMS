resource "aws_route53_zone" "this" {
  name          = var.zone_name
  comment       = "CMS public hosted zone, delegated from Namecheap"
  force_destroy = false
}

output "zone_id" {
  description = "Route 53 hosted zone ID."
  value       = aws_route53_zone.this.zone_id
}

output "zone_name" {
  description = "Public hosted zone name."
  value       = aws_route53_zone.this.name
}

output "name_servers" {
  description = "Four name servers to delegate at Namecheap."
  value       = aws_route53_zone.this.name_servers
}

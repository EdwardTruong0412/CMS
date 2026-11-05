output "ecr_repository_name" {
  description = "API image repository name."
  value       = module.container_registry.repository_name
}

output "ecr_repository_arn" {
  description = "API image repository ARN."
  value       = module.container_registry.repository_arn
}

output "ecr_repository_url" {
  description = "API image repository URL."
  value       = module.container_registry.repository_url
}

output "hosted_zone_id" {
  description = "CMS public hosted zone ID."
  value       = module.dns_zone.zone_id
}

output "hosted_zone_name" {
  description = "CMS public hosted zone name."
  value       = module.dns_zone.zone_name
}

output "hosted_zone_name_servers" {
  description = "Name servers for the CMS delegation at Namecheap."
  value       = module.dns_zone.name_servers
}

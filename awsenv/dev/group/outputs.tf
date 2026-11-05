output "vpc_id" {
  description = "VPC ID."
  value       = module.network.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block."
  value       = module.network.vpc_cidr_block
}

output "availability_zones" {
  description = "Availability zones in zone a then zone b order."
  value       = module.network.availability_zones
}

output "public_subnet_ids" {
  description = "Public subnet IDs in availability zone order."
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs in availability zone order."
  value       = module.network.private_subnet_ids
}

output "isolated_subnet_ids" {
  description = "Isolated subnet IDs in availability zone order."
  value       = module.network.isolated_subnet_ids
}

output "nat_gateway_ids" {
  description = "NAT gateway IDs in availability zone order."
  value       = module.network.nat_gateway_ids
}

output "nat_public_ips" {
  description = "NAT public IPv4 addresses in availability zone order."
  value       = module.network.nat_public_ips
}

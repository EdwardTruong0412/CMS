output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block."
  value       = aws_vpc.this.cidr_block
}

output "availability_zones" {
  description = "Availability zones in zone a then zone b order."
  value       = var.availability_zones
}

output "public_subnet_ids" {
  description = "Public subnet IDs in availability zone order."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs in availability zone order."
  value       = aws_subnet.private[*].id
}

output "isolated_subnet_ids" {
  description = "Isolated subnet IDs in availability zone order."
  value       = aws_subnet.isolated[*].id
}

output "nat_gateway_ids" {
  description = "NAT gateway IDs in availability zone order."
  value       = aws_nat_gateway.this[*].id
}

output "nat_public_ips" {
  description = "NAT public IPv4 addresses in availability zone order."
  value       = aws_eip.nat[*].public_ip
}

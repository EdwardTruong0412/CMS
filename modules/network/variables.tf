variable "name_prefix" {
  type        = string
  description = "Prefix used in network resource Name tags."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name_prefix))
    error_message = "The prefix must start with a lowercase letter and contain lowercase letters, digits or hyphens."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "VPC IPv4 CIDR, split into subnets with eight additional prefix bits."

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "The VPC CIDR must be valid CIDR notation."
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "Exactly two availability zones in output order, zone a then zone b."

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Exactly two availability zones are required."
  }
}

variable "nat_gateway_count" {
  type        = number
  description = "Number of NAT gateways: 1 in the lean profile, 2 in the full profile (one per availability zone)."

  validation {
    condition     = contains([1, 2], var.nat_gateway_count)
    error_message = "The NAT gateway count must be 1 or 2."
  }
}

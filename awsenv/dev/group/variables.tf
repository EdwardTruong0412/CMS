variable "nat_gateway_count" {
  type        = number
  description = "Number of NAT gateways: 1 in the lean profile, 2 in the full profile (one per availability zone)."

  validation {
    condition     = contains([1, 2], var.nat_gateway_count)
    error_message = "The NAT gateway count must be 1 or 2."
  }
}

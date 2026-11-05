variable "repository_name" {
  type        = string
  description = "CMS ECR repository name."

  validation {
    condition     = can(regex("^cms-[a-z0-9-]+$", var.repository_name))
    error_message = "The repository name must start with cms- and contain lowercase letters, digits or hyphens."
  }
}

variable "images_to_keep" {
  type        = number
  description = "Number of most recent images retained by the lifecycle policy."
  default     = 5

  validation {
    condition     = var.images_to_keep >= 1 && floor(var.images_to_keep) == var.images_to_keep
    error_message = "The number of images to keep must be a positive integer."
  }
}

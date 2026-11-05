terraform {
  backend "s3" {
    bucket       = "cms-terraform-state-store"
    key          = "singleton/terraform.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true
    encrypt      = true
  }
}

module "network" {
  source             = "../../../modules/network"
  name_prefix        = "cms"
  vpc_cidr           = "10.20.0.0/16"
  availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
  nat_gateway_count  = var.nat_gateway_count
}

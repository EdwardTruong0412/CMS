module "container_registry" {
  source          = "../../../modules/container_registry"
  repository_name = "cms-api"
}

module "dns_zone" {
  source    = "../../../modules/dns_zone"
  zone_name = "cms.imaprof.ink"
}

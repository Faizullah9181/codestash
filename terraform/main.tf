module "droplet" {
  source = "./modules/droplet"
  count  = var.create_droplet ? 1 : 0

  name        = var.droplet_name
  region      = var.droplet_region
  size        = var.droplet_size
  image       = var.droplet_image
  ssh_key_ids = var.ssh_key_ids
  tags        = ["codestash"]
}

module "firewall" {
  source = "./modules/firewall"
  count  = var.create_firewall && var.create_droplet ? 1 : 0

  name            = "${var.droplet_name}-fw"
  droplet_ids     = [module.droplet[0].id]
  ssh_allowed_ips = var.ssh_allowed_ips
}

locals {
  droplet_urn = var.create_droplet ? module.droplet[0].urn : "do:droplet:${var.droplet_id}"
  resources   = distinct(concat([local.droplet_urn], var.additional_resource_urns))
}

module "project" {
  source = "./modules/project"

  name        = var.project_name
  description = var.project_description
  purpose     = var.project_purpose
  environment = var.project_environment
  resources   = local.resources
}

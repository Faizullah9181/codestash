resource "digitalocean_droplet" "this" {
  name     = var.name
  region   = var.region
  size     = var.size
  image    = var.image
  ssh_keys = var.ssh_key_ids
  tags     = var.tags

  monitoring = true
  ipv6       = true
}

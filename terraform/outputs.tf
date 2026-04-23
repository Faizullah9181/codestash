output "droplet_id" {
  value       = var.create_droplet ? module.droplet[0].id : var.droplet_id
  description = "Droplet ID"
}

output "droplet_ipv4" {
  value       = var.create_droplet ? module.droplet[0].ipv4_address : null
  description = "Droplet IPv4"
}

output "firewall_id" {
  value       = var.create_firewall && var.create_droplet ? module.firewall[0].id : null
  description = "Firewall ID"
}

output "project_id" {
  value       = module.project.project_id
  description = "Project ID"
}

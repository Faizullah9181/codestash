variable "digitalocean_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "create_droplet" {
  description = "Create new droplet"
  type        = bool
  default     = false
}

variable "droplet_id" {
  description = "Existing droplet ID when create_droplet is false"
  type        = number
  default     = 0
}

variable "droplet_name" {
  description = "Droplet hostname"
  type        = string
  default     = "codestash-node"
}

variable "droplet_region" {
  description = "DO region"
  type        = string
  default     = "blr1"
}

variable "droplet_size" {
  description = "DO size slug"
  type        = string
  default     = "s-2vcpu-2gb"
}

variable "droplet_image" {
  description = "Droplet image"
  type        = string
  default     = "ubuntu-24-04-x64"
}

variable "ssh_key_ids" {
  description = "SSH key IDs"
  type        = list(string)
  default     = []
}

variable "create_firewall" {
  description = "Create firewall"
  type        = bool
  default     = true
}

variable "ssh_allowed_ips" {
  description = "SSH allow list"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "CodeStash"
}

variable "project_description" {
  description = "Project description"
  type        = string
  default     = "Generic full-stack starter"
}

variable "project_purpose" {
  description = "Project purpose"
  type        = string
  default     = "Web Application"
}

variable "project_environment" {
  description = "Project environment"
  type        = string
  default     = "Development"
}

variable "additional_resource_urns" {
  description = "Additional resource URNs"
  type        = list(string)
  default     = []
}

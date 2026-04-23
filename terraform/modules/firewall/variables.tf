variable "name" {
  type = string
}

variable "droplet_ids" {
  type    = list(number)
  default = []
}

variable "ssh_allowed_ips" {
  type    = list(string)
  default = ["0.0.0.0/0", "::/0"]
}

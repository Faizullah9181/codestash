variable "name" {
  type = string
}

variable "region" {
  type = string
}

variable "size" {
  type = string
}

variable "image" {
  type = string
}

variable "ssh_key_ids" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = list(string)
  default = []
}

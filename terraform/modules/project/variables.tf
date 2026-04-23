variable "name" {
  type = string
}

variable "description" {
  type = string
}

variable "purpose" {
  type = string
}

variable "environment" {
  type = string
}

variable "resources" {
  type    = list(string)
  default = []
}

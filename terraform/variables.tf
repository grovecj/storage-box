variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "ssh_key_name" {
  description = "Name of the SSH key in DigitalOcean"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Droplet size slug"
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "db_size" {
  description = "Database cluster size slug"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "domain" {
  description = "Domain name managed by DigitalOcean (leave empty to skip DNS)"
  type        = string
  default     = ""
}

variable "subdomain" {
  description = "Subdomain for the app"
  type        = string
  default     = "boxes"
}

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc"
}

variable "github_repo" {
  description = "GitHub repository (owner/repo format)"
  type        = string
  default     = "grovecj/storage-box"
}

variable "github_branch" {
  description = "GitHub branch to deploy"
  type        = string
  default     = "main"
}

variable "instance_size" {
  description = "App Platform instance size"
  type        = string
  default     = "basic-xxs"
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 1
}

variable "database_cluster_name" {
  description = "Name of the existing managed PostgreSQL cluster"
  type        = string
  default     = "mlb-stats-db"
}

variable "custom_domain" {
  description = "Custom domain (e.g., boxes.cartergrove.me)"
  type        = string
  default     = ""
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

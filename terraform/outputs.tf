output "app_url" {
  description = "The URL of the deployed application"
  value       = digitalocean_app.storage_box.live_url
}

output "app_id" {
  description = "The App Platform application ID (add to mlb-stats additional_trusted_sources)"
  value       = digitalocean_app.storage_box.id
}

output "default_hostname" {
  description = "Default DO hostname for CNAME record"
  value       = replace(digitalocean_app.storage_box.default_ingress, "https://", "")
}

output "database_name" {
  description = "Database name on the shared cluster"
  value       = digitalocean_database_db.storagebox.name
}

output "database_user" {
  description = "Database user on the shared cluster"
  value       = digitalocean_database_user.storagebox.name
}

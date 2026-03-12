output "app_ip" {
  description = "Public IP of the application droplet"
  value       = digitalocean_droplet.app.ipv4_address
}

output "db_host" {
  description = "Database host"
  value       = digitalocean_database_cluster.db.host
}

output "db_port" {
  description = "Database port"
  value       = digitalocean_database_cluster.db.port
}

output "db_uri" {
  description = "Database connection URI"
  value       = digitalocean_database_cluster.db.uri
  sensitive   = true
}

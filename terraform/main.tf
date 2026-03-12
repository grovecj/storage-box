terraform {
  required_version = ">= 1.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.34"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# Look up the existing managed PostgreSQL cluster (owned by mlb-stats)
data "digitalocean_database_cluster" "postgres" {
  name = var.database_cluster_name
}

# Create a dedicated database for storage-box on the shared cluster
resource "digitalocean_database_db" "storagebox" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "storagebox"
}

# Create a dedicated user for storage-box
resource "digitalocean_database_user" "storagebox" {
  cluster_id = data.digitalocean_database_cluster.postgres.id
  name       = "storagebox"
}

# App Platform Application
resource "digitalocean_app" "storage_box" {
  spec {
    name   = "storage-box"
    region = var.region

    # Custom domain
    dynamic "domain" {
      for_each = var.custom_domain != "" ? [var.custom_domain] : []
      content {
        name = domain.value
        type = "PRIMARY"
      }
    }

    alert {
      rule = "DEPLOYMENT_FAILED"
    }

    service {
      name               = "web"
      instance_count     = var.instance_count
      instance_size_slug = var.instance_size
      http_port          = 8080

      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = true
      }

      dockerfile_path = "Dockerfile"

      health_check {
        http_path             = "/api/v1/health"
        initial_delay_seconds = 30
        period_seconds        = 30
        timeout_seconds       = 10
        failure_threshold     = 3
      }

      env {
        key   = "DATABASE_URL"
        value = "postgresql+asyncpg://${digitalocean_database_user.storagebox.name}:${urlencode(digitalocean_database_user.storagebox.password)}@${data.digitalocean_database_cluster.postgres.host}:${data.digitalocean_database_cluster.postgres.port}/${digitalocean_database_db.storagebox.name}"
        type  = "SECRET"
      }

      env {
        key   = "APP_BASE_URL"
        value = var.custom_domain != "" ? "https://${var.custom_domain}" : ""
        type  = "GENERAL"
      }

      env {
        key   = "APP_ENV"
        value = "production"
        type  = "GENERAL"
      }

      env {
        key   = "SECRET_KEY"
        value = var.secret_key
        type  = "SECRET"
      }
    }
  }
}

# DNS Record for custom subdomain
resource "digitalocean_record" "app_cname" {
  count  = var.custom_domain != "" ? 1 : 0
  domain = join(".", slice(split(".", var.custom_domain), 1, length(split(".", var.custom_domain))))
  type   = "CNAME"
  name   = split(".", var.custom_domain)[0]
  value  = "${replace(digitalocean_app.storage_box.default_ingress, "https://", "")}."
  ttl    = 3600
}

terraform {
  required_version = ">= 1.5"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.36"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# SSH Key
data "digitalocean_ssh_key" "main" {
  name = var.ssh_key_name
}

# Droplet for the application
resource "digitalocean_droplet" "app" {
  image    = "ubuntu-24-04-x64"
  name     = "storage-box"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [data.digitalocean_ssh_key.main.id]

  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx
    systemctl enable docker
    systemctl start docker
  EOF

  tags = ["storage-box"]
}

# Managed PostgreSQL Database
resource "digitalocean_database_cluster" "db" {
  name       = "storage-box-db"
  engine     = "pg"
  version    = "16"
  size       = var.db_size
  region     = var.region
  node_count = 1
}

# Firewall
resource "digitalocean_firewall" "app" {
  name        = "storage-box-fw"
  droplet_ids = [digitalocean_droplet.app.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# DNS Record (optional - requires domain managed by DO)
resource "digitalocean_record" "app" {
  count  = var.domain != "" ? 1 : 0
  domain = var.domain
  type   = "A"
  name   = var.subdomain
  value  = digitalocean_droplet.app.ipv4_address
  ttl    = 300
}

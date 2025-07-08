# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Get project information to access the project number
data "google_project" "project" {
  project_id = var.dev_project_id
}

# VPC Network for AlloyDB
resource "google_compute_network" "default" {
  name                    = "${var.project_name}-alloydb-network"
  project                 = var.dev_project_id
  auto_create_subnetworks = false
  depends_on = [resource.google_project_service.services]
}

# Subnet for AlloyDB
resource "google_compute_subnetwork" "default" {
  name          = "${var.project_name}-alloydb-network"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.default.id
  project       = var.dev_project_id

  # This is required for Cloud Run VPC connectors
  purpose       = "PRIVATE"

  private_ip_google_access = true
}

# Private IP allocation for AlloyDB
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "${var.project_name}-private-ip"
  project       = var.dev_project_id
  address_type  = "INTERNAL"
  purpose       = "VPC_PEERING"
  prefix_length = 16
  network       = google_compute_network.default.id

  depends_on = [resource.google_project_service.services]
}

# VPC connection for AlloyDB
resource "google_service_networking_connection" "vpc_connection" {
  network                 = google_compute_network.default.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# AlloyDB Cluster
resource "google_alloydb_cluster" "session_db_cluster" {
  project    = var.dev_project_id
  cluster_id = "${var.project_name}-alloydb-cluster"
  location   = var.region

  network_config {
    network = google_compute_network.default.id
  }

  depends_on = [
    google_service_networking_connection.vpc_connection
  ]
}

# AlloyDB Instance
resource "google_alloydb_instance" "session_db_instance" {
  cluster       = google_alloydb_cluster.session_db_cluster.name
  instance_id   = "${var.project_name}-alloydb-instance"
  instance_type = "PRIMARY"

  availability_type = "REGIONAL" # Regional redundancy

  machine_config {
    cpu_count = 2
  }
}

# Generate a random password for the database user
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store the password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  project   = var.dev_project_id
  secret_id = "${var.project_name}-db-password"

  replication {
    auto {}
  }

  depends_on = [resource.google_project_service.services]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_alloydb_user" "db_user" {
  cluster        = google_alloydb_cluster.session_db_cluster.name
  user_id        = "postgres"
  user_type      = "ALLOYDB_BUILT_IN"
  password       = random_password.db_password.result
  database_roles = ["alloydbsuperuser"]

  depends_on = [google_alloydb_instance.session_db_instance]
}


resource "google_cloud_run_v2_service" "app" {
  name                = var.project_name
  location            = var.region
  project             = var.dev_project_id
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }

      env {
        name  = "DB_HOST"
        value = google_alloydb_instance.session_db_instance.ip_address
      }

      env {
        name = "DB_PASS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password.secret_id
            version = "latest"
          }
        }
      }
    }

    service_account = google_service_account.cloud_run_app_sa.email
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    session_affinity = true
    # VPC access for AlloyDB connectivity
    vpc_access {
      network_interfaces {
        network    = google_compute_network.default.id
        subnetwork = google_compute_subnetwork.default.id
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # This lifecycle block prevents Terraform from overwriting the container image when it's
  # updated by Cloud Run deployments outside of Terraform (e.g., via CI/CD pipelines)
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }

  # Make dependencies conditional to avoid errors.
  depends_on = [resource.google_project_service.services]
}

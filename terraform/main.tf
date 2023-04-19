terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
  credentials = file(var.credentials)  # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

# Data Lake Bucket
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}_${var.project}" # Concatenating DL bucket & Project name for unique naming
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  # days
    }
  }

  force_destroy = true
}

# DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
  project    = var.project
  location   = var.region
}

#VM Instance
resource "google_compute_instance" "reviews-instance" {
  name         = "reviews-instance"
  machine_type = "e2-standard-4"
  zone = "us-east1-b" # note: zone, not region
  
  tags = ["amz"] # for ease of identification later

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts" # project/family
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network = "default"
    
    access_config {
      # Ephemeral IP
    }
  }

  metadata = {
    # startup_script = "${file(var.bootstrap_script)}" #unable to get this going for now
    ssh-keys = "mherr:${file(var.ssh_public_key)}"  #username from keygen
  }
  
  service_account {
    email = "reviews-user@amazon-reviews-365312.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }
}
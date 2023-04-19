locals {
  data_lake_bucket = "amzproject"
}

variable "project" {
  description = "GCP Project ID"
  default = "amazon-reviews-365312" #remove for repo
  type = string
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default = "us-east1"
  type = string
}

variable "credentials"{
  description = "location of GCP credentials token"
  default = "~/.google/credentials/google-credentials.json"
}

variable "ssh_public_key"{
  description = "filepath for ssh public key"
  type = string
  default = "~/.ssh/gcp.pub"
}

variable "bootstrap_script"{
  description = "location of bootstrap script"
  type = string
  default = "startup.sh"
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  //**remove for repo**
  type = string
  default = "amazon_reviews"
}



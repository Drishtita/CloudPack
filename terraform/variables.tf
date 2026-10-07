variable "aws_region" {
  description = "AWS region for CloudPack infrastructure"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloudpack"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "demo"
}

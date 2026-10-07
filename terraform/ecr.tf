locals {
  services = [
    "agent-service",
    "weather-service",
    "memory-service",
    "api-gateway"
  ]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = "${var.project_name}-${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Service = each.value
  }
}
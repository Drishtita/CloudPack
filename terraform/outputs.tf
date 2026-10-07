output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.cloudpack.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.cloudpack.endpoint
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value = {
    for service, repository in aws_ecr_repository.services :
    service => repository.repository_url
  }
}

output "vpc_id" {
  description = "CloudPack VPC ID"
  value       = aws_vpc.cloudpack.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}
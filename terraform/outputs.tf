output "repository_url" {
    description = "The URL of the repository"
    value = module.ecr.repository_url
}

output "repository_arn" {
    description = "The ARN of the repository"
    value = module.ecr.repository_arn
}

output "vpc_id" {
    description = "The ID of the VPC"
    value = module.vpc.vpc_id
}

output "private_subnets" {
    description = "List of IDs of the private subnets"
    value = module.vpc.private_subnets
}

output "public_subnets" {
    description = "List of IDs of the public subnets"
    value = module.vpc.public_subnets
}

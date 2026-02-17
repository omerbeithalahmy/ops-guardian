module "ecr" {
    source = "terraform-aws-modules/ecr/aws"
    version = "~> 1.6.0"
    
    repository_name = var.repo_name

    repository_lifecycle_policy = jsonencode({
        rules = [
            {
                rulePriority = 1
                description = "Keep last 10 images"
                selection = {
                    tagStatus = "any"
                    countType = "imageCountMoreThan"
                    countNumber = 10
                }
                action = {
                    type = "expire"
                }
            }
        ]
    })

    repository_force_delete = true

    tags = {
        Terraform = "true"
        Environment = "dev"
        Project = "opsguardian"
    }
}

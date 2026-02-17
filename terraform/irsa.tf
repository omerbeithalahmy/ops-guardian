module "opsguardian_irsa_role" {
    source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
    version = "~> 5.0"

    role_name = "opsguardian-role"

    role_policy_arns = {
        policy = aws_iam_policy.opsguardian_policy.arn
    }

    oidc_providers = {
        main = {
            provider_arn = module.eks.oidc_provider_arn
            namespace_service_accounts = ["default:opsguardian-sa"]
        }
    }
}


resource "aws_iam_policy" "opsguardian_policy" {
  name        = "OpsGuardianPolicy"
  description = "Read-only permissions for OpsGuardian to scan AWS resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EC2Remediation"
        Effect = "Allow"
        Action = [
          "ec2:DeleteVolume",
          "ec2:ReleaseAddress",
          "ec2:TerminateInstances",
          "ec2:DeleteSecurityGroup",
          "ec2:DeleteVpc",
          "ec2:DescribeVolumes",
          "ec2:DescribeAddresses",
          "ec2:DescribeInstances",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSecurityGroupRules",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets"
        ]
        Resource = "*"
      },
      {
        Sid    = "S3Remediation"
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetBucketAcl",
          "s3:GetBucketVersioning",
          "s3:DeleteBucket"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAMRemediation"
        Effect = "Allow"
        Action = [
          "iam:ListUsers",
          "iam:ListMFADevices",
          "iam:DeleteUser"
        ]
        Resource = "*"
      },
      {
        Sid    = "SecretsManagerReadOnly"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:opsguardian/*"
      }
    ]
  })
}

module "opsguardian_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "opsguardian-role"

  role_policy_arns = {
    policy = aws_iam_policy.opsguardian_policy.arn
  }

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["default:opsguardian-sa"]
    }
  }
}

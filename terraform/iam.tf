data "aws_caller_identity" "current" {}

resource "aws_iam_role" "github_actions" {
    name = "github-actions-opsguardian-role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub": "repo:${var.github_repo}:*"
          }
          StringEquals = {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
          }
        }
      }
    ]
    })
}

resource "aws_iam_role_policy" "github_actions_ecr" {
    name = "github-actions-ecr-policy"
    role = aws_iam_role.github_actions.id

    policy = jsonencode({
        Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = "*" 
      }
    ]
    })
}
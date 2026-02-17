resource "aws_iam_policy" "opsguardian_policy" {
    name = "OpsGuardianPolicy"
    description = "Permission for OpsGuardian bot to manage EBS volumes and Security Groups"

    policy = jsonencode({
        Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ManageVolumes"
        Effect = "Allow"
        Action = [
          "ec2:DescribeVolumes",
          "ec2:DeleteVolume"
        ]
        Resource = "*"
      },
      {
        Sid    = "ScanSecurityGroups"
        Effect = "Allow"
        Action = [
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSecurityGroupRules"
        ]
        Resource = "*"
      }
    ]
    })
}
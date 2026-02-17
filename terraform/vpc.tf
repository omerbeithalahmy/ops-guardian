data "aws_availability_zone" "available" {}

module "vpc" {
    source = "terraform-aws-modules/vpc/aws"
    version = "~> 5.0"

    name = var.vpc_name
    cidr = var.vpc_cidr
    azs = slice(data.aws_availability_zone.available, 0, 2)
    private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
    public_subnets = ["10.0.101.0/24", "10.0.102.0/24"]
    enable_nat_gateway = true
    single_nat_gateway = true
    enable_dns_hostnames = true
    public_subnet_tags = {
        "kubernetes.io/role/elb" = 1
    }
    private_subnet_tags = {
        "kubernetes.io/role/internal-elb" = 1
    }

    tags = {
        Terraform = "true"
        Environmet = "dev"
        Project = "opsguardian"
    }
}
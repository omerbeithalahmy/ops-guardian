variable "region" {
    description = "AWS region"
    type = string
    default = "us-east-1"
}

variable "repo_name" {
    description = "Name of the ECR repository"
    type = string
    default = "opsguardian"
}

variable "vpc_name" {
    description = "Name of the VPC"
    type = string
    default = "opsguardian-vpc"
}

variable "vpc_cidr" {
    description = "CIDR block for the VPC"
    type = string
    default = "10.0.0.0/16"
}

variable "cluster_name" {
    description = "Name of the EKS cluster"
    type = string
    default = "opsguardian-cluster"
}
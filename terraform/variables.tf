# The AWS region where your infrastructure will be deployed
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

# The instance type must be t2.micro to stay within the Free Tier [cite: 12]
variable "instance_type" {
  description = "EC2 instance type for the K3s node"
  type        = string
  default     = "t2.micro" 
}

# This is the name of the key pair you created in the AWS Console
variable "key_name" {
  description = "Name of the existing AWS Key Pair for SSH access"
  type        = string
}

# Tagging helps with project organization and documentation [cite: 18]
variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "Cloud-Computing-Coursework"
}
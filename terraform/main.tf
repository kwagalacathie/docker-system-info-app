# Configure the AWS Provider
provider "aws" {
  region = "us-east-1" 
}

# Security Group to allow Web, SSH, and K3s traffic
resource "aws_security_group" "k3s_sg" {
  name        = "k3s-security-group"
  description = "Allow inbound traffic for Flask and K3s"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SSH Access
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Your Flask App port
  }

  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # K3s API Server
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance (t2.micro for Free Tier)
resource "aws_instance" "devops_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS (Verify for your region)
  instance_type = "t2.micro"              # Required for Free Tier [cite: 12, 13]
  key_name      = "your-key-pair"         # Replace with your AWS key pair name

  vpc_security_group_ids = [aws_security_group.k3s_sg.id]

  tags = {
    Name = "K3s-DevOps-Server"
  }

  # Script to install K3s automatically on boot
  user_data = <<-EOF
              #!/bin/bash
              curl -sfL https://get.k3s.io | sh -
              EOF
}
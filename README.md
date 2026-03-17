# Docker System Info App - AWS ECS Deployment Guide

A containerized web application that displays Docker container and system information, designed to run on AWS ECS (Fargate).

## 📋 Application Overview

This Flask-based web application displays:
- Container/Host information
- CPU and Memory metrics
- Disk usage
- System architecture details
- Real-time statistics

## 🏗️ Architecture

- **Application**: Python Flask web server
- **Container**: Docker
- **Container Registry**: Amazon ECR
- **Orchestration**: Amazon ECS (Fargate)

## 🚀 Step-by-Step Deployment Guide

### Prerequisites

1. AWS Account with appropriate permissions
2. Docker installed locally
3. AWS CLI installed and configured
4. Git (optional)

### Step 1: Build Docker Container Locally

```bash
# Navigate to project directory
cd /path/to/docker-system-info-app

# Build the Docker image
docker build -t docker-system-info-app .

# Verify the image was created
docker images | grep docker-system-info-app

# Test locally (optional)
docker run -p 5000:5000 docker-system-info-app

# Access at http://localhost:5000
```

### Step 2: Push Container Image to Amazon ECR

```bash
# Set variables (replace with your values)
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="123456789012"
REPOSITORY_NAME="docker-system-info-app"

# Create ECR repository
aws ecr create-repository \
    --repository-name $REPOSITORY_NAME \
    --region $AWS_REGION

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS \
    --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag the image
docker tag docker-system-info-app:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:latest
```

### Step 3: Run Container on Amazon ECS (Fargate)

#### Option A: Using AWS Console

1. **Create ECS Cluster**
   - Go to AWS ECS Console
   - Click "Create Cluster"
   - Select "Networking only" (Fargate)
   - Name: `docker-app-cluster`
   - Create cluster

2. **Create Task Definition**
   - Go to "Task Definitions" → "Create new Task Definition"
   - Select "Fargate"
   - Task Definition Name: `docker-system-info-task`
   - Task Role: Create new role or use existing
   - Task execution role: ecsTaskExecutionRole
   - Task memory: 512 MB (0.5 GB)
   - Task CPU: 256 (.25 vCPU)
   - Add Container:
     - Container name: `docker-system-info-container`
     - Image: `<your-ecr-image-uri>:latest`
     - Port mappings: 5000 (tcp)
     - Health check: `/health`
   - Create

3. **Create Service**
   - Go to your cluster
   - Click "Create" under Services
   - Launch type: Fargate
   - Task Definition: Select your task definition
   - Service name: `docker-system-info-service`
   - Number of tasks: 1
   - Configure network:
     - VPC: Select your VPC
     - Subnets: Select public subnets
     - Security group: Allow inbound on port 5000
     - Auto-assign public IP: ENABLED
   - Create service

#### Option B: Using AWS CLI

```bash
# Create ECS cluster
aws ecs create-cluster \
    --cluster-name docker-app-cluster \
    --region $AWS_REGION

# Register task definition (requires JSON file - see task-definition.json)
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region $AWS_REGION

# Create service
aws ecs create-service \
    --cluster docker-app-cluster \
    --service-name docker-system-info-service \
    --task-definition docker-system-info-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --region $AWS_REGION
```

### Step 4: Access the Running Application

1. Go to ECS Console → Clusters → Your cluster → Service
2. Click on the running task
3. Find the Public IP address
4. Access the application at: `http://<public-ip>:5000`

## 🔧 Configuration

### Environment Variables

You can customize the application by setting environment variables in your ECS task definition:

- `ENVIRONMENT`: Custom environment name (default: "AWS ECS Container")

### Security Group Configuration

Ensure your security group allows:
- Inbound: TCP port 5000 from your IP or 0.0.0.0/0
- Outbound: All traffic

## 📊 Monitoring

### Health Check Endpoint

The application includes a health check endpoint at `/health`

```bash
curl http://<public-ip>:5000/health
```

### CloudWatch Logs

ECS automatically sends logs to CloudWatch. View them at:
- CloudWatch → Log Groups → `/ecs/docker-system-info-task`

## 🛠️ Troubleshooting

### Container won't start
- Check CloudWatch logs
- Verify security group allows port 5000
- Ensure task has public IP assigned
- Check task execution role permissions

### Can't access application
- Verify security group inbound rules
- Check task is in RUNNING state
- Confirm public IP is accessible
- Test health endpoint: `curl http://<public-ip>:5000/health`

### Image pull errors
- Verify ECR authentication
- Check task execution role has ECR permissions
- Confirm image URI is correct

## 📝 File Structure

```
docker-system-info-app/
├── app.py                  # Flask application
├── templates/
│   └── index.html         # HTML template
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── .dockerignore         # Docker ignore rules
└── README.md            # This file
```

## 🔄 Updates and Redeployment

To update the application:

```bash
# 1. Build new image
docker build -t docker-system-info-app:v2 .

# 2. Tag and push to ECR
docker tag docker-system-info-app:v2 \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:v2
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:v2

# 3. Update task definition with new image version
# 4. Update ECS service to use new task definition
aws ecs update-service \
    --cluster docker-app-cluster \
    --service docker-system-info-service \
    --force-new-deployment \
    --region $AWS_REGION
```

## 🧹 Cleanup

To avoid AWS charges:

```bash
# Delete ECS service
aws ecs delete-service \
    --cluster docker-app-cluster \
    --service docker-system-info-service \
    --force \
    --region $AWS_REGION

# Delete cluster
aws ecs delete-cluster \
    --cluster docker-app-cluster \
    --region $AWS_REGION

# Delete ECR repository
aws ecr delete-repository \
    --repository-name $REPOSITORY_NAME \
    --force \
    --region $AWS_REGION
```

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)

## 💡 Tips

1. Use specific image tags instead of `latest` in production
2. Set up Application Load Balancer for better availability
3. Configure auto-scaling for production workloads
4. Use AWS Secrets Manager for sensitive data
5. Implement proper logging and monitoring

## 📄 License

This is a demonstration project for educational purposes.
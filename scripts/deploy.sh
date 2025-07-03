#!/bin/bash
# AWS deployment script

# Check if environment variables are set
if [ -z "$AWS_ACCOUNT_ID" ] || [ -z "$AWS_REGION" ] || [ -z "$EC2_INSTANCE_ID" ]; then
  echo "Error: Required environment variables not set."
  echo "Please set AWS_ACCOUNT_ID, AWS_REGION, and EC2_INSTANCE_ID."
  exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t meetup-bot .

# Tag the image for ECR
echo "Tagging image for ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag meetup-bot:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/meetup-bot:latest

# Push to ECR
echo "Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/meetup-bot:latest

# Update EC2 instance (using SSM Run Command)
echo "Updating EC2 instance..."
aws ssm send-command \
    --document-name "AWS-RunShellScript" \
    --targets "Key=instanceids,Values=$EC2_INSTANCE_ID" \
    --parameters "commands=['cd /home/ec2-user && ./update_container.sh']"

echo "Deployment complete!"

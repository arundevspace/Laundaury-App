# AWS Deployment Guide — Laundry Management System

> Hand this document to your cloud engineer.  
> All commands are run from the repo root unless noted.

---

## Architecture Overview

```
Internet
   │
   ▼
[Route 53] ──► [ACM Certificate]
   │
   ▼
[Application Load Balancer]  (public subnet, port 443 / 80)
   │
   ▼
[ECS Fargate Service]        (private subnet, port 80)
   │ Flask API (Gunicorn 4 workers)
   │
   ├──► [RDS PostgreSQL 15]  (private subnet, port 5432)
   ├──► [ElastiCache Redis]  (private subnet, port 6379) ← Phase 2
   └──► [Secrets Manager]    (environment variables)
         [CloudWatch Logs]   (log group: /ecs/laundry-api)
         [ECR]               (Docker image registry)
```

### AWS Services Used

| Service | Purpose |
|---|---|
| **ECR** | Private Docker image registry |
| **ECS Fargate** | Serverless container hosting (no EC2 to manage) |
| **RDS PostgreSQL 15** | Managed database |
| **Application Load Balancer** | HTTPS termination + routing |
| **Secrets Manager** | Secure env var storage |
| **ACM** | Free SSL/TLS certificate |
| **CloudWatch** | Container logs + alarms |
| **VPC** | Network isolation |

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| AWS CLI | ≥ 2.x | `brew install awscli` |
| Docker | ≥ 24.x | https://docs.docker.com/get-docker |
| Terraform | ≥ 1.7 | `brew install terraform` *(optional, for IaC)* |

```bash
aws configure          # set Access Key, Secret, region (e.g. ap-south-1)
aws sts get-caller-identity   # verify login
```

---

## Step 1 — Create ECR Repository

```bash
REGION=ap-south-1          # Mumbai (change if needed)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME=laundry-api

aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true

# Login Docker to ECR
aws ecr get-login-password --region $REGION \
  | docker login --username AWS \
    --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

---

## Step 2 — Build & Push Docker Image

```bash
cd backend/

IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

docker build -t $REPO_NAME .
docker tag $REPO_NAME:latest $IMAGE_URI
docker push $IMAGE_URI

echo "Image URI: $IMAGE_URI"
```

The existing `backend/Dockerfile` is production-ready (Python 3.10-slim + Gunicorn).

---

## Step 3 — Create VPC & Networking

Use the AWS Console **or** run these CLI commands:

```bash
# VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Public subnets (for ALB)
PUB_SUB_1=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 --availability-zone ${REGION}a \
  --query 'Subnet.SubnetId' --output text)
PUB_SUB_2=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 --availability-zone ${REGION}b \
  --query 'Subnet.SubnetId' --output text)

# Private subnets (for ECS + RDS)
PRIV_SUB_1=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 --availability-zone ${REGION}a \
  --query 'Subnet.SubnetId' --output text)
PRIV_SUB_2=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 --availability-zone ${REGION}b \
  --query 'Subnet.SubnetId' --output text)

# Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
```

---

## Step 4 — Create RDS PostgreSQL Database

```bash
# Security group — allow 5432 from ECS private subnet only
RDS_SG=$(aws ec2 create-security-group \
  --group-name laundry-rds-sg \
  --description "Laundry RDS" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp --port 5432 \
  --cidr 10.0.11.0/24
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp --port 5432 \
  --cidr 10.0.12.0/24

# Subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name laundry-db-subnet \
  --db-subnet-group-description "Laundry DB subnet" \
  --subnet-ids $PRIV_SUB_1 $PRIV_SUB_2

# RDS instance (db.t3.micro for dev, db.t3.small+ for prod)
aws rds create-db-instance \
  --db-instance-identifier laundry-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username laundry_user \
  --master-user-password "CHANGE_THIS_PASSWORD" \
  --db-name laundry_db \
  --allocated-storage 20 \
  --storage-type gp3 \
  --no-publicly-accessible \
  --vpc-security-group-ids $RDS_SG \
  --db-subnet-group-name laundry-db-subnet \
  --backup-retention-period 7 \
  --deletion-protection

# Wait for RDS to be available (~5 min)
aws rds wait db-instance-available --db-instance-identifier laundry-db

# Get the endpoint
RDS_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier laundry-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)
echo "DB Host: $RDS_HOST"
```

---

## Step 5 — Store Secrets in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name laundry/prod \
  --secret-string '{
    "DATABASE_URL": "postgresql://laundry_user:CHANGE_THIS_PASSWORD@'"$RDS_HOST"':5432/laundry_db",
    "JWT_SECRET_KEY": "GENERATE_A_STRONG_RANDOM_KEY_HERE",
    "SECRET_KEY": "GENERATE_ANOTHER_STRONG_KEY_HERE",
    "FLASK_ENV": "production",
    "DEBUG": "false"
  }'
```

> **Tip:** Generate strong keys with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

---

## Step 6 — Create ECS Cluster & Task Definition

### 6a. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name laundry-cluster
```

### 6b. IAM Role for Task Execution

```bash
# Trust policy
cat > /tmp/ecs-trust.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
  --role-name laundry-ecs-execution-role \
  --assume-role-policy-document file:///tmp/ecs-trust.json

aws iam attach-role-policy \
  --role-name laundry-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Add Secrets Manager read permission
aws iam attach-role-policy \
  --role-name laundry-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

### 6c. Task Definition

Create `infra/task-definition.json`:

```json
{
  "family": "laundry-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/laundry-ecs-execution-role",
  "taskRoleArn":      "arn:aws:iam::ACCOUNT_ID:role/laundry-ecs-execution-role",
  "containerDefinitions": [
    {
      "name": "laundry-api",
      "image": "ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/laundry-api:latest",
      "portMappings": [{"containerPort": 80, "protocol": "tcp"}],
      "essential": true,
      "secrets": [
        {"name": "DATABASE_URL",  "valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:laundry/prod:DATABASE_URL::"},
        {"name": "JWT_SECRET_KEY","valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:laundry/prod:JWT_SECRET_KEY::"},
        {"name": "SECRET_KEY",    "valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:laundry/prod:SECRET_KEY::"},
        {"name": "FLASK_ENV",     "valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:laundry/prod:FLASK_ENV::"},
        {"name": "DEBUG",         "valueFrom": "arn:aws:secretsmanager:ap-south-1:ACCOUNT_ID:secret:laundry/prod:DEBUG::"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group":         "/ecs/laundry-api",
          "awslogs-region":        "ap-south-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:80/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

```bash
# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/laundry-api

# Register task definition (replace ACCOUNT_ID in the file first)
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" infra/task-definition.json

aws ecs register-task-definition \
  --cli-input-json file://infra/task-definition.json
```

---

## Step 7 — Create Application Load Balancer

```bash
# Security group for ALB
ALB_SG=$(aws ec2 create-security-group \
  --group-name laundry-alb-sg \
  --description "Laundry ALB" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress --group-id $ALB_SG \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG \
  --protocol tcp --port 80  --cidr 0.0.0.0/0

# ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name laundry-alb \
  --subnets $PUB_SUB_1 $PUB_SUB_2 \
  --security-groups $ALB_SG \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Target group
TG_ARN=$(aws elbv2 create-target-group \
  --name laundry-api-tg \
  --protocol HTTP --port 80 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# HTTP listener (redirects to HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP --port 80 \
  --default-actions '[{"Type":"redirect","RedirectConfig":{"Protocol":"HTTPS","Port":"443","StatusCode":"HTTP_301"}}]'

# HTTPS listener (needs ACM cert — see Step 7a)
# aws elbv2 create-listener \
#   --load-balancer-arn $ALB_ARN \
#   --protocol HTTPS --port 443 \
#   --certificates CertificateArn=arn:aws:acm:... \
#   --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### 7a. SSL Certificate (ACM)

```bash
# Request cert (validate via DNS — add the CNAME record to Route 53)
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS \
  --region ap-south-1
```

---

## Step 8 — Create ECS Service

```bash
# Security group for ECS tasks
ECS_SG=$(aws ec2 create-security-group \
  --group-name laundry-ecs-sg \
  --description "Laundry ECS" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Allow ALB to reach ECS on port 80
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG \
  --protocol tcp --port 80 \
  --source-group $ALB_SG

# ECS Service
aws ecs create-service \
  --cluster laundry-cluster \
  --service-name laundry-api \
  --task-definition laundry-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$PRIV_SUB_1,$PRIV_SUB_2],
    securityGroups=[$ECS_SG],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=laundry-api,containerPort=80" \
  --health-check-grace-period-seconds 60
```

---

## Step 9 — Run Database Migrations

Run migrations **once** using a one-off ECS task (not the service):

```bash
aws ecs run-task \
  --cluster laundry-cluster \
  --task-definition laundry-api \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$PRIV_SUB_1],
    securityGroups=[$ECS_SG],
    assignPublicIp=DISABLED
  }" \
  --overrides '{
    "containerOverrides": [{
      "name": "laundry-api",
      "command": ["flask", "db", "upgrade"]
    }]
  }'
```

> **Important:** Run this after every deployment that includes model changes.

---

## Step 10 — Auto-Scaling (Optional but Recommended)

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/laundry-cluster/laundry-api \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Scale when CPU > 60%
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/laundry-cluster/laundry-api \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name laundry-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT signing secret (32+ char random) | `openssl rand -hex 32` |
| `SECRET_KEY` | Flask session secret | `openssl rand -hex 32` |
| `FLASK_ENV` | `production` or `development` | `production` |
| `DEBUG` | `false` in production | `false` |
| `REDIS_URL` | Redis connection (Phase 2) | `redis://host:6379/0` |

---

## Post-Deployment Checklist

- [ ] `GET https://api.yourdomain.com/health` returns `{"status": "OK"}`
- [ ] `GET https://api.yourdomain.com/docs` shows Swagger UI
- [ ] `GET https://api.yourdomain.com/openapi.yaml` returns the spec
- [ ] Create first ADMIN user via direct DB or seeding script
- [ ] Set up CloudWatch alarm for 5xx error rate > 1%
- [ ] Set up CloudWatch alarm for ECS CPU > 80%
- [ ] Enable RDS automated backups (already set: 7 days)
- [ ] Enable RDS deletion protection (already set)
- [ ] Test `POST /user/login` returns JWT
- [ ] Verify Secrets Manager secrets are loaded (check `/health` logs)

---

## Seeding the First Admin User

SSH into an ECS task or run a one-off task:

```bash
aws ecs run-task \
  --cluster laundry-cluster \
  --task-definition laundry-api \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIV_SUB_1],securityGroups=[$ECS_SG],assignPublicIp=DISABLED}" \
  --overrides '{
    "containerOverrides": [{
      "name": "laundry-api",
      "command": ["python", "-c",
        "from app.app import create_app; from app.models.base import db; from app.user.models import User, UserType; from werkzeug.security import generate_password_hash; app=create_app(); ctx=app.app_context(); ctx.push(); u=User(username=\"admin\",email=\"admin@laundry.com\",phone=\"9999999999\",password_hash=generate_password_hash(\"changeme123\"),user_type=UserType.ADMIN); db.session.add(u); db.session.commit(); print(\"Admin created\")"
      ]
    }]
  }'
```

> Change the password immediately after first login.

---

## Useful Commands

```bash
# View live logs
aws logs tail /ecs/laundry-api --follow

# Force new deployment (after pushing a new image)
aws ecs update-service \
  --cluster laundry-cluster \
  --service laundry-api \
  --force-new-deployment

# Check service health
aws ecs describe-services \
  --cluster laundry-cluster \
  --services laundry-api \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount}'

# List running tasks
aws ecs list-tasks --cluster laundry-cluster --service-name laundry-api
```

---

## Cost Estimate (ap-south-1 / Mumbai)

| Service | Config | Est. Monthly |
|---|---|---|
| ECS Fargate | 2 tasks × 0.5 vCPU / 1 GB | ~$15 |
| RDS PostgreSQL | db.t3.micro, 20 GB gp3 | ~$20 |
| ALB | 1 ALB, ~10 GB processed | ~$20 |
| ECR | ~1 GB storage | ~$0.10 |
| CloudWatch | Basic logs | ~$3 |
| Secrets Manager | 2 secrets | ~$0.80 |
| **Total** | | **~$60/month** |

*Scale up RDS to db.t3.small and Fargate to 1 vCPU / 2 GB for production traffic.*

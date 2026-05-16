# AWS Deployment Guide — Laundry Management System

> Hand this document to your cloud engineer.  
> All shell commands are AWS CLI unless noted. Run them in order.

---

## Why Not RDS? Why Not Redis?

### PostgreSQL on EC2 instead of RDS

| | RDS (managed) | EC2 Ubuntu (self-managed) |
|---|---|---|
| Monthly cost | ~₹1,700 (db.t3.micro) | ~₹700 (t3.micro + 30 GB EBS) |
| Automated backups | ✅ built-in | ⚠️ manual cron (pg_dump) |
| Patching | ✅ AWS handles | ⚠️ you run `apt upgrade` |
| Multi-AZ failover | ✅ one click | ❌ manual setup |
| Effort to set up | 5 min console | ~20 min commands |

**Decision: EC2 Ubuntu** — saves ~₹1,000/month. For Phase 1 traffic (internal tool, not millions of users) the tradeoff is worth it. Migrate to RDS later if needed with zero code changes (same DATABASE_URL format).

### Redis — not installed in Phase 1

Redis is **not used anywhere** in Phase 1 code. It was in the original scaffold but removed. It will be added in Phase 2 for:
- Background job queue (sending notifications after delivery)
- Caching frequently-read price lists / item catalogs

Do **not** install Redis now. Skip it entirely.

---

## Architecture (Phase 1)

```
Internet
   │
   ▼
[Elastic IP]  ──or──  [ALB + ACM cert if you have a domain]
   │
   ▼
[EC2 t3.small]   — Ubuntu 22.04 — public subnet
   │  Flask API (Gunicorn, port 80)
   │  Nginx reverse proxy (port 80/443)
   │
   ▼ (private network, same VPC)
[EC2 t3.micro]   — Ubuntu 22.04 — private subnet
   │  PostgreSQL 15 (port 5432)
   │  pg_dump cron → S3 (backups)
   │
[Secrets Manager]   env vars (JWT key, DB password)
[CloudWatch Logs]   /var/log/laundry (streamed via agent)
```

### Simpler alternative (single server, minimal cost)

If you want the absolute cheapest setup (dev/staging):

```
[EC2 t3.small — Ubuntu 22.04]
  ├── Nginx (port 80/443)
  ├── Gunicorn / Flask API (port 8000, internal)
  └── PostgreSQL 15 (port 5432, localhost only)
```

Single server — **~₹600/month** (t3.small + 30 GB EBS). Use this for internal/pilot use.  
Split into two servers when you need DB backups isolated or expect > 50 concurrent users.

This guide covers **two-server setup** (more production-like).

---

## Step 1 — AWS Prerequisites

```bash
# Install and configure AWS CLI
aws configure
# Enter: Access Key ID, Secret, Region (ap-south-1 = Mumbai), output format (json)

REGION=ap-south-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account: $ACCOUNT_ID  Region: $REGION"
```

---

## Step 2 — Create VPC & Networking

```bash
# VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=laundry-vpc

# Public subnet (API server lives here)
PUB_SUB=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 --availability-zone ${REGION}a \
  --query 'Subnet.SubnetId' --output text)
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB --map-public-ip-on-launch

# Private subnet (DB server lives here)
PRIV_SUB=$(aws ec2 create-subnet --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 --availability-zone ${REGION}a \
  --query 'Subnet.SubnetId' --output text)

# Internet Gateway (so API server can reach the internet / ECR)
IGW=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC_ID

# Route table for public subnet
RTB=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $RTB \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
aws ec2 associate-route-table --route-table-id $RTB --subnet-id $PUB_SUB

echo "VPC: $VPC_ID  Public: $PUB_SUB  Private: $PRIV_SUB"
```

---

## Step 3 — Security Groups

```bash
# API server: allow SSH (22) + HTTP (80) + HTTPS (443) from anywhere
API_SG=$(aws ec2 create-security-group \
  --group-name laundry-api-sg --description "Laundry API" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $API_SG \
  --ip-permissions \
  '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]},
    {"IpProtocol":"tcp","FromPort":80,"ToPort":80,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]},
    {"IpProtocol":"tcp","FromPort":443,"ToPort":443,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]'

# DB server: allow PostgreSQL (5432) from API server's subnet ONLY
DB_SG=$(aws ec2 create-security-group \
  --group-name laundry-db-sg --description "Laundry DB" \
  --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $DB_SG \
  --protocol tcp --port 5432 --cidr 10.0.1.0/24     # API subnet only
aws ec2 authorize-security-group-ingress --group-id $DB_SG \
  --protocol tcp --port 22  --cidr 10.0.1.0/24      # SSH via API server (bastion)

echo "API SG: $API_SG  DB SG: $DB_SG"
```

---

## Step 4 — Create SSH Key Pair

```bash
aws ec2 create-key-pair --key-name laundry-key \
  --query 'KeyMaterial' --output text > ~/.ssh/laundry-key.pem
chmod 400 ~/.ssh/laundry-key.pem
echo "Key saved to ~/.ssh/laundry-key.pem"
```

---

## Step 5 — Launch EC2 Instances

Get the latest Ubuntu 22.04 AMI for Mumbai:

```bash
AMI=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters 'Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*' \
            'Name=state,Values=available' \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text)
echo "AMI: $AMI"
```

### 5a. DB Server (private subnet)

```bash
DB_INSTANCE=$(aws ec2 run-instances \
  --image-id $AMI \
  --instance-type t3.micro \
  --key-name laundry-key \
  --subnet-id $PRIV_SUB \
  --security-group-ids $DB_SG \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=laundry-db}]' \
  --query 'Instances[0].InstanceId' --output text)

aws ec2 wait instance-running --instance-ids $DB_INSTANCE
DB_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $DB_INSTANCE \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
echo "DB server private IP: $DB_PRIVATE_IP"
```

### 5b. API Server (public subnet)

```bash
API_INSTANCE=$(aws ec2 run-instances \
  --image-id $AMI \
  --instance-type t3.small \
  --key-name laundry-key \
  --subnet-id $PUB_SUB \
  --security-group-ids $API_SG \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=laundry-api}]' \
  --query 'Instances[0].InstanceId' --output text)

aws ec2 wait instance-running --instance-ids $API_INSTANCE
API_PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $API_INSTANCE \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "API server public IP: $API_PUBLIC_IP"
```

> Allocate an **Elastic IP** so the IP doesn't change on reboot:
> ```bash
> EIP=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
> aws ec2 associate-address --instance-id $API_INSTANCE --allocation-id $EIP
> ```

---

## Step 6 — Install PostgreSQL 15 on DB Server

SSH into the DB server **through** the API server (it has no public IP):

```bash
# From your laptop → API server → DB server
ssh -i ~/.ssh/laundry-key.pem -J ubuntu@$API_PUBLIC_IP ubuntu@$DB_PRIVATE_IP
```

Run these commands **on the DB server**:

```bash
# Install PostgreSQL 15
sudo apt update && sudo apt upgrade -y
sudo apt install -y postgresql-15 postgresql-client-15

# Start and enable service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database user and database
sudo -u postgres psql << 'SQL'
CREATE USER laundry_user WITH PASSWORD 'CHANGE_THIS_STRONG_PASSWORD';
CREATE DATABASE laundry_db OWNER laundry_user;
GRANT ALL PRIVILEGES ON DATABASE laundry_db TO laundry_user;
\q
SQL

# Allow remote connections from API subnet (10.0.1.0/24)
PG_CONF=$(sudo -u postgres psql -t -c "SHOW config_file;" | xargs dirname)
sudo bash -c "echo \"listen_addresses = '*'\" >> $PG_CONF/postgresql.conf"
sudo bash -c "echo \"host laundry_db laundry_user 10.0.1.0/24 scram-sha-256\" >> $PG_CONF/pg_hba.conf"

sudo systemctl restart postgresql

# Verify it's listening
sudo ss -tlnp | grep 5432
```

**Test from API server** (not DB server):

```bash
# SSH into API server first
ssh -i ~/.ssh/laundry-key.pem ubuntu@$API_PUBLIC_IP

# Test DB connection
psql "postgresql://laundry_user:CHANGE_THIS_STRONG_PASSWORD@$DB_PRIVATE_IP:5432/laundry_db" \
  -c "SELECT version();"
```

---

## Step 7 — Set Up Automated Backups (pg_dump → S3)

On the DB server:

```bash
# Create S3 bucket for backups
aws s3 mb s3://laundry-db-backups-$(date +%Y) --region $REGION

# Install AWS CLI on DB server
sudo apt install -y awscli

# Create backup script
sudo tee /usr/local/bin/backup-postgres.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE=/tmp/laundry_${DATE}.sql.gz
pg_dump -U laundry_user -h localhost laundry_db | gzip > $BACKUP_FILE
aws s3 cp $BACKUP_FILE s3://laundry-db-backups-YEAR/daily/ --region ap-south-1
rm $BACKUP_FILE
echo "Backup $BACKUP_FILE uploaded to S3"
EOF
sudo chmod +x /usr/local/bin/backup-postgres.sh

# Schedule daily at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * PGPASSWORD='CHANGE_THIS_STRONG_PASSWORD' /usr/local/bin/backup-postgres.sh >> /var/log/pg_backup.log 2>&1") | crontab -
```

> Attach an IAM role to the DB EC2 instance with `s3:PutObject` permission on the bucket, or configure `aws configure` with dedicated backup credentials.

---

## Step 8 — Deploy Flask API on API Server

SSH into the API server:

```bash
ssh -i ~/.ssh/laundry-key.pem ubuntu@$API_PUBLIC_IP
```

Run these **on the API server**:

```bash
# System dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip \
                   libpq-dev gcc nginx git

# Clone repo
git clone https://github.com/arundevspace/Laundaury-App.git /opt/laundry
cd /opt/laundry/backend

# Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Environment file
cat > /opt/laundry/backend/.env << EOF
DATABASE_URL=postgresql://laundry_user:CHANGE_THIS_STRONG_PASSWORD@DB_PRIVATE_IP:5432/laundry_db
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_APP=run.py
FLASK_ENV=production
DEBUG=false
EOF

# Run DB migrations
source .venv/bin/activate
cd /opt/laundry/backend
flask db upgrade

# Test the app
gunicorn -w 2 -b 127.0.0.1:8000 run:app --daemon
curl http://127.0.0.1:8000/health
```

---

## Step 9 — Nginx Reverse Proxy

On the API server:

```bash
# Nginx config
sudo tee /etc/nginx/sites-available/laundry << 'EOF'
server {
    listen 80;
    server_name _;          # replace with your domain if you have one

    # Swagger docs
    location /docs       { proxy_pass http://127.0.0.1:8000; }
    location /openapi.yaml { proxy_pass http://127.0.0.1:8000; }

    # API
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/laundry /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Test
curl http://$API_PUBLIC_IP/health
```

---

## Step 10 — Systemd Service (auto-restart on reboot)

On the API server:

```bash
sudo tee /etc/systemd/system/laundry.service << 'EOF'
[Unit]
Description=Laundry Management API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/laundry/backend
EnvironmentFile=/opt/laundry/backend/.env
ExecStart=/opt/laundry/backend/.venv/bin/gunicorn \
          -w 4 -b 127.0.0.1:8000 \
          --access-logfile /var/log/laundry-access.log \
          --error-logfile  /var/log/laundry-error.log \
          run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable laundry
sudo systemctl start laundry
sudo systemctl status laundry
```

---

## Step 11 — HTTPS with Let's Encrypt (if you have a domain)

```bash
# Point your domain A record → API_PUBLIC_IP first, then:
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com --non-interactive \
  --agree-tos -m your@email.com
sudo systemctl reload nginx
```

Free SSL, auto-renews every 90 days.

---

## Step 12 — Seed First Admin User

On the API server:

```bash
cd /opt/laundry/backend && source .venv/bin/activate
python3 << 'EOF'
from app.app import create_app
from app.models.base import db
from app.user.models import User, UserType
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    u = User(
        username="admin",
        email="admin@laundry.com",
        phone="9999999999",
        password_hash=generate_password_hash("changeme123"),
        user_type=UserType.ADMIN,
    )
    db.session.add(u)
    db.session.commit()
    print("Admin user created. Change the password after first login!")
EOF
```

---

## Deploying Updates

Every time you push new code:

```bash
# On the API server
cd /opt/laundry
git pull origin main

cd backend
source .venv/bin/activate
pip install -r requirements.txt        # only if requirements changed
flask db upgrade                       # only if models changed
sudo systemctl restart laundry
curl http://127.0.0.1:8000/health
```

Or use the GitHub Actions CI/CD pipeline (`.github/workflows/deploy-aws.yml`) — it SSH-deploys automatically on push to `main` if you add `SSH_HOST`, `SSH_USER`, `SSH_KEY` as GitHub secrets.

---

## Environment Variables Reference

| Variable | Description | How to generate |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT signing key — keep secret | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `SECRET_KEY` | Flask session key | same as above |
| `FLASK_ENV` | `production` in prod | hardcode `production` |
| `DEBUG` | Must be `false` in prod | hardcode `false` |

---

## Redis — When to Add (Phase 2)

| Use case | Why Redis |
|---|---|
| Notification queue | Send WhatsApp/SMS after delivery without blocking the API |
| Order status webhooks | Push updates to customer app |
| Price list cache | Avoid DB hit on every order item lookup |

When Phase 2 starts: `sudo apt install redis-server` on the API server (or a separate t3.micro), add `REDIS_URL=redis://localhost:6379/0` to `.env`, and uncomment the Redis config line.

---

## Cost Estimate (ap-south-1 / Mumbai)

### Two-server setup (recommended)

| Resource | Spec | Cost/month |
|---|---|---|
| API Server | EC2 t3.small (2 vCPU, 2 GB) + 20 GB gp3 | ~₹800 |
| DB Server | EC2 t3.micro (2 vCPU, 1 GB) + 30 GB gp3 | ~₹700 |
| Elastic IP | 1 static IP | ~₹0 (free while attached) |
| S3 backups | ~5 GB/month | ~₹10 |
| Data transfer | First 100 GB free | ₹0 |
| **Total** | | **~₹1,500/month** |

### Single-server setup (pilot / internal tool)

| Resource | Spec | Cost/month |
|---|---|---|
| API + DB Server | EC2 t3.small + 30 GB gp3 | ~₹800 |
| **Total** | | **~₹800/month** |

### Comparison

| Setup | Cost/month | Suitable for |
|---|---|---|
| Single EC2 (this guide) | ₹800 | Pilot / internal tool |
| Two EC2 (this guide) | ₹1,500 | Small production |
| ECS Fargate + RDS | ₹5,000 | Scaling production |
| ECS + RDS Multi-AZ | ₹12,000+ | High availability |

---

## Post-Deployment Checklist

- [ ] `curl http://SERVER_IP/health` returns `{"status":"OK"}`
- [ ] `http://SERVER_IP/docs` opens Swagger UI
- [ ] `POST /user/login` returns JWT token
- [ ] Run DB migration: `flask db upgrade`
- [ ] Admin user seeded and first login tested
- [ ] pg_dump cron running: `crontab -l` on DB server
- [ ] Systemd service enabled: `systemctl is-enabled laundry`
- [ ] Nginx serving correctly on port 80
- [ ] `.env` file not committed to Git (check `.gitignore`)
- [ ] Firewall: port 5432 not open to the internet (only API subnet)

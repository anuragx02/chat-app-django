# Deployment Guide

This guide covers deploying the Django Chat Application to production environments.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx (recommended for production)
- SSL certificate (recommended)

## General Deployment Steps

### 1. Server Setup

Update system packages:
```bash
sudo apt-get update
sudo apt-get upgrade
```

Install required packages:
```bash
sudo apt-get install python3-pip python3-venv postgresql redis-server nginx
```

### 2. Database Setup

Create PostgreSQL database and user:
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE chatapp;
CREATE USER chatuser WITH PASSWORD 'secure_password';
ALTER ROLE chatuser SET client_encoding TO 'utf8';
ALTER ROLE chatuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE chatuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE chatapp TO chatuser;
\q
```

### 3. Application Setup

Clone repository:
```bash
cd /var/www
git clone https://github.com/anuragx02/chat-app-django.git
cd chat-app-django
```

Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
pip install gunicorn  # For WSGI
```

### 4. Environment Configuration

Create `.env` file:
```bash
SECRET_KEY=your-production-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://chatuser:secure_password@localhost:5432/chatapp
REDIS_HOST=localhost
REDIS_PORT=6379
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### 5. Django Setup

Run migrations:
```bash
python manage.py migrate
```

Create superuser:
```bash
python manage.py createsuperuser
```

Collect static files:
```bash
python manage.py collectstatic --noinput
```

### 6. Systemd Service Setup

Create systemd service file for Daphne (ASGI):
```bash
sudo nano /etc/systemd/system/chatapp.service
```

```ini
[Unit]
Description=Chat App Daphne Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/chat-app-django
Environment="PATH=/var/www/chat-app-django/venv/bin"
ExecStart=/var/www/chat-app-django/venv/bin/daphne -b 127.0.0.1 -p 8000 chatapp.asgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable chatapp
sudo systemctl start chatapp
sudo systemctl status chatapp
```

### 7. Nginx Configuration

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/chatapp
```

```nginx
# WebSocket upgrade
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream chatapp {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Static files
    location /static/ {
        alias /var/www/chat-app-django/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/chat-app-django/media/;
        expires 7d;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://chatapp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Application
    location / {
        proxy_pass http://chatapp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/chatapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Setup with Let's Encrypt

Install Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

Obtain certificate:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Docker Deployment

### Using Docker Compose

Build and run:
```bash
docker-compose up -d
```

Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

Create superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

View logs:
```bash
docker-compose logs -f
```

### Production Docker Compose

For production, modify `docker-compose.yml`:
- Use PostgreSQL instead of SQLite
- Set `DEBUG=False`
- Use proper secret key
- Add volume mounts for persistent data
- Configure proper networking

## Heroku Deployment

### Prepare Application

Create `Procfile`:
```
web: daphne -b 0.0.0.0 -p $PORT chatapp.asgi:application
```

Create `runtime.txt`:
```
python-3.11.0
```

### Deploy

```bash
heroku login
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## AWS EC2 Deployment

1. Launch EC2 instance (Ubuntu 22.04 LTS)
2. Configure security groups (ports 80, 443, 22)
3. SSH into instance
4. Follow general deployment steps above
5. Configure Elastic IP
6. Set up RDS for PostgreSQL
7. Set up ElastiCache for Redis
8. Configure S3 for media files

## Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use HTTPS with valid SSL certificate
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Set up firewall (ufw/iptables)
- [ ] Configure PostgreSQL security
- [ ] Set up Redis password
- [ ] Regular security updates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Implement rate limiting
- [ ] Configure CSP headers

## Monitoring

### Application Monitoring

Install Sentry for error tracking:
```bash
pip install sentry-sdk
```

Add to settings.py:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Server Monitoring

Monitor system resources:
```bash
sudo apt-get install htop
```

Monitor logs:
```bash
sudo journalctl -u chatapp -f
sudo tail -f /var/log/nginx/error.log
```

## Backup Strategy

### Database Backup

Daily PostgreSQL backup:
```bash
pg_dump -U chatuser chatapp > backup_$(date +%Y%m%d).sql
```

Automated backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U chatuser chatapp | gzip > /backups/chatapp_$DATE.sql.gz
find /backups -name "chatapp_*.sql.gz" -mtime +30 -delete
```

### Media Files Backup

Backup media files:
```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz /var/www/chat-app-django/media/
```

## Performance Optimization

- Use Redis caching
- Optimize database queries
- Use CDN for static files
- Configure Nginx caching
- Enable Gzip compression
- Use database connection pooling
- Optimize images
- Implement lazy loading

## Troubleshooting

### WebSocket Connection Issues

Check Nginx WebSocket configuration:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

Check Redis connection:
```bash
redis-cli ping
```

### Database Issues

Check PostgreSQL status:
```bash
sudo systemctl status postgresql
```

Test database connection:
```bash
psql -U chatuser -d chatapp -h localhost
```

### Application Logs

View application logs:
```bash
sudo journalctl -u chatapp -n 100
```

View Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Scaling

### Horizontal Scaling

- Use load balancer (AWS ELB, Nginx)
- Multiple application servers
- Shared PostgreSQL and Redis
- Shared media storage (S3)

### Vertical Scaling

- Increase server resources
- Optimize database
- Use caching extensively
- CDN for static files

## Support

For deployment issues:
- Check application logs
- Verify environment variables
- Test database and Redis connections
- Review Nginx configuration
- Check firewall settings

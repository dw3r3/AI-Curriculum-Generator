# Setup & Deployment Guide - AI Curriculum Platform

## 🚀 **Quick Start (Development)**

### **Prerequisites**
- **Python 3.8+** (Recommended: Python 3.10+)
- **pip** (Python package manager)
- **Git** (for version control)
- **Google Gemini API Key** (for AI curriculum generation)

### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd ai_curriculum
```

### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Environment Configuration**
Create a `.env` file in the project root:
```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Get Gemini API Key**:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

### **Step 5: Database Setup**
```bash
# Run migrations
python manage.py migrate

# Create superuser (optional - for Django admin)
python manage.py createsuperuser
```

### **Step 6: Create Admin User**
```bash
# Create admin user for the platform
python manage.py create_admin \
    --username admin \
    --email admin@example.com \
    --full-name "System Administrator" \
    --super-admin \
    --can-delete-users
```

### **Step 7: Start Development Server**
```bash
python manage.py runserver 8001
```

### **Step 8: Access the Application**
- **Student Portal**: http://127.0.0.1:8001/
- **Admin Dashboard**: Login with admin credentials at the same URL

---

## 📦 **Dependencies**

### **requirements.txt**
```txt
Django==5.2.5
google-generativeai==0.8.3
reportlab==4.2.5
Pillow==10.4.0
python-decouple==3.8
psycopg2-binary==2.9.9  # For PostgreSQL (production)
gunicorn==21.2.0        # For production deployment
whitenoise==6.6.0       # For static file serving
```

### **Core Dependencies Explained**
- **Django**: Web framework
- **google-generativeai**: Google Gemini AI integration
- **reportlab**: PDF generation
- **Pillow**: Image processing (for avatars)
- **python-decouple**: Environment variable management
- **psycopg2-binary**: PostgreSQL database adapter
- **gunicorn**: WSGI HTTP Server for production
- **whitenoise**: Static file serving middleware

---

## 🗄️ **Database Configuration**

### **Development (SQLite)**
Default configuration uses SQLite - no additional setup required.

### **Production (PostgreSQL)**
Update `settings.py`:
```python
import os
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

Environment variables:
```bash
DB_NAME=ai_curriculum_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 🔧 **Configuration Options**

### **Django Settings**
Key settings in `ai_curriculum/settings.py`:

```python
# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'accounts' / 'static']

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email Configuration (for production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
```

### **AI Configuration**
Google Gemini AI setup in `views.py`:
```python
import google.generativeai as genai
import os

# Configure the API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Model configuration
model = genai.GenerativeModel('gemini-1.5-flash')
```

---

## 🚀 **Production Deployment**

### **Option 1: Traditional Server Deployment**

#### **1. Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Create application user
sudo adduser appuser
sudo usermod -aG sudo appuser
```

#### **2. Application Setup**
```bash
# Switch to app user
sudo su - appuser

# Clone repository
git clone <repository-url>
cd ai_curriculum

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### **3. Database Setup**
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE ai_curriculum_db;
CREATE USER appuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_curriculum_db TO appuser;
\q
```

#### **4. Environment Configuration**
```bash
# Create production .env file
cat > .env << EOF
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
GEMINI_API_KEY=your_gemini_api_key
DB_NAME=ai_curriculum_db
DB_USER=appuser
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EOF
```

#### **5. Django Setup**
```bash
# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create admin user
python manage.py create_admin --username admin --email admin@yourdomain.com --full-name "Administrator" --super-admin --can-delete-users
```

#### **6. Gunicorn Configuration**
```bash
# Create gunicorn service file
sudo nano /etc/systemd/system/ai_curriculum.service
```

```ini
[Unit]
Description=AI Curriculum Django App
After=network.target

[Service]
User=appuser
Group=www-data
WorkingDirectory=/home/appuser/ai_curriculum
Environment="PATH=/home/appuser/ai_curriculum/venv/bin"
ExecStart=/home/appuser/ai_curriculum/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/appuser/ai_curriculum/ai_curriculum.sock ai_curriculum.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start ai_curriculum
sudo systemctl enable ai_curriculum
```

#### **7. Nginx Configuration**
```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/ai_curriculum
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/appuser/ai_curriculum;
    }
    
    location /media/ {
        root /home/appuser/ai_curriculum;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/appuser/ai_curriculum/ai_curriculum.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ai_curriculum /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### **Option 2: Docker Deployment**

#### **Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ai_curriculum.wsgi:application"]
```

#### **docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your_secret_key
      - GEMINI_API_KEY=your_gemini_key
      - DB_HOST=db
      - DB_NAME=ai_curriculum
      - DB_USER=postgres
      - DB_PASSWORD=postgres
    depends_on:
      - db
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=ai_curriculum
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### **Deploy with Docker**
```bash
# Build and start containers
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py create_admin --username admin --email admin@example.com --full-name "Administrator" --super-admin --can-delete-users
```

---

## 🔒 **Security Checklist**

### **Production Security**
- [ ] Set `DEBUG = False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS (SSL certificate)
- [ ] Set up proper database permissions
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Backup strategy implementation

### **Environment Variables**
```bash
# Required for production
SECRET_KEY=your_very_secure_secret_key_minimum_50_characters
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
GEMINI_API_KEY=your_gemini_api_key

# Database
DB_NAME=ai_curriculum_db
DB_USER=your_db_user
DB_PASSWORD=secure_database_password
DB_HOST=localhost
DB_PORT=5432

# Email (optional but recommended)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_specific_password
```

---

## 🔧 **Management Commands**

### **Create Admin User**
```bash
python manage.py create_admin --help
python manage.py create_admin --username admin --email admin@example.com --full-name "Administrator" --super-admin --can-delete-users
```

### **Database Management**
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

### **Static Files**
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

---

## 📊 **Monitoring & Maintenance**

### **Log Files**
- **Django logs**: Check application logs for errors
- **Nginx logs**: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
- **Gunicorn logs**: Check systemd journal with `journalctl -u ai_curriculum`

### **Database Backup**
```bash
# PostgreSQL backup
pg_dump -U appuser -h localhost ai_curriculum_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -U appuser -h localhost ai_curriculum_db < backup_file.sql
```

### **Regular Maintenance**
- Monitor disk space and database size
- Regular security updates
- Database optimization and cleanup
- Log rotation and cleanup
- SSL certificate renewal

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Gemini API Errors**
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API connection
python -c "import google.generativeai as genai; genai.configure(api_key='your_key'); print('API key works')"
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
python manage.py dbshell
```

#### **Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check nginx configuration
sudo nginx -t
```

#### **Permission Errors**
```bash
# Fix file permissions
sudo chown -R appuser:www-data /home/appuser/ai_curriculum
sudo chmod -R 755 /home/appuser/ai_curriculum
```

### **Debug Mode**
For troubleshooting, temporarily enable debug mode:
```python
# In settings.py
DEBUG = True
ALLOWED_HOSTS = ['*']  # Only for debugging
```

**Remember to disable debug mode in production!**

---

## 📱 **Mobile & Browser Compatibility**

### **Supported Browsers**
- **Chrome** 90+ (Recommended)
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

### **Mobile Responsiveness**
- Fully responsive design
- Touch-friendly interface
- Mobile-optimized forms and navigation
- Progressive Web App (PWA) ready

---

## 🔄 **Updates & Maintenance**

### **Updating the Application**
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart ai_curriculum
sudo systemctl restart nginx
```

### **Database Migrations**
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

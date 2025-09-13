#!/usr/bin/env python
"""
Database Reset Script for AI Curriculum Platform
This script will clean up and reorganize the database structure
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from accounts.models import AdminUser

def reset_database():
    """Reset and reorganize the database structure"""
    
    print("🔄 Starting database cleanup and reorganization...")
    print("=" * 60)
    
    # Step 1: Remove all migration files (except __init__.py)
    print("📁 Cleaning up migration files...")
    migrations_dir = project_dir / 'accounts' / 'migrations'
    
    for file in migrations_dir.glob('*.py'):
        if file.name != '__init__.py':
            file.unlink()
            print(f"   Removed: {file.name}")
    
    # Step 2: Remove database file
    print("\n🗄️ Removing old database...")
    db_file = project_dir / 'db.sqlite3'
    if db_file.exists():
        db_file.unlink()
        print("   ✅ Database file removed")
    
    # Step 3: Create fresh migrations
    print("\n📋 Creating fresh migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Step 4: Apply migrations
    print("\n⚡ Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Step 5: Create admin user
    print("\n👤 Creating admin user...")
    try:
        admin_user = AdminUser.objects.create(
            username='admin',
            email='admin@aicurriculum.com',
            full_name='System Administrator',
            can_manage_users=True,
            can_delete_users=True,
            can_manage_curricula=True,
            can_view_analytics=True,
            can_manage_admins=True
        )
        admin_user.set_password('admin123')
        admin_user.save()
        print("   ✅ Admin user created successfully")
        print(f"   Username: admin")
        print(f"   Password: admin123")
    except Exception as e:
        print(f"   ❌ Error creating admin user: {e}")
    
    print("\n🎉 Database reorganization complete!")
    print("=" * 60)
    print("📊 Database Structure:")
    print("   ✅ User (Django built-in)")
    print("   ✅ UserProfile (Extended user info)")
    print("   ✅ Curriculum (AI-generated curricula)")
    print("   ✅ UserProgress (Task completion tracking)")
    print("   ✅ UserNote (Learning notes)")
    print("   ✅ CurriculumFeedback (Ratings and reviews)")
    print("   ✅ Achievement (Gamification)")
    print("   ✅ AdminUser (Admin authentication)")
    print("   ✅ AdminSession (Admin session management)")
    print("\n🚀 Your database is now clean and properly organized!")

if __name__ == '__main__':
    reset_database()

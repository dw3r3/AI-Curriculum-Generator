import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from accounts.models import AdminUser

# Create admin user
admin = AdminUser.objects.create(
    username='admin',
    email='admin@aicurriculum.com',
    full_name='System Administrator',
    is_active=True,
    can_manage_users=True,
    can_delete_users=True,
    can_manage_curricula=True,
    can_view_analytics=True,
    can_manage_admins=True
)

# Set password
admin.set_password('admin123')
admin.save()

print("Admin user created successfully!")
print("Username: admin")
print("Password: admin123")
print("Email: admin@aicurriculum.com")

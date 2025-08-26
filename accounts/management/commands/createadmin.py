from django.core.management.base import BaseCommand
from accounts.models import AdminUser

class Command(BaseCommand):
    help = 'Create an admin user for the application'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin username')
        parser.add_argument('--email', type=str, default='admin@aicurriculum.com', help='Admin email')
        parser.add_argument('--password', type=str, default='admin123', help='Admin password')
        parser.add_argument('--full-name', type=str, default='System Administrator', help='Admin full name')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        full_name = options['full_name']

        # Check if admin already exists
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists!')
            )
            return

        try:
            # Create admin user
            admin = AdminUser.objects.create(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True,
                can_manage_users=True,
                can_delete_users=True,
                can_manage_curricula=True,
                can_view_analytics=True,
                can_manage_admins=True
            )
            
            # Set password
            admin.set_password(password)
            admin.save()

            self.stdout.write(
                self.style.SUCCESS(f'Admin user created successfully!')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Full Name: {full_name}')
            
            self.stdout.write('\nTo access admin console:')
            self.stdout.write('1. Go to: http://127.0.0.1:8000/')
            self.stdout.write('2. Click "Login"')
            self.stdout.write('3. Enter the credentials above')
            self.stdout.write('4. You\'ll be redirected to admin dashboard')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )

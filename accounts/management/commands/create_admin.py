from django.core.management.base import BaseCommand
from accounts.models import AdminUser
import getpass


class Command(BaseCommand):
    help = 'Create a new admin user for the secure admin system'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email')
        parser.add_argument('--full-name', type=str, help='Admin full name')
        parser.add_argument('--super-admin', action='store_true', help='Grant super admin privileges')
        parser.add_argument('--can-delete-users', action='store_true', help='Grant user deletion permission')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🛡️  Creating Secure Admin User'))
        self.stdout.write('=' * 50)

        # Get username
        username = options.get('username')
        if not username:
            username = input('Admin Username: ')

        # Check if username already exists
        if AdminUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'❌ Admin user "{username}" already exists!'))
            return

        # Get email
        email = options.get('email')
        if not email:
            email = input('Admin Email: ')

        # Check if email already exists
        if AdminUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'❌ Admin email "{email}" already exists!'))
            return

        # Get full name
        full_name = options.get('full_name')
        if not full_name:
            full_name = input('Full Name: ')

        # Get password
        while True:
            password = getpass.getpass('Admin Password: ')
            password_confirm = getpass.getpass('Confirm Password: ')
            
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('❌ Passwords do not match. Please try again.'))
                continue
            
            if len(password) < 8:
                self.stdout.write(self.style.ERROR('❌ Password must be at least 8 characters long.'))
                continue
            
            break

        # Check for super admin privileges
        is_super_admin = options.get('super_admin', False)
        if not is_super_admin:
            super_admin_input = input('Grant super admin privileges? (y/N): ').lower()
            is_super_admin = super_admin_input in ['y', 'yes']

        # Check for user deletion permission
        can_delete_users = options.get('can_delete_users', False)
        if not can_delete_users and not is_super_admin:  # Super admins get all permissions
            delete_input = input('Grant user deletion permission? (y/N): ').lower()
            can_delete_users = delete_input in ['y', 'yes']

        # Create admin user
        try:
            admin_user = AdminUser.objects.create(
                username=username,
                email=email,
                full_name=full_name,
                can_manage_users=True,
                can_delete_users=can_delete_users or is_super_admin,  # Super admins get all permissions
                can_manage_curricula=True,
                can_view_analytics=True,
                can_manage_admins=is_super_admin
            )
            admin_user.set_password(password)
            admin_user.save()

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Admin user created successfully!'))
            self.stdout.write('')
            self.stdout.write('📋 Admin Details:')
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Full Name: {full_name}')
            self.stdout.write(f'   Super Admin: {"Yes" if is_super_admin else "No"}')
            self.stdout.write(f'   Can Delete Users: {"Yes" if admin_user.can_delete_users else "No"}')
            self.stdout.write('')
            self.stdout.write('🔐 Security Features:')
            self.stdout.write('   ✓ Password encrypted with Django\'s secure hashing')
            self.stdout.write('   ✓ Account lockout after 5 failed attempts')
            self.stdout.write('   ✓ Session timeout after 8 hours')
            self.stdout.write('   ✓ IP address and user agent logging')
            self.stdout.write('')
            self.stdout.write(f'🌐 Admin Login URL: http://your-domain.com/admin-login/')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  Keep these credentials secure!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating admin user: {str(e)}'))

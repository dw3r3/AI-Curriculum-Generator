from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check email verification status for users'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Check specific username')
        parser.add_argument('--all', action='store_true', help='Check all users')

    def handle(self, *args, **options):
        self.stdout.write('🔍 Email Verification Status Check')
        self.stdout.write('=' * 50)

        if options.get('all'):
            users = User.objects.all()
        elif options.get('username'):
            try:
                users = [User.objects.get(username=options['username'])]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User "{options["username"]}" not found'))
                return
        else:
            users = User.objects.all()

        for user in users:
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                profile = None

            self.stdout.write(f'\n👤 User: {user.username} ({user.email})')
            self.stdout.write(f'   Account Active: {"✅ Yes" if user.is_active else "❌ No"}')
            
            if profile:
                self.stdout.write(f'   Email Verified: {"✅ Yes" if profile.email_verified else "❌ No"}')
                self.stdout.write(f'   Verification Token: {profile.email_verification_token}')
                
                if profile.email_verification_sent_at:
                    self.stdout.write(f'   Token Sent: {profile.email_verification_sent_at}')
                    expired = profile.is_verification_expired()
                    self.stdout.write(f'   Token Expired: {"❌ Yes" if expired else "✅ No"}')
                else:
                    self.stdout.write(f'   Token Sent: ❌ Never')
                
                # Generate verification URL for testing
                from django.urls import reverse
                verification_url = f"http://127.0.0.1:8001{reverse('verify_email', kwargs={'token': profile.email_verification_token})}"
                self.stdout.write(f'   Verification URL: {verification_url}')
            else:
                self.stdout.write(f'   Profile: ❌ No UserProfile found')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('💡 To manually verify a user, run:')
        self.stdout.write('   python manage.py verify_user --username <username>')
        self.stdout.write('   python manage.py verify_user --all')

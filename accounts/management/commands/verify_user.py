from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Manually verify a user email for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to verify')
        parser.add_argument('--email', type=str, help='Email to verify')
        parser.add_argument('--all', action='store_true', help='Verify all unverified users')

    def handle(self, *args, **options):
        if options.get('all'):
            # Verify all unverified users
            unverified_profiles = UserProfile.objects.filter(email_verified=False)
            count = 0
            for profile in unverified_profiles:
                profile.email_verified = True
                profile.user.is_active = True
                profile.user.save()
                profile.save()
                count += 1
                self.stdout.write(f'✅ Verified: {profile.user.username} ({profile.user.email})')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Verified {count} users'))
            return

        username = options.get('username')
        email = options.get('email')

        if not username and not email:
            self.stdout.write(self.style.ERROR('❌ Please provide --username, --email, or --all'))
            return

        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(email=email)

            profile, created = UserProfile.objects.get_or_create(user=user)
            
            if profile.email_verified:
                self.stdout.write(self.style.WARNING(f'⚠️  User {user.username} is already verified'))
                return

            # Verify the user
            profile.email_verified = True
            user.is_active = True
            user.save()
            profile.save()

            self.stdout.write(self.style.SUCCESS(f'✅ Successfully verified user: {user.username} ({user.email})'))
            self.stdout.write(f'   User can now login to the platform')

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

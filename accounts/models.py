from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# ============================================================================
# STUDENT MODELS
# ============================================================================

class UserProfile(models.Model):
    """Extended user profile with learning preferences and gamification"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Account Verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # Personal Information
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)

    # Learning Preferences
    LEARNING_STYLES = [
        ('visual', 'Visual Learner'),
        ('auditory', 'Auditory Learner'),
        ('kinesthetic', 'Kinesthetic Learner'),
        ('reading', 'Reading/Writing Learner'),
    ]
    learning_style = models.CharField(max_length=20, choices=LEARNING_STYLES, default='visual')

    STUDY_PACE_CHOICES = [
        ('slow', 'Slow & Steady'),
        ('medium', 'Moderate Pace'),
        ('fast', 'Fast Track'),
    ]
    study_pace = models.CharField(max_length=10, choices=STUDY_PACE_CHOICES, default='medium')

    # Privacy Settings
    public_profile = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=True)

    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    study_reminders = models.BooleanField(default=True)
    achievement_notifications = models.BooleanField(default=True)

    # Gamification
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    study_streak = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - Level {self.level} ({self.xp} XP)"

    def add_xp(self, amount):
        """Add XP and handle level progression"""
        self.xp += amount
        self.update_level()
        self.save()

    def update_level(self):
        """Calculate and update user level based on XP"""
        new_level = min(int(self.xp / 100) + 1, 50)  # Max level 50
        if new_level > self.level:
            self.level = new_level
            # Award level achievement
            UserAchievement.objects.get_or_create(
                user=self.user,
                achievement_type='LEVEL_5' if new_level >= 5 else 'LEVEL_UP'
            )

    def get_level_progress(self):
        """Get progress percentage to next level"""
        current_level_xp = self.xp % 100
        return current_level_xp

    def get_avatar_url(self):
        """Get avatar URL or return default"""
        if self.avatar:
            return self.avatar.url
        return '/static/accounts/images/default_avatar.png'

    @property
    def total_xp(self):
        """Get total XP for display"""
        return self.xp

    def is_verification_expired(self):
        """Check if email verification token has expired (7 days)"""
        if not self.email_verification_sent_at:
            return True

        from django.conf import settings
        expiry_days = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)
        expiry_date = self.email_verification_sent_at + timezone.timedelta(days=expiry_days)
        return timezone.now() > expiry_date

class Curriculum(models.Model):
    """AI-generated learning curricula"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration = models.CharField(max_length=50, default='4 weeks')

    # JSON structure with weeks and tasks
    content = models.JSONField()

    # Progress tracking
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    progress_percentage = models.FloatField(default=0.0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.difficulty})"

    def update_progress(self):
        """Calculate and update progress percentage"""
        total_tasks = 0
        completed_tasks = 0

        # Handle both old and new content formats
        if isinstance(self.content, list):
            # Old format: content is directly a list of weeks
            weeks = self.content
        elif isinstance(self.content, dict) and 'weeks' in self.content:
            # New format: content is an object with 'weeks' key
            weeks = self.content['weeks']
        else:
            # Fallback: empty weeks
            weeks = []

        # Count total tasks from weeks
        for week in weeks:
            total_tasks += len(week.get('tasks', []))

        # Count completed tasks
        completed_tasks = UserProgress.objects.filter(
            user=self.user,
            curriculum=self,
            completed=True
        ).count()

        self.total_tasks = total_tasks
        self.completed_tasks = completed_tasks
        self.progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        self.save()

    def get_progress_percentage(self):
        """Get the current progress percentage"""
        return self.progress_percentage

class UserProgress(models.Model):
    """Track individual task completion for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    week_number = models.IntegerField()
    task_index = models.IntegerField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'curriculum', 'week_number', 'task_index']
        ordering = ['week_number', 'task_index']

    def __str__(self):
        return f"{self.user.username} - Week {self.week_number} Task {self.task_index} - {'✓' if self.completed else '✗'}"

class UserNote(models.Model):
    """User notes for curriculum sections"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    week_number = models.IntegerField(null=True, blank=True)
    task_index = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class CurriculumFeedback(models.Model):
    """User feedback and ratings for curricula"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars

    DIFFICULTY_RATING_CHOICES = [
        ('too_easy', 'Too Easy'),
        ('easy', 'Easy'),
        ('just_right', 'Just Right'),
        ('hard', 'Hard'),
        ('too_hard', 'Too Hard'),
    ]
    difficulty_rating = models.CharField(max_length=20, choices=DIFFICULTY_RATING_CHOICES, default='just_right')

    feedback_text = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'curriculum']  # One feedback per user per curriculum
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.curriculum.topic} ({self.rating}★)"

class UserAchievement(models.Model):
    """User achievements for gamification"""
    ACHIEVEMENT_TYPES = [
        ('FIRST_CURRICULUM', 'Created First Curriculum'),
        ('FIRST_NOTE', 'Created First Note'),
        ('FIRST_FEEDBACK', 'Provided First Feedback'),
        ('STREAK_7', '7-Day Study Streak'),
        ('LEVEL_5', 'Reached Level 5'),
        ('LEVEL_UP', 'Level Up'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement_type']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_achievement_type_display()}"

# ============================================================================
# ADMIN MODELS
# ============================================================================

class AdminUser(models.Model):
    """Separate admin user system with enhanced security"""
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Will be hashed
    full_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Admin permissions
    can_manage_users = models.BooleanField(default=True)
    can_delete_users = models.BooleanField(default=False)  # Separate permission for user deletion
    can_manage_curricula = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_manage_admins = models.BooleanField(default=False)  # Only super admin

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Admin: {self.username}"

    def set_password(self, raw_password):
        """Hash and set password"""
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if provided password matches"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def is_locked(self):
        """Check if account is locked due to failed attempts"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        self.locked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()

    def unlock_account(self):
        """Unlock account and reset attempts"""
        self.locked_until = None
        self.login_attempts = 0
        self.save()

class AdminSession(models.Model):
    """Secure admin session tracking"""
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Admin Session: {self.admin_user.username}"

    def is_expired(self):
        return timezone.now() > self.expires_at

# Code Documentation - AI Curriculum Platform

## 📁 **Project Structure**

```
ai_curriculum/
├── ai_curriculum/                 # Django project configuration
│   ├── __init__.py
│   ├── settings.py               # Main settings and configuration
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py                   # WSGI application entry point
│   └── asgi.py                   # ASGI application entry point
├── accounts/                     # Main Django application
│   ├── __init__.py
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions and business logic
│   ├── urls.py                   # URL patterns for the app
│   ├── admin.py                  # Django admin configuration
│   ├── apps.py                   # App configuration
│   ├── migrations/               # Database migration files
│   │   ├── 0001_initial.py
│   │   ├── 0002_curriculum_userprofile_userprogress.py
│   │   ├── 0003_usernote_curriculumfeedback_userachievement.py
│   │   ├── 0004_userprofile_avatar_userprofile_bio_and_more.py
│   │   ├── 0005_adminuser_adminsession.py
│   │   └── 0006_adminuser_can_delete_users.py
│   ├── management/               # Custom Django commands
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── create_admin.py   # Command to create admin users
│   ├── templates/                # HTML templates
│   │   └── accounts/
│   │       ├── login.html        # Unified login page
│   │       ├── register.html     # User registration
│   │       ├── dashboard.html    # Student dashboard
│   │       ├── curriculum_detail.html  # Curriculum view
│   │       ├── admin_dashboard.html     # Admin dashboard
│   │       ├── admin_users.html         # User management
│   │       ├── admin_curricula.html     # Curriculum management
│   │       └── admin_feedback.html      # Feedback management
│   └── static/                   # Static files
│       └── accounts/
│           ├── css/
│           │   └── styles.css    # Main stylesheet
│           └── images/
│               └── dwa_logo.png  # Application logo
├── requirements.txt              # Python dependencies
├── manage.py                     # Django management script
└── db.sqlite3                    # SQLite database (development)
```

## 🗄️ **Database Models**

### **User-Related Models**

#### **UserProfile**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Personal Information
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Learning Preferences
    learning_style = models.CharField(max_length=20, choices=LEARNING_STYLES, default='visual')
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
    
    # Account Status
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Methods:**
- `add_xp(amount)` - Add XP and handle level progression
- `update_level()` - Calculate and update user level
- `get_level_progress()` - Get progress to next level
- `get_avatar_url()` - Get avatar URL or default

#### **Curriculum**
```python
class Curriculum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration = models.CharField(max_length=50, default='4 weeks')
    content = models.JSONField()  # Stores the AI-generated curriculum structure
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Progress tracking
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    progress_percentage = models.FloatField(default=0.0)
```

**JSON Structure:**
```json
{
  "weeks": [
    {
      "week": 1,
      "title": "Week Title",
      "description": "Week description",
      "tasks": [
        {
          "task": "Task description",
          "resources": ["Resource 1", "Resource 2"],
          "videos": ["Video URL 1", "Video URL 2"]
        }
      ]
    }
  ]
}
```

#### **UserProgress**
```python
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    week_number = models.IntegerField()
    task_index = models.IntegerField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### **UserNote**
```python
class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    week_number = models.IntegerField(null=True, blank=True)
    task_index = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### **CurriculumFeedback**
```python
class CurriculumFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    difficulty_rating = models.CharField(max_length=20, choices=DIFFICULTY_RATING_CHOICES)
    feedback_text = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### **UserAchievement**
```python
class UserAchievement(models.Model):
    ACHIEVEMENT_TYPES = [
        ('FIRST_CURRICULUM', 'Created First Curriculum'),
        ('FIRST_NOTE', 'Created First Note'),
        ('FIRST_FEEDBACK', 'Provided First Feedback'),
        ('STREAK_7', '7-Day Study Streak'),
        ('LEVEL_5', 'Reached Level 5'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)
```

### **Admin Models**

#### **AdminUser**
```python
class AdminUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Hashed password
    full_name = models.CharField(max_length=200)
    
    # Account Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Security
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Permissions
    can_manage_users = models.BooleanField(default=True)
    can_delete_users = models.BooleanField(default=False)
    can_manage_curricula = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_manage_admins = models.BooleanField(default=False)  # Super admin only
```

**Key Methods:**
- `set_password(raw_password)` - Hash and set password
- `check_password(raw_password)` - Verify password
- `is_locked()` - Check if account is locked
- `lock_account(minutes=30)` - Lock account temporarily
- `unlock_account()` - Unlock and reset attempts

#### **AdminSession**
```python
class AdminSession(models.Model):
    admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
```

## 🔧 **View Functions**

### **Authentication Views**

#### **Unified Login System**
```python
def login_view(request):
    """
    Unified login that handles both regular users and admin users.
    
    Process:
    1. Try admin authentication first
    2. If not admin, try regular user authentication
    3. Route to appropriate dashboard based on user type
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Try admin authentication first
        try:
            admin_user = AdminUser.objects.get(username=username, is_active=True)
            if admin_user.check_password(password):
                create_admin_session(admin_user, request)
                return redirect('admin_dashboard')
        except AdminUser.DoesNotExist:
            pass

        # Try regular user authentication
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return redirect('dashboard')
```

#### **Admin Authentication Helpers**
```python
def create_admin_session(admin_user, request):
    """Create secure admin session with tracking"""
    session_key = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timezone.timedelta(hours=8)
    
    AdminSession.objects.create(
        admin_user=admin_user,
        session_key=session_key,
        expires_at=expires_at,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

def admin_required(view_func):
    """Decorator to require admin authentication"""
    def wrapper(request, *args, **kwargs):
        admin_user = get_admin_user(request)
        if not admin_user:
            return redirect('login')
        request.admin_user = admin_user
        return view_func(request, *args, **kwargs)
    return wrapper
```

### **Student Views**

#### **Dashboard**
```python
@login_required
def dashboard(request):
    """
    Student dashboard with curriculum history and statistics
    """
    # Get user's curricula with progress
    curricula = Curriculum.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate progress for each curriculum
    for curriculum in curricula:
        total_tasks = 0
        completed_tasks = 0
        
        for week in curriculum.content.get('weeks', []):
            total_tasks += len(week.get('tasks', []))
            
        completed_tasks = UserProgress.objects.filter(
            user=request.user,
            curriculum=curriculum,
            completed=True
        ).count()
        
        curriculum.progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get user profile and achievements
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    recent_achievements = UserAchievement.objects.filter(user=request.user).order_by('-earned_at')[:5]
    
    context = {
        'curricula': curricula,
        'profile': profile,
        'recent_achievements': recent_achievements,
    }
    return render(request, 'accounts/dashboard.html', context)
```

#### **AI Curriculum Generation**
```python
@login_required
def generate_curriculum(request):
    """
    Generate AI-powered curriculum using Google Gemini
    """
    if request.method == 'POST':
        topic = request.POST.get('topic')
        difficulty = request.POST.get('difficulty', 'beginner')
        duration = request.POST.get('duration', '4 weeks')
        
        # Validate input
        errors = validate_curriculum_input(topic, difficulty, duration)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        try:
            # Generate curriculum using Gemini AI
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Create a detailed {duration} curriculum for learning {topic} at {difficulty} level.
            
            Format as JSON with this structure:
            {{
                "weeks": [
                    {{
                        "week": 1,
                        "title": "Week title",
                        "description": "What will be covered",
                        "tasks": [
                            {{
                                "task": "Specific learning task",
                                "resources": ["Resource 1", "Resource 2"],
                                "videos": ["Video URL or search term"]
                            }}
                        ]
                    }}
                ]
            }}
            """
            
            response = model.generate_content(prompt)
            curriculum_data = json.loads(response.text)
            
            # Save curriculum to database
            curriculum = Curriculum.objects.create(
                user=request.user,
                topic=topic,
                difficulty=difficulty,
                duration=duration,
                content=curriculum_data
            )
            
            # Award achievement for first curriculum
            if not UserAchievement.objects.filter(user=request.user, achievement_type='FIRST_CURRICULUM').exists():
                UserAchievement.objects.create(user=request.user, achievement_type='FIRST_CURRICULUM')
            
            return JsonResponse({
                'success': True,
                'curriculum_id': curriculum.id,
                'redirect_url': reverse('curriculum_detail', args=[curriculum.id])
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
```

### **Admin Views**

#### **Admin Dashboard**
```python
@admin_required
def admin_dashboard(request):
    """
    Admin dashboard with platform statistics and insights
    """
    # Platform statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_curricula = Curriculum.objects.count()
    total_notes = UserNote.objects.count()
    total_feedback = CurriculumFeedback.objects.count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_curricula = Curriculum.objects.order_by('-created_at')[:10]
    recent_feedback = CurriculumFeedback.objects.order_by('-created_at')[:10]
    
    # Popular topics analysis
    from django.db.models import Count
    popular_topics = Curriculum.objects.values('topic').annotate(
        count=Count('topic')
    ).order_by('-count')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_curricula': total_curricula,
        'total_notes': total_notes,
        'total_feedback': total_feedback,
        'recent_users': recent_users,
        'recent_curricula': recent_curricula,
        'recent_feedback': recent_feedback,
        'popular_topics': popular_topics,
        'admin_user': request.admin_user,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)
```

#### **User Management**
```python
@admin_required
def admin_users(request):
    """
    User management interface for admins
    """
    users = User.objects.all().order_by('-date_joined')
    
    # Add statistics for each user
    for user in users:
        user.curriculum_count = Curriculum.objects.filter(user=user).count()
        user.notes_count = UserNote.objects.filter(user=user).count()
        user.feedback_count = CurriculumFeedback.objects.filter(user=user).count()
        try:
            user.profile = user.userprofile
        except:
            user.profile = None
    
    context = {
        'users': users,
        'admin_user': request.admin_user
    }
    return render(request, 'accounts/admin_users.html', context)
```

#### **User Deletion**
```python
@csrf_exempt
@admin_required
def admin_delete_user(request):
    """
    Delete user account and all associated data with security checks
    """
    if request.method == 'POST':
        try:
            # Check admin permissions
            if not request.admin_user.can_delete_users:
                return JsonResponse({
                    'success': False, 
                    'error': 'You do not have permission to delete users.'
                }, status=403)
            
            data = json.loads(request.body)
            user_id = data.get('user_id')
            confirm_username = data.get('confirm_username', '')
            
            user = User.objects.get(id=user_id)
            
            # Security: confirm username matches
            if confirm_username != user.username:
                return JsonResponse({
                    'success': False, 
                    'error': 'Username confirmation does not match.'
                }, status=400)
            
            # Prevent deletion of admin users
            if AdminUser.objects.filter(email=user.email).exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot delete admin users.'
                }, status=400)
            
            # Get data counts before deletion
            curricula_count = Curriculum.objects.filter(user=user).count()
            notes_count = UserNote.objects.filter(user=user).count()
            feedback_count = CurriculumFeedback.objects.filter(user=user).count()
            
            # Delete user (cascades to related data)
            username = user.username
            email = user.email
            user.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'User "{username}" ({email}) deleted successfully.',
                'deleted_data': {
                    'curricula': curricula_count,
                    'notes': notes_count,
                    'feedback': feedback_count
                }
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

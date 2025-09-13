from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .models import Curriculum, UserProgress, UserProfile, UserNote, CurriculumFeedback, UserAchievement, AdminUser, AdminSession
import os
import json
import re
import uuid
import requests
import secrets
import hashlib
from urllib.parse import urlparse
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO

# Configure the API key
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

# Temporary code to list available models
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

def send_verification_email(user, request):
    """Send email verification to user"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created or not profile.email_verification_sent_at:
            profile.email_verification_token = uuid.uuid4()
            profile.email_verification_sent_at = timezone.now()
            profile.save()

        current_site = get_current_site(request)
        verification_url = f"http://{current_site.domain}{reverse('verify_email', kwargs={'token': profile.email_verification_token})}"

        subject = f'{settings.EMAIL_SUBJECT_PREFIX}Verify Your Email Address'
        message = f"""
        Hi {user.first_name or user.username},

        Thank you for registering with AI Curriculum! Please verify your email address by clicking the link below:

        {verification_url}

        This link will expire in {settings.ACCOUNT_ACTIVATION_DAYS} days.

        If you didn't create this account, please ignore this email.

        Best regards,
        AI Curriculum Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

def validate_video_link(url):
    """Validate if a video link is accessible"""
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False

        # Check if it's a known video platform
        video_platforms = ['youtube.com', 'youtu.be', 'vimeo.com', 'mit.edu', 'harvard.edu']
        if any(platform in parsed_url.netloc.lower() for platform in video_platforms):
            return True

        # Try to make a HEAD request to check if URL is accessible
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def validate_password_strength(password):
    """Validate password strength"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")

    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number.")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")

    return errors

# Admin Authentication Helper Functions
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_admin_session(admin_user, request):
    """Create a new admin session"""
    # Clean up expired sessions
    AdminSession.objects.filter(expires_at__lt=timezone.now()).delete()

    # Create new session
    session_key = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timezone.timedelta(hours=8)  # 8 hour sessions

    session = AdminSession.objects.create(
        admin_user=admin_user,
        session_key=session_key,
        expires_at=expires_at,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

    # Store session in request session
    request.session['admin_session_key'] = session_key
    request.session['admin_user_id'] = admin_user.id

    return session

def get_admin_user(request):
    """Get current admin user from session"""
    session_key = request.session.get('admin_session_key')
    admin_user_id = request.session.get('admin_user_id')

    if not session_key or not admin_user_id:
        return None

    try:
        session = AdminSession.objects.get(
            session_key=session_key,
            admin_user_id=admin_user_id,
            is_active=True
        )

        if session.is_expired():
            session.is_active = False
            session.save()
            return None

        return session.admin_user
    except AdminSession.DoesNotExist:
        return None

def admin_required(view_func):
    """Decorator to require admin authentication"""
    def wrapper(request, *args, **kwargs):
        admin_user = get_admin_user(request)
        if not admin_user:
            messages.info(request, 'Please login with your admin credentials to access the admin panel.')
            return redirect('login')

        request.admin_user = admin_user
        return view_func(request, *args, **kwargs)

    return wrapper

def admin_logout(request):
    """Logout admin user"""
    session_key = request.session.get('admin_session_key')
    if session_key:
        try:
            session = AdminSession.objects.get(session_key=session_key)
            session.is_active = False
            session.save()
        except AdminSession.DoesNotExist:
            pass

    # Clear session
    request.session.pop('admin_session_key', None)
    request.session.pop('admin_user_id', None)

def extract_json_from_response(text):
    """Extract JSON from AI response that might contain extra text"""
    # Try to find JSON array in the response
    json_pattern = r'\[[\s\S]*\]'
    match = re.search(json_pattern, text)
    if match:
        return match.group(0)
    return text

@csrf_exempt
def generate_curriculum(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic')
            duration = int(data.get('duration'))
            goal = data.get('goal') or "Learn the topic thoroughly"

            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""
Create a detailed {duration} curriculum for learning {topic} at {data.get('difficulty', 'beginner')} level.

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

Make it practical and hands-on with real-world applications.
Include 3-4 tasks per week.
Focus on {topic} fundamentals and practical skills.
Return only valid JSON, no extra text.
"""

            response = model.generate_content(prompt)
            ai_response = response.text

            print("AI raw output:", ai_response)

            try:
                # Extract JSON from response
                json_text = extract_json_from_response(ai_response)
                parsed = json.loads(json_text)

                # Ensure curriculum is in the correct format
                if isinstance(parsed, list):
                    # AI returned array of weeks (old format) - wrap it
                    validated_curriculum = {"weeks": parsed}
                else:
                    # AI returned object with weeks (new format) - use as is
                    validated_curriculum = parsed

                # Save curriculum to database if user is authenticated
                if request.user.is_authenticated:
                    # Create new curriculum with validated links
                    curriculum = Curriculum.objects.create(
                        user=request.user,
                        topic=topic,
                        difficulty=data.get('difficulty', 'beginner'),
                        duration=duration,
                        content=validated_curriculum
                    )

                    # Initialize progress tracking (should be 0% initially)
                    curriculum.update_progress()

                    return JsonResponse({
                        "success": True,
                        "curriculum": validated_curriculum,
                        "curriculum_id": curriculum.id
                    })
                else:
                    return JsonResponse({"success": True, "curriculum": validated_curriculum})

            except json.JSONDecodeError:
                return JsonResponse({
                    "success": False,
                    "error": "Invalid JSON from AI",
                    "raw_output": ai_response
                }, status=500)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"error": "Only POST allowed"}, status=405)



def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        # Validate passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html')

        # Validate password strength
        password_errors = validate_password_strength(password1)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return render(request, 'accounts/register.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'accounts/register.html')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address is already registered.")
            return render(request, 'accounts/register.html')

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messages.error(request, "Please enter a valid email address.")
            return render(request, 'accounts/register.html')

        try:
            from django.conf import settings
            require_verification = getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', True)

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=not require_verification  # Active immediately if verification not required
            )

            # Create user profile
            UserProfile.objects.create(
                user=user,
                email_verified=not require_verification  # Verified immediately if not required
            )

            if require_verification:
                # Send verification email
                if send_verification_email(user, request):
                    messages.success(request,
                        "Account created successfully! Please check your email to verify your account before logging in.")
                else:
                    messages.warning(request,
                        "Account created but there was an issue sending the verification email. Please contact support.")
            else:
                # Development mode - no verification needed
                messages.success(request,
                    "Account created successfully! You can now log in immediately.")

            return redirect('login')

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'accounts/register.html')

    return render(request, 'accounts/register.html')

def verify_email(request, token):
    """Verify user email with token"""
    try:
        # Try to find the profile with the given token
        try:
            profile = UserProfile.objects.get(email_verification_token=token)
        except UserProfile.DoesNotExist:
            messages.error(request, "Invalid verification link. The token was not found.")
            return redirect('register')

        # Check if verification has expired
        if profile.is_verification_expired():
            messages.error(request, "Email verification link has expired. Please register again.")
            return redirect('register')

        # Check if already verified
        if profile.email_verified:
            messages.info(request, "Email already verified. You can log in.")
            return redirect('login')

        # Activate user and mark email as verified
        profile.user.is_active = True
        profile.user.save()
        profile.email_verified = True
        profile.save()

        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect('login')

    except Exception as e:
        print(f"Email verification error: {e}")  # For debugging
        messages.error(request, f"Error during verification: {str(e)}")
        return redirect('register')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # First, try admin authentication
        try:
            admin_user = AdminUser.objects.get(username=username, is_active=True)

            # Check if admin account is locked
            if admin_user.is_locked():
                messages.error(request, 'Admin account is temporarily locked due to failed login attempts.')
                return render(request, 'accounts/login.html')

            # Check admin password
            if admin_user.check_password(password):
                # Reset login attempts on successful login
                admin_user.login_attempts = 0
                admin_user.last_login = timezone.now()
                admin_user.save()

                # Create admin session
                create_admin_session(admin_user, request)

                messages.success(request, f'Welcome back, {admin_user.full_name}!')
                return redirect('admin_dashboard')
            else:
                # Increment failed attempts for admin
                admin_user.login_attempts += 1
                if admin_user.login_attempts >= 5:
                    admin_user.lock_account(30)  # Lock for 30 minutes
                    messages.error(request, 'Too many failed attempts. Admin account locked for 30 minutes.')
                else:
                    remaining = 5 - admin_user.login_attempts
                    messages.error(request, f'Invalid credentials. {remaining} attempts remaining.')
                admin_user.save()
                return render(request, 'accounts/login.html')

        except AdminUser.DoesNotExist:
            # Not an admin user, try regular user authentication
            pass

        # Try regular user authentication
        user = authenticate(request, username=username, password=password)

        # If username auth failed, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            if user.is_active:
                # Check if email is verified (with fallback for development)
                try:
                    profile = UserProfile.objects.get(user=user)
                    if not profile.email_verified:
                        # In development, show warning but allow login
                        from django.conf import settings
                        if settings.DEBUG:
                            messages.warning(request, 'Email not verified, but login allowed in development mode.')
                        else:
                            messages.error(request, 'Please verify your email address before logging in.')
                            return render(request, 'accounts/login.html')
                except UserProfile.DoesNotExist:
                    # Create profile for existing users
                    UserProfile.objects.create(user=user, email_verified=True)

                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Account is not activated. Please check your email for verification link.')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'accounts/login.html')

@login_required(login_url='/')
def dashboard_view(request):
    # Get user's curriculum history
    curricula = Curriculum.objects.filter(user=request.user).order_by('-created_at')

    # Get the most recent curriculum as "active"
    active_curriculum = curricula.first()

    # Prepare curriculum content for frontend
    curriculum_content_json = None
    if active_curriculum and active_curriculum.content:
        import json
        # Ensure content is in the correct format for frontend
        if isinstance(active_curriculum.content, list):
            # Old format: wrap in weeks object
            curriculum_weeks = active_curriculum.content
        elif isinstance(active_curriculum.content, dict) and 'weeks' in active_curriculum.content:
            # New format: extract weeks array
            curriculum_weeks = active_curriculum.content['weeks']
        else:
            curriculum_weeks = []

        curriculum_content_json = json.dumps(curriculum_weeks)

    context = {
        'curricula': curricula,
        'active_curriculum': active_curriculum,
        'curriculum_content_json': curriculum_content_json,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def update_progress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            curriculum_id = data.get('curriculum_id')
            week_number = data.get('week_number')
            task_index = data.get('task_index')
            is_completed = data.get('is_completed', False)

            curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)

            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                curriculum=curriculum,
                week_number=week_number,
                task_index=task_index,
                defaults={'completed': is_completed}
            )

            if not created:
                progress.completed = is_completed
                progress.completed_at = timezone.now() if is_completed else None
                progress.save()
            elif is_completed:
                progress.completed_at = timezone.now()
                progress.save()

            # Update curriculum progress
            curriculum.update_progress()
            progress_percentage = curriculum.get_progress_percentage()

            # Check if curriculum is completed (100%)
            is_completed = progress_percentage >= 100.0

            return JsonResponse({
                'success': True,
                'progress_percentage': progress_percentage,
                'is_completed': is_completed,
                'congratulations': is_completed
            })

        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'Invalid JSON: {str(e)}'}, status=400)
        except Curriculum.DoesNotExist as e:
            return JsonResponse({'success': False, 'error': 'Curriculum not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

@login_required
def get_curriculum_progress(request, curriculum_id):
    try:
        curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)
        progress_data = {}

        # Handle both old and new content formats
        if isinstance(curriculum.content, list):
            weeks = curriculum.content
        elif isinstance(curriculum.content, dict) and 'weeks' in curriculum.content:
            weeks = curriculum.content['weeks']
        else:
            weeks = []

        for week_data in weeks:
            week_num = week_data.get('week', 1)
            progress_data[week_num] = {}

            for i, task in enumerate(week_data.get('tasks', [])):
                progress = UserProgress.objects.filter(
                    user=request.user,
                    curriculum=curriculum,
                    week_number=week_num,
                    task_index=i
                ).first()

                progress_data[week_num][i] = {
                    'completed': progress.completed if progress else False,
                    'completed_at': progress.completed_at.isoformat() if progress and progress.completed_at else None
                }

        # Prepare curriculum content for frontend
        curriculum_content = None
        if isinstance(curriculum.content, list):
            # Old format: content is directly a list of weeks
            curriculum_content = curriculum.content
        elif isinstance(curriculum.content, dict) and 'weeks' in curriculum.content:
            # New format: content is an object with 'weeks' key
            curriculum_content = curriculum.content['weeks']
        else:
            curriculum_content = []

        return JsonResponse({
            'success': True,
            'progress': progress_data,
            'overall_percentage': curriculum.progress_percentage,
            'curriculum_content': curriculum_content
        })

    except Curriculum.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Curriculum not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def download_curriculum_pdf(request, curriculum_id):
    try:
        curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph(f"<b>{curriculum.topic} Curriculum</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Duration
        duration_text = Paragraph(f"<b>Duration:</b> {curriculum.duration}", styles['Normal'])
        story.append(duration_text)
        story.append(Spacer(1, 12))

        # Difficulty
        difficulty_text = Paragraph(f"<b>Difficulty:</b> {curriculum.difficulty.title()}", styles['Normal'])
        story.append(difficulty_text)
        story.append(Spacer(1, 12))

        # Progress
        progress_percentage = curriculum.progress_percentage
        progress_text = Paragraph(f"<b>Progress:</b> {progress_percentage:.1f}% completed", styles['Normal'])
        story.append(progress_text)
        story.append(Spacer(1, 20))

        # Curriculum content - handle both formats
        if isinstance(curriculum.content, list):
            weeks = curriculum.content
        elif isinstance(curriculum.content, dict) and 'weeks' in curriculum.content:
            weeks = curriculum.content['weeks']
        else:
            weeks = []

        for week_data in weeks:
            week_title = Paragraph(f"<b>Week {week_data.get('week', 1)}: {week_data.get('title', '')}</b>", styles['Heading2'])
            story.append(week_title)
            story.append(Spacer(1, 6))

            description = Paragraph(f"<b>Description:</b> {week_data.get('description', '')}", styles['Normal'])
            story.append(description)
            story.append(Spacer(1, 6))

            # Videos
            if week_data.get('videos'):
                videos_title = Paragraph("<b>Videos:</b>", styles['Normal'])
                story.append(videos_title)
                for video in week_data['videos']:
                    video_item = Paragraph(f"• {video}", styles['Normal'])
                    story.append(video_item)
                story.append(Spacer(1, 6))

            # Tasks
            if week_data.get('tasks'):
                tasks_title = Paragraph("<b>Tasks:</b>", styles['Normal'])
                story.append(tasks_title)
                for i, task in enumerate(week_data['tasks']):
                    # Check if task is completed
                    progress = UserProgress.objects.filter(
                        user=request.user,
                        curriculum=curriculum,
                        week_number=week_data.get('week', 1),
                        task_index=i,
                        is_completed=True
                    ).exists()

                    status = "✓" if progress else "○"
                    task_item = Paragraph(f"• {status} {task}", styles['Normal'])
                    story.append(task_item)
                story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{curriculum.topic}_curriculum.pdf"'
        return response

    except Curriculum.DoesNotExist:
        return JsonResponse({'error': 'Curriculum not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def custom_password_reset(request):
    """Custom password reset that verifies email exists"""
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if email exists in database
        try:
            user = User.objects.get(email=email)
            # Only send reset email if user exists and is active
            if user.is_active:
                from django.contrib.auth.forms import PasswordResetForm
                form = PasswordResetForm({'email': email})
                if form.is_valid():
                    form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='registration/password_reset_email.html',
                        subject_template_name='registration/password_reset_subject.txt'
                    )
                messages.success(request, 'Password reset email sent successfully.')
            else:
                messages.error(request, 'Account is not activated. Please verify your email first.')
        except User.DoesNotExist:
            # Don't reveal that email doesn't exist for security
            messages.success(request, 'If an account with this email exists, a password reset link has been sent.')

        return redirect('login')

    return render(request, 'registration/password_reset_form.html')

@csrf_exempt
@login_required
def add_note(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            curriculum_id = data.get('curriculum_id')
            week_number = data.get('week_number')
            task_index = data.get('task_index')
            title = data.get('title')
            content = data.get('content')
            is_public = data.get('is_public', False)

            curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)

            note = UserNote.objects.create(
                user=request.user,
                curriculum=curriculum,
                week_number=week_number,
                task_index=task_index,
                title=title,
                content=content,
                is_public=is_public
            )

            # Award XP for note-taking
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.add_xp(5)  # 5 XP for creating a note

            # Award achievement for first note
            if not UserAchievement.objects.filter(user=request.user, achievement_type='FIRST_NOTE').exists():
                UserAchievement.objects.create(user=request.user, achievement_type='FIRST_NOTE')

            return JsonResponse({
                'success': True,
                'note_id': note.id,
                'xp_awarded': 5
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

@login_required
def get_notes(request, curriculum_id, week_number):
    try:
        curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)
        notes = UserNote.objects.filter(
            user=request.user,
            curriculum=curriculum,
            week_number=week_number
        ).order_by('-created_at')

        notes_data = [{
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'created_at': note.created_at.isoformat(),
            'is_public': note.is_public
        } for note in notes]

        return JsonResponse(notes_data, safe=False)

    except Curriculum.DoesNotExist:
        return JsonResponse({'error': 'Curriculum not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@login_required
def add_feedback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            curriculum_id = data.get('curriculum_id')
            rating = data.get('rating')
            difficulty_rating = data.get('difficulty_rating')
            feedback_text = data.get('feedback_text', '')
            would_recommend = data.get('would_recommend', True)
            is_anonymous = data.get('is_anonymous', False)

            curriculum = Curriculum.objects.get(id=curriculum_id, user=request.user)

            # Map difficulty rating numbers to choices
            difficulty_choices = {
                '1': 'too_easy',
                '2': 'easy',
                '3': 'just_right',
                '4': 'hard',
                '5': 'too_hard'
            }

            feedback, created = CurriculumFeedback.objects.update_or_create(
                user=request.user,
                curriculum=curriculum,
                defaults={
                    'rating': rating,
                    'difficulty_rating': difficulty_choices.get(str(difficulty_rating), 'just_right'),
                    'feedback_text': feedback_text,
                    'would_recommend': would_recommend,
                    'is_anonymous': is_anonymous
                }
            )

            # Award XP for providing feedback
            profile, created_profile = UserProfile.objects.get_or_create(user=request.user)
            profile.add_xp(10)  # 10 XP for providing feedback

            # Award achievement for first feedback
            if not UserAchievement.objects.filter(user=request.user, achievement_type='FIRST_FEEDBACK').exists():
                UserAchievement.objects.create(user=request.user, achievement_type='FIRST_FEEDBACK')

            return JsonResponse({
                'success': True,
                'feedback_id': feedback.id,
                'xp_awarded': 10
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

# Admin Authentication Views (Redirect to unified login)
def admin_login_view(request):
    """Redirect to unified login page"""
    messages.info(request, 'Please use your admin credentials to login.')
    return redirect('login')

def admin_logout_view(request):
    """Admin logout"""
    admin_logout(request)
    messages.success(request, 'Admin logged out successfully. You can login again below.')
    return redirect('login')

# Admin Views (Protected)
@admin_required
def admin_dashboard(request):
    """Admin dashboard with user management and analytics"""
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_curricula = Curriculum.objects.count()
    total_notes = UserNote.objects.count()
    total_feedback = CurriculumFeedback.objects.count()

    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_curricula = Curriculum.objects.order_by('-created_at')[:10]
    recent_feedback = CurriculumFeedback.objects.order_by('-created_at')[:10]

    # Popular topics
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
        'admin_user': request.admin_user,  # Pass admin user to template
    }

    return render(request, 'accounts/admin_dashboard.html', context)

@admin_required
def admin_users(request):
    """User management page"""
    users = User.objects.all().order_by('-date_joined')

    # Add user statistics
    for user in users:
        user.curriculum_count = Curriculum.objects.filter(user=user).count()
        user.notes_count = UserNote.objects.filter(user=user).count()
        user.feedback_count = CurriculumFeedback.objects.filter(user=user).count()
        try:
            user.profile = user.userprofile
        except:
            user.profile = None

    context = {'users': users, 'admin_user': request.admin_user}
    return render(request, 'accounts/admin_users.html', context)

@admin_required
def admin_curricula(request):
    """Curriculum management page"""
    curricula = Curriculum.objects.all().order_by('-created_at')

    # Add curriculum statistics
    for curriculum in curricula:
        curriculum.feedback_count = CurriculumFeedback.objects.filter(curriculum=curriculum).count()
        curriculum.notes_count = UserNote.objects.filter(curriculum=curriculum).count()
        curriculum.avg_rating = CurriculumFeedback.objects.filter(curriculum=curriculum).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']

    context = {'curricula': curricula, 'admin_user': request.admin_user}
    return render(request, 'accounts/admin_curricula.html', context)

@admin_required
def admin_feedback(request):
    """Feedback management page"""
    feedback = CurriculumFeedback.objects.all().order_by('-created_at')
    context = {'feedback': feedback, 'admin_user': request.admin_user}
    return render(request, 'accounts/admin_feedback.html', context)

@csrf_exempt
@admin_required
def admin_toggle_user_status(request):
    """Toggle user active status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()

            return JsonResponse({
                'success': True,
                'is_active': user.is_active,
                'message': f"User {'activated' if user.is_active else 'deactivated'} successfully"
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

@csrf_exempt
@admin_required
def admin_delete_user(request):
    """Delete user account and all associated data"""
    if request.method == 'POST':
        try:
            # Check if admin has delete permission
            if not request.admin_user.can_delete_users:
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to delete users. Contact a super admin.'
                }, status=403)

            data = json.loads(request.body)
            user_id = data.get('user_id')
            confirm_username = data.get('confirm_username', '')

            # Get the user to delete
            user = User.objects.get(id=user_id)

            # Security check: confirm username matches
            if confirm_username != user.username:
                return JsonResponse({
                    'success': False,
                    'error': 'Username confirmation does not match. Deletion cancelled for security.'
                }, status=400)

            # Prevent deletion of admin users (safety check)
            if AdminUser.objects.filter(email=user.email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete admin users through this interface.'
                }, status=400)

            # Store user info for response
            username = user.username
            email = user.email

            # Get counts of user data before deletion
            curricula_count = Curriculum.objects.filter(user=user).count()
            notes_count = UserNote.objects.filter(user=user).count()
            feedback_count = CurriculumFeedback.objects.filter(user=user).count()

            # Delete user (this will cascade delete related data due to foreign keys)
            user.delete()

            return JsonResponse({
                'success': True,
                'message': f'User "{username}" ({email}) has been permanently deleted.',
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

    return JsonResponse({'error': 'Only POST allowed'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('login')

# API Documentation - AI Curriculum Platform

## 🔐 **Authentication**

### **Unified Login System**
The platform uses a smart login system that automatically detects user type and routes appropriately.

#### **POST /** - Unified Login
**Description**: Single login endpoint for both students and admins

**Request Body**:
```json
{
    "username": "string",
    "password": "string"
}
```

**Response**:
- **Student Login**: Redirects to `/dashboard/`
- **Admin Login**: Redirects to `/admin-dashboard/`
- **Error**: Returns login page with error messages

**Authentication Flow**:
1. System first checks if credentials match an AdminUser
2. If admin match found, creates admin session and redirects to admin dashboard
3. If no admin match, tries regular Django user authentication
4. If regular user match found, creates user session and redirects to student dashboard
5. If no match found, returns error message

---

## 👤 **Student API Endpoints**

### **GET /dashboard/** - Student Dashboard
**Authentication**: Required (Student)
**Description**: Main student dashboard with curriculum history and statistics

**Response Data**:
```json
{
    "curricula": [
        {
            "id": 1,
            "topic": "Python Programming",
            "difficulty": "beginner",
            "duration": "4 weeks",
            "progress_percentage": 75.5,
            "created_at": "2025-01-01T10:00:00Z"
        }
    ],
    "profile": {
        "xp": 150,
        "level": 3,
        "study_streak": 7,
        "achievements_count": 5
    },
    "recent_achievements": [...]
}
```

### **POST /generate-curriculum/** - AI Curriculum Generation
**Authentication**: Required (Student)
**Description**: Generate personalized curriculum using Google Gemini AI

**Request Body**:
```json
{
    "topic": "Machine Learning",
    "difficulty": "intermediate",
    "duration": "6 weeks"
}
```

**Response**:
```json
{
    "success": true,
    "curriculum_id": 123,
    "redirect_url": "/curriculum/123/"
}
```

**Error Response**:
```json
{
    "success": false,
    "errors": ["Topic is required", "Invalid difficulty level"]
}
```

### **GET /curriculum/<id>/** - Curriculum Details
**Authentication**: Required (Student, Owner)
**Description**: View detailed curriculum with progress tracking

**Response Data**:
```json
{
    "curriculum": {
        "id": 123,
        "topic": "Machine Learning",
        "difficulty": "intermediate",
        "duration": "6 weeks",
        "content": {
            "weeks": [
                {
                    "week": 1,
                    "title": "Introduction to ML",
                    "description": "Basic concepts and terminology",
                    "tasks": [
                        {
                            "task": "Read about supervised learning",
                            "resources": ["Resource 1", "Resource 2"],
                            "videos": ["Video URL 1"]
                        }
                    ]
                }
            ]
        }
    },
    "progress_data": {
        "1": {
            "0": {"completed": true, "completed_at": "2025-01-01T10:00:00Z"}
        }
    },
    "notes": [...],
    "feedback": {...}
}
```

### **POST /update-progress/** - Update Task Progress
**Authentication**: Required (Student)
**Description**: Mark tasks as completed/incomplete

**Request Body**:
```json
{
    "curriculum_id": 123,
    "week_number": 1,
    "task_index": 0,
    "completed": true
}
```

**Response**:
```json
{
    "success": true,
    "progress_percentage": 25.0,
    "xp_awarded": 0
}
```

### **GET /download-pdf/<id>/** - Download Curriculum PDF
**Authentication**: Required (Student, Owner)
**Description**: Generate and download curriculum as PDF

**Response**: PDF file download

### **POST /save-note/** - Save User Notes
**Authentication**: Required (Student)
**Description**: Create or update notes for curriculum sections

**Request Body**:
```json
{
    "curriculum_id": 123,
    "week_number": 1,
    "task_index": 0,
    "title": "My Learning Notes",
    "content": "Detailed notes about the topic...",
    "is_public": false
}
```

**Response**:
```json
{
    "success": true,
    "note_id": 456,
    "xp_awarded": 5
}
```

### **POST /submit-feedback/** - Submit Curriculum Feedback
**Authentication**: Required (Student)
**Description**: Provide rating and feedback for curricula

**Request Body**:
```json
{
    "curriculum_id": 123,
    "rating": 5,
    "difficulty_rating": "just_right",
    "feedback_text": "Excellent curriculum!",
    "would_recommend": true,
    "is_anonymous": false
}
```

**Response**:
```json
{
    "success": true,
    "feedback_id": 789,
    "xp_awarded": 10
}
```

### **GET /profile/** - User Profile Management
**Authentication**: Required (Student)
**Description**: View and manage user profile settings

**Response Data**:
```json
{
    "user": {
        "username": "student123",
        "email": "student@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "profile": {
        "bio": "Learning enthusiast",
        "phone": "+1234567890",
        "location": "New York",
        "learning_style": "visual",
        "study_pace": "medium",
        "xp": 150,
        "level": 3,
        "study_streak": 7
    }
}
```

---

## 🛡️ **Admin API Endpoints**

### **GET /admin-dashboard/** - Admin Dashboard
**Authentication**: Required (Admin)
**Description**: Main admin dashboard with platform statistics

**Response Data**:
```json
{
    "statistics": {
        "total_users": 1250,
        "active_users": 1100,
        "total_curricula": 3500,
        "total_notes": 8900,
        "total_feedback": 2100
    },
    "recent_activity": {
        "recent_users": [...],
        "recent_curricula": [...],
        "recent_feedback": [...]
    },
    "popular_topics": [
        {"topic": "Python Programming", "count": 150},
        {"topic": "Machine Learning", "count": 120}
    ]
}
```

### **GET /admin-users/** - User Management
**Authentication**: Required (Admin)
**Description**: View and manage all platform users

**Response Data**:
```json
{
    "users": [
        {
            "id": 1,
            "username": "student123",
            "email": "student@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": true,
            "date_joined": "2025-01-01T10:00:00Z",
            "curriculum_count": 5,
            "notes_count": 12,
            "feedback_count": 3,
            "profile": {...}
        }
    ]
}
```

### **POST /admin-toggle-user/** - Toggle User Status
**Authentication**: Required (Admin)
**Description**: Activate or deactivate user accounts

**Request Body**:
```json
{
    "user_id": 123
}
```

**Response**:
```json
{
    "success": true,
    "is_active": false,
    "message": "User deactivated successfully"
}
```

### **POST /admin-delete-user/** - Delete User Account
**Authentication**: Required (Admin with delete permission)
**Description**: Permanently delete user and all associated data

**Request Body**:
```json
{
    "user_id": 123,
    "confirm_username": "student123"
}
```

**Response**:
```json
{
    "success": true,
    "message": "User \"student123\" deleted successfully.",
    "deleted_data": {
        "curricula": 5,
        "notes": 12,
        "feedback": 3
    }
}
```

**Error Responses**:
```json
{
    "success": false,
    "error": "You do not have permission to delete users."
}
```

### **GET /admin-curricula/** - Curriculum Management
**Authentication**: Required (Admin)
**Description**: View and manage all curricula on the platform

**Response Data**:
```json
{
    "curricula": [
        {
            "id": 1,
            "topic": "Python Programming",
            "user": "student123",
            "difficulty": "beginner",
            "created_at": "2025-01-01T10:00:00Z",
            "feedback_count": 5,
            "notes_count": 12,
            "avg_rating": 4.5
        }
    ]
}
```

### **GET /admin-feedback/** - Feedback Management
**Authentication**: Required (Admin)
**Description**: View and moderate user feedback

**Response Data**:
```json
{
    "feedback": [
        {
            "id": 1,
            "user": "student123",
            "curriculum": "Python Programming",
            "rating": 5,
            "difficulty_rating": "just_right",
            "feedback_text": "Great curriculum!",
            "would_recommend": true,
            "is_anonymous": false,
            "created_at": "2025-01-01T10:00:00Z"
        }
    ]
}
```

---

## 🔒 **Authentication & Security**

### **Session Management**

#### **Student Sessions**
- Uses Django's built-in session framework
- Standard session timeout (2 weeks by default)
- Session data stored in database

#### **Admin Sessions**
- Custom secure session system
- 8-hour session timeout
- IP address and user agent tracking
- Session key stored in AdminSession model

### **Security Features**

#### **Account Lockout**
- **Admin Accounts**: 5 failed attempts = 30-minute lockout
- **Regular Users**: Standard Django authentication

#### **Password Security**
- **Admin Passwords**: Custom hashing using Django's make_password
- **User Passwords**: Django's built-in password hashing

#### **CSRF Protection**
- All POST requests require CSRF tokens
- Automatic CSRF token generation in templates

#### **Permission System**
```python
# Admin Permissions
can_manage_users = True/False
can_delete_users = True/False  # Separate permission for deletion
can_manage_curricula = True/False
can_view_analytics = True/False
can_manage_admins = True/False  # Super admin only
```

---

## 📊 **Data Models & Relationships**

### **Entity Relationship Overview**
```
User (Django) ──┬── UserProfile (1:1)
                ├── Curriculum (1:N)
                ├── UserProgress (1:N)
                ├── UserNote (1:N)
                ├── CurriculumFeedback (1:N)
                └── UserAchievement (1:N)

AdminUser ──── AdminSession (1:N)

Curriculum ──┬── UserProgress (1:N)
             ├── UserNote (1:N)
             └── CurriculumFeedback (1:N)
```

### **JSON Data Structures**

#### **Curriculum Content Structure**
```json
{
    "weeks": [
        {
            "week": 1,
            "title": "Week Title",
            "description": "Week description",
            "tasks": [
                {
                    "task": "Learning task description",
                    "resources": [
                        "Resource URL or description",
                        "Another resource"
                    ],
                    "videos": [
                        "Video URL or search term",
                        "Another video"
                    ]
                }
            ]
        }
    ]
}
```

---

## 🎮 **Gamification API**

### **XP System**
- **Note Creation**: +5 XP
- **Feedback Submission**: +10 XP
- **Task Completion**: Variable XP based on difficulty

### **Level Calculation**
```python
def calculate_level(xp):
    return min(int(xp / 100) + 1, 50)  # Max level 50

def xp_for_next_level(current_level):
    return current_level * 100
```

### **Achievement Types**
- `FIRST_CURRICULUM` - Created first curriculum
- `FIRST_NOTE` - Created first note
- `FIRST_FEEDBACK` - Provided first feedback
- `STREAK_7` - 7-day study streak
- `LEVEL_5` - Reached level 5

---

## 🚨 **Error Handling**

### **Standard Error Responses**
```json
{
    "success": false,
    "error": "Error message description",
    "code": "ERROR_CODE"  // Optional error code
}
```

### **HTTP Status Codes**
- `200` - Success
- `302` - Redirect (for form submissions)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (not logged in)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `405` - Method Not Allowed
- `500` - Internal Server Error

### **Common Error Scenarios**
- **Invalid credentials**: Username/password mismatch
- **Account locked**: Too many failed login attempts
- **Permission denied**: Insufficient admin permissions
- **Validation errors**: Invalid form data
- **Not found**: Resource doesn't exist or user doesn't own it

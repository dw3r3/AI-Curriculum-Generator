#!/usr/bin/env python3
import os
import sys
import django
import json
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from accounts.models import Curriculum, User, UserProgress

def test_progress_request():
    print("=== Testing Progress Update Request ===")
    
    # Get the first curriculum
    try:
        curriculum = Curriculum.objects.first()
        if not curriculum:
            print("No curricula found in database!")
            return
        
        print(f"Testing curriculum: {curriculum.topic} (ID: {curriculum.id})")
        
        # Simulate the request data that the frontend sends
        request_data = {
            'curriculum_id': curriculum.id,
            'week_number': 1,
            'task_index': 0,
            'is_completed': True
        }
        
        print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        # Test the view logic directly
        from accounts.views import update_progress
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.post('/update_progress/', 
                             data=json.dumps(request_data),
                             content_type='application/json')
        request.user = curriculum.user
        
        # Call the view
        response = update_progress(request)
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        # Check if progress was updated
        curriculum.refresh_from_db()
        print(f"Updated progress: {curriculum.progress_percentage}%")
        
        # Check if UserProgress record was created
        progress_record = UserProgress.objects.filter(
            user=curriculum.user,
            curriculum=curriculum,
            week_number=1,
            task_index=0
        ).first()
        
        if progress_record:
            print(f"Progress record created: Week 1, Task 0 - {'✓' if progress_record.completed else '✗'}")
        else:
            print("No progress record found")
        
    except Exception as e:
        print(f"Error testing progress request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_progress_request()

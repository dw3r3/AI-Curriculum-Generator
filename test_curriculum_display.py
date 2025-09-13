#!/usr/bin/env python3
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from accounts.models import Curriculum, User

def test_curriculum_display():
    print("=== Testing Curriculum Display ===")
    
    # Get the first curriculum
    try:
        curriculum = Curriculum.objects.first()
        if not curriculum:
            print("No curricula found in database!")
            return
        
        print(f"Testing curriculum: {curriculum.topic}")
        print(f"Content type: {type(curriculum.content)}")
        
        # Test the content structure
        if isinstance(curriculum.content, dict):
            if 'weeks' in curriculum.content:
                weeks = curriculum.content['weeks']
                print(f"✓ Content has 'weeks' key with {len(weeks)} weeks")
                if weeks:
                    first_week = weeks[0]
                    print(f"First week structure: {json.dumps(first_week, indent=2)}")
            else:
                print("✗ Content is dict but no 'weeks' key found")
        elif isinstance(curriculum.content, list):
            print(f"✓ Content is list with {len(curriculum.content)} weeks")
            if curriculum.content:
                first_week = curriculum.content[0]
                print(f"First week structure: {json.dumps(first_week, indent=2)}")
        else:
            print(f"✗ Unexpected content type: {type(curriculum.content)}")
        
        # Test the get_curriculum_progress view logic
        print("\n=== Testing Progress View Logic ===")
        
        # Simulate the view logic
        if isinstance(curriculum.content, list):
            weeks = curriculum.content
        elif isinstance(curriculum.content, dict) and 'weeks' in curriculum.content:
            weeks = curriculum.content['weeks']
        else:
            weeks = []
        
        print(f"Extracted weeks: {len(weeks)}")
        if weeks:
            print(f"First week keys: {list(weeks[0].keys())}")
            
            # Check if tasks exist
            if 'tasks' in weeks[0]:
                tasks = weeks[0]['tasks']
                print(f"First week has {len(tasks)} tasks")
                if tasks:
                    print(f"First task type: {type(tasks[0])}")
                    print(f"First task: {tasks[0]}")
        
    except Exception as e:
        print(f"Error testing curriculum: {e}")

if __name__ == "__main__":
    test_curriculum_display()

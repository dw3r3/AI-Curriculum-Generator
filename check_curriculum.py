#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from accounts.models import Curriculum, User

def check_curriculum_data():
    print("=== Curriculum Database Check ===")
    
    # Check total curricula
    total_curricula = Curriculum.objects.count()
    print(f"Total curricula in database: {total_curricula}")
    
    if total_curricula == 0:
        print("No curricula found in database!")
        return
    
    # Check curricula by user
    for curriculum in Curriculum.objects.all()[:5]:
        print(f"\n--- Curriculum ID: {curriculum.id} ---")
        print(f"User: {curriculum.user.username}")
        print(f"Topic: {curriculum.topic}")
        print(f"Difficulty: {curriculum.difficulty}")
        print(f"Duration: {curriculum.duration}")
        print(f"Content type: {type(curriculum.content)}")
        print(f"Content preview: {str(curriculum.content)[:300]}...")
        
        # Check if content is valid JSON structure
        if isinstance(curriculum.content, dict):
            if 'weeks' in curriculum.content:
                weeks = curriculum.content['weeks']
                print(f"Number of weeks: {len(weeks)}")
                if weeks:
                    print(f"First week structure: {weeks[0]}")
            else:
                print("Content is dict but no 'weeks' key found")
        elif isinstance(curriculum.content, list):
            print(f"Content is list with {len(curriculum.content)} items")
            if curriculum.content:
                print(f"First item structure: {curriculum.content[0]}")
        else:
            print(f"Unexpected content type: {type(curriculum.content)}")

if __name__ == "__main__":
    check_curriculum_data()

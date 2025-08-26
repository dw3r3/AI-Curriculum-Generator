#!/usr/bin/env python3
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_curriculum.settings')
django.setup()

from accounts.models import Curriculum, User, UserProgress

def test_progress_update():
    print("=== Testing Progress Update ===")
    
    # Get the first curriculum
    try:
        curriculum = Curriculum.objects.first()
        if not curriculum:
            print("No curricula found in database!")
            return
        
        print(f"Testing curriculum: {curriculum.topic} (ID: {curriculum.id})")
        print(f"Current progress: {curriculum.progress_percentage}%")
        print(f"Total tasks: {curriculum.total_tasks}")
        print(f"Completed tasks: {curriculum.completed_tasks}")
        
        # Check existing progress records
        progress_records = UserProgress.objects.filter(curriculum=curriculum)
        print(f"Existing progress records: {progress_records.count()}")
        
        for record in progress_records[:5]:
            print(f"  Week {record.week_number}, Task {record.task_index}: {'✓' if record.completed else '✗'}")
        
        # Test creating a new progress record
        print("\n=== Testing Progress Creation ===")
        try:
            progress, created = UserProgress.objects.get_or_create(
                user=curriculum.user,
                curriculum=curriculum,
                week_number=1,
                task_index=0,
                defaults={'completed': True}
            )
            
            if created:
                print(f"✓ Created new progress record: Week 1, Task 0")
            else:
                print(f"✓ Found existing progress record: Week 1, Task 0")
                progress.completed = True
                progress.save()
            
            # Update curriculum progress
            curriculum.update_progress()
            print(f"Updated progress: {curriculum.progress_percentage}%")
            
        except Exception as e:
            print(f"✗ Error creating progress record: {e}")
        
    except Exception as e:
        print(f"Error testing progress: {e}")

if __name__ == "__main__":
    test_progress_update()

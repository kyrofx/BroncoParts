#!/usr/bin/env python3
"""
Test script to verify the first project sync logic.
This script will check the current projects and demonstrate which one would be considered the "first" project.
"""

import os
import sys

# Set environment variables before importing the app
os.environ['FLASK_ENV'] = 'development'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key'

# Add the current directory to Python path to import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Project, db

def test_first_project_logic():
    """Test which project would be considered the first project created."""
    try:
        app = create_app()
        print("App created successfully")
        
        with app.app_context():
            print("App context established")
            
            # Test database connection
            try:
                # Get all projects ordered by creation date
                all_projects = Project.query.order_by(Project.created_at.asc()).all()
                print(f"Database query successful. Found {len(all_projects)} projects.")
            except Exception as e:
                print(f"Database query failed: {e}")
                return
            
            print("=== Current Projects (ordered by creation date) ===")
            if not all_projects:
                print("No projects found in the database.")
                print("This means that when the first project is created, it will automatically sync to Airtable.")
                print("All subsequent projects will NOT sync to Airtable.")
                return
            
            for i, project in enumerate(all_projects):
                is_first = i == 0
                print(f"{'[FIRST]' if is_first else '[OTHER]'} ID: {project.id}, Name: '{project.name}', Created: {project.created_at}")
            
            # Get the first project (what our sync logic would use)
            first_project = Project.query.order_by(Project.created_at.asc()).first()
            
            print(f"\n=== Sync Logic Results ===")
            print(f"First project (will sync to Airtable): '{first_project.name}' (ID: {first_project.id})")
            print(f"All other projects will NOT sync to Airtable")
            
            # Simulate the logic for each project
            print(f"\n=== Simulation for each project ===")
            for project in all_projects:
                would_sync = project.id == first_project.id
                print(f"Project '{project.name}' (ID: {project.id}): {'WILL SYNC' if would_sync else 'WILL NOT SYNC'}")
                
    except Exception as e:
        print(f"Error in test_first_project_logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_first_project_logic()

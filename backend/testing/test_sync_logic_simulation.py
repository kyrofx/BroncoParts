#!/usr/bin/env python3
"""
Simple test to verify the first project sync logic without running the full Flask app.
This demonstrates the core logic we implemented.
"""

from datetime import datetime

class MockProject:
    """Mock Project class to simulate the database model."""
    def __init__(self, id, name, created_at):
        self.id = id
        self.name = name
        self.created_at = created_at

class MockPart:
    """Mock Part class to simulate a part."""
    def __init__(self, part_number, name, project_id, type='part'):
        self.part_number = part_number
        self.name = name
        self.project_id = project_id
        self.type = type

def simulate_first_project_sync_logic():
    """Simulate the sync logic we implemented in routes.py"""
    
    # Simulate some projects with different creation dates
    projects = [
        MockProject(1, "Project Alpha", datetime(2025, 1, 1, 10, 0, 0)),
        MockProject(2, "Project Beta", datetime(2025, 1, 2, 10, 0, 0)),
        MockProject(3, "Project Gamma", datetime(2025, 1, 3, 10, 0, 0)),
    ]
    
    # Sort by creation date (ascending) to find the first one
    projects_by_date = sorted(projects, key=lambda p: p.created_at)
    first_project = projects_by_date[0] if projects_by_date else None
    
    print("=== Simulated Projects (ordered by creation date) ===")
    for i, project in enumerate(projects_by_date):
        is_first = i == 0
        print(f"{'[FIRST]' if is_first else '[OTHER]'} ID: {project.id}, Name: '{project.name}', Created: {project.created_at}")
    
    print(f"\n=== Sync Logic Results ===")
    if first_project:
        print(f"First project (will sync to Airtable): '{first_project.name}' (ID: {first_project.id})")
        print(f"All other projects will NOT sync to Airtable")
    else:
        print("No projects found - first project created will sync to Airtable")
    
    # Test our sync logic with sample parts
    test_parts = [
        MockPart("P001", "Test Part 1", 1),  # From first project - should sync
        MockPart("P002", "Test Part 2", 2),  # From second project - should NOT sync
        MockPart("P003", "Test Part 3", 1),  # From first project - should sync
        MockPart("A001", "Test Assembly", 3, type='assembly'),  # Assembly - should not sync regardless
    ]
    
    print(f"\n=== Part Sync Simulation ===")
    for part in test_parts:
        # This is the exact logic we implemented in routes.py
        if part.type.lower() == 'part':
            if first_project and part.project_id == first_project.id:
                print(f"✅ WILL SYNC: Part {part.part_number} ({part.name}) - belongs to first project")
            else:
                print(f"❌ WILL NOT SYNC: Part {part.part_number} ({part.name}) - not from first project")
        elif part.type.lower() == 'assembly':
            print(f"⚙️  SKIPPED: Assembly {part.part_number} ({part.name}) - assemblies don't sync")
    
    return first_project

if __name__ == '__main__':
    print("=== Testing First Project Sync Logic ===\n")
    simulate_first_project_sync_logic()
    print("\n=== Summary ===")
    print("✅ Only parts from the FIRST project created will sync to Airtable")
    print("❌ Parts from all other projects will be skipped")
    print("⚙️  Assemblies never sync to Airtable (existing behavior)")

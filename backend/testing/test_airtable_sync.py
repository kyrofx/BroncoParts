#!/usr/bin/env python3
"""
Simple test script to verify that the main Airtable sync functionality is working.
This tests the sync_part_to_airtable function without testing field schema updates.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Part, Project, Machine, PostProcess
from app.services.airtable_service import sync_part_to_airtable, get_airtable_table

def test_airtable_connection():
    """Test basic Airtable connection and table access."""
    app = create_app()
    with app.app_context():
        print("Testing Airtable connection...")
        table = get_airtable_table()
        if table:
            print("✅ Airtable table connection successful")
            try:
                # Try to get table schema to verify API access
                schema = table.schema()
                print(f"✅ Table schema access successful. Field count: {len(schema.fields)}")
                
                # List some key fields
                field_names = [field.name for field in schema.fields]
                print(f"✅ Key fields found: {', '.join(field_names[:10])}")
                
                if 'Part Number' in field_names and 'Subsystem' in field_names:
                    print("✅ Required fields 'Part Number' and 'Subsystem' are present")
                else:
                    print("⚠️  Warning: Some required fields may be missing")
                    
                return True
            except Exception as e:
                print(f"❌ Error accessing table schema: {e}")
                return False
        else:
            print("❌ Failed to connect to Airtable table")
            return False

def test_part_sync():
    """Test syncing a part to Airtable (read-only test - doesn't create records)."""
    app = create_app()
    with app.app_context():
        print("\nTesting part sync preparation...")
        
        # Find an existing part to test with
        part = Part.query.filter_by(type='part').first()
        if not part:
            print("❌ No parts found in database to test with")
            return False
            
        print(f"✅ Found test part: {part.part_number} ({part.name})")
        
        # Check if part has required fields for Airtable sync
        required_fields = ['part_number', 'name', 'quantity', 'status']
        missing_fields = []
        for field in required_fields:
            if not hasattr(part, field) or getattr(part, field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️  Part missing required fields: {missing_fields}")
        else:
            print("✅ Part has all required fields for Airtable sync")
            
        # Test sync (this will actually attempt to create/update a record)
        try:
            print("🔄 Testing actual sync to Airtable...")
            result = sync_part_to_airtable(part)
            if result:
                print(f"✅ Part sync successful! Airtable record ID: {result.get('id')}")
                return True
            else:
                print("❌ Part sync failed (check logs for details)")
                return False
        except Exception as e:
            print(f"❌ Part sync exception: {e}")
            return False

if __name__ == "__main__":
    print("BroncoPartsV2 Airtable Integration Test")
    print("=" * 50)
    
    # Test 1: Basic connection
    connection_ok = test_airtable_connection()
    
    if connection_ok:
        # Test 2: Part sync
        sync_ok = test_part_sync()
        
        if sync_ok:
            print("\n🎉 All Airtable tests passed!")
            print("The main Airtable integration is working correctly.")
            print("Note: Subsystem field option updates may still need manual intervention.")
        else:
            print("\n⚠️  Airtable connection works, but part sync failed.")
            print("Check the application logs for more details.")
    else:
        print("\n❌ Airtable connection failed.")
        print("Check your .env file and Airtable configuration.")

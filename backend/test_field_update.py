#!/usr/bin/env python3
"""
Test script to specifically test the Airtable field choice update functionality.
This will attempt to add a test option to the Subsystem field.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.services.airtable_service import add_option_to_airtable_subsystem_field, get_airtable_table

def test_field_update():
    """Test adding a new option to the Subsystem field."""
    app = create_app()
    with app.app_context():
        print("Testing Airtable field choice update...")
        
        # Test connection first
        table = get_airtable_table()
        if not table:
            print("❌ Failed to connect to Airtable table")
            return False
            
        print("✅ Airtable connection successful")
        
        # Try to add a test option
        test_option = "Test Assembly 2024"
        print(f"🔄 Attempting to add test option: '{test_option}'")
        
        try:
            result = add_option_to_airtable_subsystem_field(test_option)
            if result:
                print(f"✅ Successfully added '{test_option}' to Subsystem field")
                return True
            else:
                print(f"⚠️  Field update returned False - check logs for details")
                print("This may be expected if manual intervention is required")
                return False
        except Exception as e:
            print(f"❌ Error during field update: {e}")
            return False

if __name__ == "__main__":
    success = test_field_update()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n⚠️  Test completed with warnings - check application logs")

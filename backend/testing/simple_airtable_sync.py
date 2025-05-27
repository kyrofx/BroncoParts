#!/usr/bin/env python3
"""
Simple Airtable Sync Script for Machines and Post Processes
"""

import os
import sys

# Load environment variables from .env file
env_file = '../.env'
if os.path.exists(env_file):
    print('✅ Loading environment variables from .env file')
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ[key] = value
else:
    print('⚠️ .env file not found, using existing environment variables')

# Set Flask environment variables
os.environ['FLASK_ENV'] = 'development'
if not os.environ.get('JWT_SECRET_KEY'):
    os.environ['JWT_SECRET_KEY'] = 'sync-script-secret-key'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_airtable_connection():
    """Test connection to Airtable and display schema."""
    try:
        from app import create_app
        from pyairtable import Table
        
        app = create_app()
        print("✅ Flask app created successfully")
        
        with app.app_context():
            # Get Airtable configuration
            api_key = app.config.get('AIRTABLE_API_KEY')
            base_id = app.config.get('AIRTABLE_BASE_ID')
            table_id = app.config.get('AIRTABLE_TABLE_ID')
            
            print(f"📋 Airtable Base ID: {base_id}")
            print(f"📋 Airtable Table ID: {table_id}")
            print(f"🔑 API Key configured: {bool(api_key)}")
            
            if not all([api_key, base_id, table_id]):
                print("❌ Airtable configuration incomplete")
                return False
            
            # Connect to Airtable
            table = Table(api_key, base_id, table_id)
            print("✅ Connected to Airtable")
            
            # Get schema
            schema = table.schema()
            print(f"\n📊 Table Schema:")
            print(f"Name: {schema.name}")
            print(f"ID: {schema.id}")
            
            print(f"\nFields:")
            machine_field = None
            post_process_field = None
            
            for field in schema.fields:
                field_info = f"  - {field.name} ({field.type})"
                
                # Check for choices/options
                if hasattr(field, 'options') and field.options:
                    if hasattr(field.options, 'choices') and field.options.choices:
                        choices = [choice.name for choice in field.options.choices]
                        field_info += f" - Choices: {choices}"
                        
                        # Look for machine and post process fields
                        field_name_lower = field.name.lower()
                        if any(keyword in field_name_lower for keyword in ['machine', 'tool']):
                            machine_field = field
                            field_info += " 🔧 [DETECTED AS MACHINE FIELD]"
                        elif any(keyword in field_name_lower for keyword in ['post-process', 'post_process', 'process']):
                            post_process_field = field
                            field_info += " ⚙️ [DETECTED AS POST-PROCESS FIELD]"
                
                print(field_info)
            
            # Extract data
            print(f"\n🔧 Machine Field Analysis:")
            if machine_field:
                print(f"Field: {machine_field.name}")
                if hasattr(machine_field.options, 'choices'):
                    machines = [choice.name for choice in machine_field.options.choices]
                    print(f"Available machines: {machines}")
                else:
                    print("No choices found")
            else:
                print("No machine field detected")
            
            print(f"\n⚙️ Post Process Field Analysis:")
            if post_process_field:
                print(f"Field: {post_process_field.name}")
                if hasattr(post_process_field.options, 'choices'):
                    post_processes = [choice.name for choice in post_process_field.options.choices]
                    print(f"Available post processes: {post_processes}")
                else:
                    print("No choices found")
            else:
                print("No post process field detected")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def sync_to_database():
    """Sync machines and post processes to database."""
    try:
        from app import create_app
        from app.models import db, Machine, PostProcess
        from pyairtable import Table
        
        app = create_app()
        
        with app.app_context():
            # Get current database state
            current_machines = Machine.query.all()
            current_post_processes = PostProcess.query.all()
            
            print(f"\n📊 Current Database State:")
            print(f"Machines: {[m.name for m in current_machines]}")
            print(f"Post Processes: {[pp.name for pp in current_post_processes]}")
            
            # Get Airtable data
            api_key = app.config.get('AIRTABLE_API_KEY')
            base_id = app.config.get('AIRTABLE_BASE_ID')
            table_id = app.config.get('AIRTABLE_TABLE_ID')
            
            table = Table(api_key, base_id, table_id)
            schema = table.schema()
            
            # Find machine and post process fields
            machine_choices = []
            post_process_choices = []
            
            for field in schema.fields:
                if hasattr(field, 'options') and field.options and hasattr(field.options, 'choices'):
                    field_name_lower = field.name.lower()
                    
                    if any(keyword in field_name_lower for keyword in ['machine', 'tool']):
                        machine_choices = [choice.name for choice in field.options.choices]
                        print(f"🔧 Found machines in field '{field.name}': {machine_choices}")
                    
                    elif any(keyword in field_name_lower for keyword in ['post-process', 'post_process', 'process']):
                        post_process_choices = [choice.name for choice in field.options.choices]
                        print(f"⚙️ Found post processes in field '{field.name}': {post_process_choices}")
            
            # Sync machines
            if machine_choices:
                print(f"\n🔧 Syncing machines...")
                for machine_name in machine_choices:
                    existing = Machine.query.filter_by(name=machine_name).first()
                    if not existing:
                        new_machine = Machine(name=machine_name)
                        db.session.add(new_machine)
                        print(f"  ✅ Added machine: {machine_name}")
                    else:
                        print(f"  ℹ️ Machine already exists: {machine_name}")
            
            # Sync post processes
            if post_process_choices:
                print(f"\n⚙️ Syncing post processes...")
                for pp_name in post_process_choices:
                    existing = PostProcess.query.filter_by(name=pp_name).first()
                    if not existing:
                        new_pp = PostProcess(name=pp_name)
                        db.session.add(new_pp)
                        print(f"  ✅ Added post process: {pp_name}")
                    else:
                        print(f"  ℹ️ Post process already exists: {pp_name}")
            
            # Commit changes
            db.session.commit()
            print(f"\n💾 Changes committed to database")
            
            # Show final state
            final_machines = Machine.query.all()
            final_post_processes = PostProcess.query.all()
            
            print(f"\n📊 Final Database State:")
            print(f"Machines: {[m.name for m in final_machines]}")
            print(f"Post Processes: {[pp.name for pp in final_post_processes]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Sync error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Airtable Sync Test")
    print("="*50)
    
    # Test connection and show schema
    if test_airtable_connection():
        print("\n" + "="*50)
        
        # Ask user if they want to proceed with sync
        response = input("\nDo you want to proceed with syncing to database? (y/n): ")
        if response.lower() in ['y', 'yes']:
            sync_to_database()
        else:
            print("Sync cancelled by user")
    else:
        print("❌ Connection test failed")

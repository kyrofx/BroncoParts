#!/usr/bin/env python3
"""
Airtable Sync Script for Machines and Post Processes

This script manually syncs machines and post processes from Airtable to the local database.
It assumes that Airtable has separate tables or fields containing this information.

Usage:
    python3 sync_from_airtable.py [--dry-run] [--machines-only] [--post-processes-only]

Options:
    --dry-run              Show what would be changed without making actual changes
    --machines-only        Only sync machines
    --post-processes-only  Only sync post processes
"""

import os
import sys
import argparse
from datetime import datetime

# Set environment variables before importing the app
os.environ['FLASK_ENV'] = 'development'
if not os.environ.get('JWT_SECRET_KEY'):
    os.environ['JWT_SECRET_KEY'] = 'sync-script-secret-key'

# Add the current directory to Python path to import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from app.models import db, Machine, PostProcess
    from pyairtable import Table
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the backend directory")
    print("and that all dependencies are installed.")
    sys.exit(1)

class AirtableSyncManager:
    """Manages synchronization of machines and post processes from Airtable."""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.app = None
        self.machines_table = None
        self.post_processes_table = None
        self.stats = {
            'machines_created': 0,
            'machines_updated': 0,
            'machines_unchanged': 0,
            'post_processes_created': 0,
            'post_processes_updated': 0,
            'post_processes_unchanged': 0,
            'errors': []
        }
    
    def initialize_app(self):
        """Initialize Flask app and Airtable connections."""
        try:
            self.app = create_app()
            print("✅ Flask app initialized successfully")
            
            with self.app.app_context():
                # Get Airtable configuration
                api_key = self.app.config.get('AIRTABLE_API_KEY')
                base_id = self.app.config.get('AIRTABLE_BASE_ID')
                table_id = self.app.config.get('AIRTABLE_TABLE_ID')
                
                if not all([api_key, base_id]):
                    raise ValueError("Airtable API_KEY and BASE_ID must be configured")
                
                print(f"📋 Airtable Base ID: {base_id}")
                print(f"🔑 API Key configured: {bool(api_key)}")
                
                # For this script, we'll assume machines and post processes are either:
                # 1. In separate tables (ideal)
                # 2. In the main parts table as field options
                # 3. In dedicated columns that we need to extract unique values from
                
                # Try to connect to the main table first
                self.main_table = Table(api_key, base_id, table_id)
                print(f"✅ Connected to main Airtable table")
                
                return True
                
        except Exception as e:
            print(f"❌ Error initializing app: {e}")
            self.stats['errors'].append(f"App initialization: {e}")
            return False
    
    def get_airtable_schema(self):
        """Get the schema of the Airtable table to understand available fields."""
        try:
            with self.app.app_context():
                schema = self.main_table.schema()
                print(f"\n📊 Airtable Table Schema:")
                print(f"Table Name: {schema.name}")
                print(f"Table ID: {schema.id}")
                print(f"\nFields:")
                
                machine_field = None
                post_process_field = None
                
                for field in schema.fields:
                    print(f"  - {field.name} ({field.type})")
                    if hasattr(field, 'options') and field.options and hasattr(field.options, 'choices'):
                        print(f"    Choices: {[choice.name for choice in field.options.choices]}")
                    
                    # Look for machine and post process fields
                    if field.name.lower() in ['machine', 'machines', 'tool', 'tools']:
                        machine_field = field
                    elif field.name.lower() in ['post-process', 'post_process', 'post processes', 'post-processes']:
                        post_process_field = field
                
                return machine_field, post_process_field
                
        except Exception as e:
            print(f"❌ Error getting Airtable schema: {e}")
            self.stats['errors'].append(f"Schema fetch: {e}")
            return None, None
    
    def extract_machines_from_airtable(self, machine_field):
        """Extract machine options from Airtable field choices."""
        machines = []
        
        if not machine_field:
            print("⚠️  No machine field found in Airtable schema")
            return machines
        
        try:
            if (hasattr(machine_field, 'options') and 
                machine_field.options and 
                hasattr(machine_field.options, 'choices')):
                
                for choice in machine_field.options.choices:
                    machines.append({
                        'name': choice.name,
                        'airtable_id': getattr(choice, 'id', None)
                    })
                
                print(f"📋 Found {len(machines)} machines in Airtable:")
                for machine in machines:
                    print(f"  - {machine['name']}")
            else:
                print("⚠️  Machine field has no choices/options")
                
        except Exception as e:
            print(f"❌ Error extracting machines: {e}")
            self.stats['errors'].append(f"Machine extraction: {e}")
        
        return machines
    
    def extract_post_processes_from_airtable(self, post_process_field):
        """Extract post process options from Airtable field choices."""
        post_processes = []
        
        if not post_process_field:
            print("⚠️  No post process field found in Airtable schema")
            return post_processes
        
        try:
            if (hasattr(post_process_field, 'options') and 
                post_process_field.options and 
                hasattr(post_process_field.options, 'choices')):
                
                for choice in post_process_field.options.choices:
                    post_processes.append({
                        'name': choice.name,
                        'airtable_id': getattr(choice, 'id', None)
                    })
                
                print(f"📋 Found {len(post_processes)} post processes in Airtable:")
                for pp in post_processes:
                    print(f"  - {pp['name']}")
            else:
                print("⚠️  Post process field has no choices/options")
                
        except Exception as e:
            print(f"❌ Error extracting post processes: {e}")
            self.stats['errors'].append(f"Post process extraction: {e}")
        
        return post_processes
    
    def sync_machines(self, airtable_machines):
        """Sync machines from Airtable to local database."""
        if not airtable_machines:
            print("📋 No machines to sync")
            return
        
        print(f"\n🔧 Syncing {len(airtable_machines)} machines...")
        
        with self.app.app_context():
            for machine_data in airtable_machines:
                try:
                    machine_name = machine_data['name'].strip()
                    if not machine_name:
                        continue
                    
                    # Check if machine already exists
                    existing_machine = Machine.query.filter_by(name=machine_name).first()
                    
                    if existing_machine:
                        print(f"  ℹ️  Machine '{machine_name}' already exists (unchanged)")
                        self.stats['machines_unchanged'] += 1
                    else:
                        if self.dry_run:
                            print(f"  🔍 [DRY RUN] Would create machine: '{machine_name}'")
                        else:
                            new_machine = Machine(name=machine_name)
                            db.session.add(new_machine)
                            print(f"  ✅ Created machine: '{machine_name}'")
                        self.stats['machines_created'] += 1
                
                except Exception as e:
                    error_msg = f"Error syncing machine '{machine_data.get('name', 'Unknown')}': {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
            
            if not self.dry_run:
                try:
                    db.session.commit()
                    print(f"  💾 Committed machine changes to database")
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"Error committing machine changes: {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
    
    def sync_post_processes(self, airtable_post_processes):
        """Sync post processes from Airtable to local database."""
        if not airtable_post_processes:
            print("📋 No post processes to sync")
            return
        
        print(f"\n⚙️  Syncing {len(airtable_post_processes)} post processes...")
        
        with self.app.app_context():
            for pp_data in airtable_post_processes:
                try:
                    pp_name = pp_data['name'].strip()
                    if not pp_name:
                        continue
                    
                    # Check if post process already exists
                    existing_pp = PostProcess.query.filter_by(name=pp_name).first()
                    
                    if existing_pp:
                        print(f"  ℹ️  Post process '{pp_name}' already exists (unchanged)")
                        self.stats['post_processes_unchanged'] += 1
                    else:
                        if self.dry_run:
                            print(f"  🔍 [DRY RUN] Would create post process: '{pp_name}'")
                        else:
                            new_pp = PostProcess(name=pp_name)
                            db.session.add(new_pp)
                            print(f"  ✅ Created post process: '{pp_name}'")
                        self.stats['post_processes_created'] += 1
                
                except Exception as e:
                    error_msg = f"Error syncing post process '{pp_data.get('name', 'Unknown')}': {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
            
            if not self.dry_run:
                try:
                    db.session.commit()
                    print(f"  💾 Committed post process changes to database")
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"Error committing post process changes: {e}"
                    print(f"  ❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
    
    def display_current_database_state(self):
        """Display current machines and post processes in the database."""
        print(f"\n📊 Current Database State:")
        
        with self.app.app_context():
            machines = Machine.query.order_by(Machine.name).all()
            post_processes = PostProcess.query.order_by(PostProcess.name).all()
            
            print(f"\n🔧 Machines ({len(machines)}):")
            for machine in machines:
                print(f"  - {machine.name} (ID: {machine.id})")
            
            print(f"\n⚙️  Post Processes ({len(post_processes)}):")
            for pp in post_processes:
                print(f"  - {pp.name} (ID: {pp.id})")
    
    def print_summary(self):
        """Print sync summary statistics."""
        print(f"\n📊 Sync Summary:")
        print(f"{'='*50}")
        
        print(f"🔧 Machines:")
        print(f"  Created: {self.stats['machines_created']}")
        print(f"  Updated: {self.stats['machines_updated']}")
        print(f"  Unchanged: {self.stats['machines_unchanged']}")
        
        print(f"\n⚙️  Post Processes:")
        print(f"  Created: {self.stats['post_processes_created']}")
        print(f"  Updated: {self.stats['post_processes_updated']}")
        print(f"  Unchanged: {self.stats['post_processes_unchanged']}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        total_changes = (self.stats['machines_created'] + self.stats['machines_updated'] + 
                        self.stats['post_processes_created'] + self.stats['post_processes_updated'])
        
        if total_changes > 0:
            print(f"\n✅ Sync completed with {total_changes} changes")
        else:
            print(f"\n✅ Sync completed - no changes needed")
        
        if self.dry_run:
            print(f"\n🔍 This was a DRY RUN - no actual changes were made")
    
    def run_sync(self, sync_machines=True, sync_post_processes=True):
        """Run the complete sync process."""
        print(f"🚀 Starting Airtable Sync...")
        print(f"🔍 Dry run mode: {self.dry_run}")
        print(f"🔧 Sync machines: {sync_machines}")
        print(f"⚙️  Sync post processes: {sync_post_processes}")
        
        if not self.initialize_app():
            return False
        
        # Show current state
        self.display_current_database_state()
        
        # Get Airtable schema and fields
        machine_field, post_process_field = self.get_airtable_schema()
        
        # Extract data from Airtable
        airtable_machines = []
        airtable_post_processes = []
        
        if sync_machines:
            airtable_machines = self.extract_machines_from_airtable(machine_field)
        
        if sync_post_processes:
            airtable_post_processes = self.extract_post_processes_from_airtable(post_process_field)
        
        # Perform sync
        if sync_machines:
            self.sync_machines(airtable_machines)
        
        if sync_post_processes:
            self.sync_post_processes(airtable_post_processes)
        
        # Show final state
        if not self.dry_run:
            self.display_current_database_state()
        
        # Print summary
        self.print_summary()
        
        return len(self.stats['errors']) == 0

def main():
    """Main function to handle command line arguments and run sync."""
    parser = argparse.ArgumentParser(
        description='Sync machines and post processes from Airtable to local database'
    )
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without making actual changes')
    parser.add_argument('--machines-only', action='store_true',
                       help='Only sync machines')
    parser.add_argument('--post-processes-only', action='store_true',
                       help='Only sync post processes')
    
    args = parser.parse_args()
    
    # Determine what to sync
    if args.machines_only and args.post_processes_only:
        print("❌ Cannot specify both --machines-only and --post-processes-only")
        sys.exit(1)
    
    sync_machines = not args.post_processes_only
    sync_post_processes = not args.machines_only
    
    # Run sync
    sync_manager = AirtableSyncManager(dry_run=args.dry_run)
    success = sync_manager.run_sync(sync_machines, sync_post_processes)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

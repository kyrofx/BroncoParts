from pyairtable import Table
from pyairtable.exceptions import PyAirtableError
from flask import current_app
from ..models import Part # Corrected import
import requests # Import requests for more specific error handling
import json

# Airtable Column Name Constants (as per feature_part_creation_enhancements.md)
AIRTABLE_NAME = "Name"
AIRTABLE_SUBTEAM = "Subteam"
AIRTABLE_SUBSYSTEM = "Subsystem"
AIRTABLE_MANUFACTURING_QUANTITY = "Manufacturing Quantity"
AIRTABLE_STATUS = "Status"
AIRTABLE_MACHINE = "Machine"
AIRTABLE_RAW_MATERIAL = "Raw material"
AIRTABLE_POST_PROCESS = "Processes"
AIRTABLE_NOTES = "Notes"
# Add any other constants if needed, e.g., for fields not explicitly listed for disregard but still synced
# AIRTABLE_PART_NUMBER = "Part Number" # Example, if you decide to sync it despite "disregard" note

# Helper function to update Airtable field choices via Metadata API
def _update_airtable_field_choices(table: Table, field_name_to_update: str, new_choice_name: str, project=None) -> bool:
    api_key, base_id, _ = _get_airtable_config(project)
    # table.name should be the table ID or name used when initializing the pyairtable.Table object
    table_id_or_name = table.name 

    current_app.logger.info(f"Starting Airtable field choice update. API Key configured: {bool(api_key)}, Base ID: {base_id}, Table ID/Name: {table_id_or_name}")

    if not all([api_key, base_id, table_id_or_name]):
        current_app.logger.error("Airtable API Key, Base ID, or Table ID/Name not configured for schema update.")
        return False
    if api_key == 'YOUR_AIRTABLE_API_KEY': # Check for placeholder
        current_app.logger.error("Airtable API Key is a placeholder. Metadata API calls will fail. Please use a valid Personal Access Token.")
        return False

    field_id = None
    current_choices_payload = []
    field_type = None

    try:
        table_schema = table.schema()
        for schema_field in table_schema.fields:
            if schema_field.name == field_name_to_update:
                field_id = schema_field.id
                field_type = schema_field.type
                if field_type not in ["singleSelect", "multipleSelects"]:
                    current_app.logger.error(f"Field '{field_name_to_update}' in Airtable is not a select field (type: {field_type}). Cannot update choices.")
                    return False
                if schema_field.options and schema_field.options.choices:
                    for choice in schema_field.options.choices:
                        choice_data = {"name": choice.name}
                        # Preserve existing ID and color as per Airtable Metadata API docs
                        if hasattr(choice, 'id') and choice.id:
                            choice_data["id"] = choice.id
                        if hasattr(choice, 'color') and choice.color: # choice.color is already a string according to API docs
                            choice_data["color"] = choice.color 
                        current_choices_payload.append(choice_data)
                break
        
        if not field_id:
            current_app.logger.error(f"Field '{field_name_to_update}' not found in Airtable table schema.")
            return False

    except Exception as e:
        current_app.logger.error(f"Error fetching Airtable schema for field '{field_name_to_update}': {e}", exc_info=True)
        return False

    # Check if new_choice_name already exists
    if any(choice['name'] == new_choice_name for choice in current_choices_payload):
        current_app.logger.info(f"Choice '{new_choice_name}' already exists in Airtable field '{field_name_to_update}'. No update needed.")
        return True

    # Check if we're approaching Airtable's choice limit (typically 50-100 choices max)
    if len(current_choices_payload) >= 45:  # Conservative limit to avoid issues
        current_app.logger.warning(f"Field '{field_name_to_update}' already has {len(current_choices_payload)} choices. "
                                  f"Approaching Airtable's choice limit. Skipping automatic update.")
        log_manual_airtable_instructions(new_choice_name, field_name_to_update)
        return False

    # Validate the new choice name
    if not new_choice_name or len(new_choice_name.strip()) == 0:
        current_app.logger.error(f"Invalid choice name: empty or whitespace only")
        return False
    
    # Trim whitespace and limit length to reasonable bounds
    clean_choice_name = new_choice_name.strip()[:100]  # Reasonable length limit
    
    # Add the new choice to the existing choices
    current_choices_payload.append({"name": clean_choice_name})
    
    # Airtable Metadata API endpoint for updating field schema
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id_or_name}/fields/{field_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload using the proper metadata API format for single select fields
    payload = {
        "type": field_type,
        "options": {
            "choices": current_choices_payload
        }
    }
    current_app.logger.info(f"Attempting to add new option '{clean_choice_name}' to Airtable field '{field_name_to_update}' using metadata API.")
    current_app.logger.info(f"URL: {url}")
    current_app.logger.info(f"Request payload: {payload}")
    current_app.logger.info(f"Total choices after update: {len(current_choices_payload)}")

    try:
        response = requests.patch(url, headers=headers, json=payload)
        current_app.logger.info(f"HTTP Response status: {response.status_code}")
        
        # Log response content regardless of success/failure
        try:
            response_json = response.json()
            current_app.logger.info(f"HTTP Response JSON: {response_json}")
        except ValueError:
            current_app.logger.info(f"HTTP Response text: {response.text}")
        
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        current_app.logger.info(f"Successfully added '{clean_choice_name}' to field '{field_name_to_update}' in Airtable.")
        return True
    except requests.exceptions.HTTPError as e_http:
        error_details = "No response content"
        if e_http.response is not None:
            try:
                error_details = e_http.response.json()
            except ValueError: # If response is not JSON
                error_details = e_http.response.text
        current_app.logger.error(f"HTTPError adding option to Airtable field '{field_name_to_update}': {e_http}. Response: {error_details}")
        
        # Try to provide more helpful error context
        if e_http.response and e_http.response.status_code == 422:
            current_app.logger.error(f"422 Error Analysis:")
            current_app.logger.error(f"  - Field '{field_name_to_update}' may be read-only or have restrictions")
            current_app.logger.error(f"  - Manual action required: Add '{clean_choice_name}' to the '{field_name_to_update}' field options in Airtable interface")
        
        return False
    except Exception as e:
        current_app.logger.error(f"Generic error adding option to Airtable field '{field_name_to_update}': {e}", exc_info=True)
        return False

# New public function to be called from routes.py
def add_option_to_airtable_subsystem_field(new_option_name: str, project=None) -> bool:
    """
    Attempts to add a new option to the Airtable Subsystem field.
    
    Note: This operation may fail due to Airtable field restrictions, permissions,
    or limits. In such cases, the option must be manually added in the Airtable interface.
    
    Args:
        new_option_name (str): The name of the new subsystem option to add
        
    Returns:
        bool: True if successful, False if failed (but this doesn't prevent part creation)
    """
    # First try the proven typecast approach
    current_app.logger.info(f"Attempting to add option '{new_option_name}' to Airtable Subsystem field using typecast method")
    result = add_option_via_typecast(new_option_name, AIRTABLE_SUBSYSTEM, project=project)
    
    if result:
        current_app.logger.info(f"Successfully added option '{new_option_name}' using typecast method")
        return True
    
    # Fallback to the metadata API approach if typecast fails
    current_app.logger.warning(f"Typecast method failed for '{new_option_name}', trying metadata API approach")
    
    table = get_airtable_table(project)
    if not table:
        current_app.logger.error("Airtable table not initialized. Cannot add subsystem option.")
        log_manual_airtable_instructions(new_option_name, AIRTABLE_SUBSYSTEM)
        return False
    
    try:
        # AIRTABLE_SUBSYSTEM is "Subsystem"
        result = _update_airtable_field_choices(table, AIRTABLE_SUBSYSTEM, new_option_name, project)
        if not result:
            current_app.logger.warning(f"Could not automatically add '{new_option_name}' to Airtable Subsystem field using either method.")
            log_manual_airtable_instructions(new_option_name, AIRTABLE_SUBSYSTEM)
        return result
    except Exception as e:
        current_app.logger.error(f"Exception when trying to add '{new_option_name}' to Airtable Subsystem field: {e}", exc_info=True)
        log_manual_airtable_instructions(new_option_name, AIRTABLE_SUBSYSTEM)
        return False


def add_option_via_typecast(option_value: str, field_name: str, project=None, primary_field_value: str = None) -> bool:
    """
    Adds a new option to an Airtable select field using the proven approach from airtable_new_option.py.
    This uses the direct Airtable API with typecast=True to create a temporary record, 
    then immediately deletes it.
    
    This is the approach that actually works based on the test script.
    
    Args:
        option_value (str): The new option value to add
        field_name (str): The Airtable field name (e.g., "Subsystem")
        primary_field_value (str): Optional value for the primary field; if None, a default is generated
    
    Returns:
        bool: True if successful, False otherwise
    """
    api_key, base_id, table_id = _get_airtable_config(project)

    if not all([api_key, base_id, table_id]):
        current_app.logger.error("Airtable configuration missing for option addition")
        return False
        
    if api_key == 'YOUR_AIRTABLE_API_KEY':
        current_app.logger.error("Airtable API Key is a placeholder")
        return False

    if not option_value or not option_value.strip():
        current_app.logger.warning(f"Empty option value provided for field '{field_name}'")
        return False

    cleaned_option_value = option_value.strip()
    if primary_field_value is None:
        primary_field_value = f"Temporary record to add option '{cleaned_option_value[:30]}'"

    # Direct API approach based on airtable_new_option.py
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Create the record with typecast=True
    data_fields = {
        AIRTABLE_NAME: primary_field_value,
        field_name: cleaned_option_value
    }

    payload = {
        "records": [
            {
                "fields": data_fields
            }
        ],
        "typecast": True  # This is crucial for adding new options
    }

    created_record_id = None
    
    try:
        current_app.logger.info(f"Creating temporary record to add option '{cleaned_option_value}' to field '{field_name}'")
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        response_data = response.json()
        if 'records' in response_data and len(response_data['records']) > 0:
            created_record_id = response_data['records'][0]['id']
            current_app.logger.info(f"Successfully created temporary record {created_record_id}")
        else:
            current_app.logger.error(f"Unexpected response structure: {response_data}")
            return False
            
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"HTTP Error creating record: {e}")
        if e.response:
            current_app.logger.error(f"Response content: {e.response.content.decode()}")
        return False
    except Exception as e:
        current_app.logger.error(f"Error creating temporary record: {e}", exc_info=True)
        return False

    # Now delete the temporary record
    if created_record_id:
        try:
            delete_url = f"{url}/{created_record_id}"
            current_app.logger.info(f"Deleting temporary record {created_record_id}")
            
            delete_response = requests.delete(delete_url, headers=headers)
            delete_response.raise_for_status()
            
            current_app.logger.info(f"Successfully deleted temporary record {created_record_id}")
            current_app.logger.info(f"Option '{cleaned_option_value}' should now be available in field '{field_name}'")
            return True
            
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(f"HTTP Error deleting record {created_record_id}: {e}")
            current_app.logger.warning(f"Temporary record {created_record_id} may need manual deletion")
            return True  # Option was still added, just cleanup failed
        except Exception as e:
            current_app.logger.error(f"Error deleting temporary record {created_record_id}: {e}", exc_info=True)
            current_app.logger.warning(f"Temporary record {created_record_id} may need manual deletion")
            return True  # Option was still added, just cleanup failed
    
    return False


def add_option_to_subsystem_field_improved(new_option_name: str, project=None) -> bool:
    """
    Improved version of add_option_to_airtable_subsystem_field that uses the proven approach.
    This should be used instead of the original function.
    """
    return add_option_via_typecast(new_option_name, AIRTABLE_SUBSYSTEM, project=project)


def get_airtable_select_options(table: Table, field_name: str) -> list[str]:
    """
    Fetches the available choices for a single select or multiple select field from Airtable.

    Args:
        table (Table): The pyairtable Table object.
        field_name (str): The name of the select field in Airtable.

    Returns:
        list[str]: A list of choice names, or an empty list if an error occurs or field is not found/not a select.
    """
    try:
        table_schema = table.schema()
        for field in table_schema.fields:
            if field.name == field_name:
                if field.type == "singleSelect" or field.type == "multipleSelects": # multipleSelects might be the type name
                    return [choice.name for choice in field.options.choices]
                else:
                    current_app.logger.warning(f"Airtable field \'{field_name}\' is not a singleSelect or multipleSelects field. Type is \'{field.type}\'.")
                    return []
        current_app.logger.warning(f"Airtable field \'{field_name}\' not found in table schema.")
        return []
    except Exception as e:
        current_app.logger.error(f"Error fetching Airtable schema or options for field \'{field_name}\': {e}")
        return []

def _get_airtable_config(project=None):
    """Return Airtable credentials for a project, falling back to app config."""
    api_key = current_app.config.get('AIRTABLE_API_KEY')
    base_id = current_app.config.get('AIRTABLE_BASE_ID')
    table_id = current_app.config.get('AIRTABLE_TABLE_ID')

    if project is not None:
        if getattr(project, 'airtable_api_key', None):
            api_key = project.airtable_api_key
        if getattr(project, 'airtable_base_id', None):
            base_id = project.airtable_base_id
        if getattr(project, 'airtable_table_id', None):
            table_id = project.airtable_table_id

    return api_key, base_id, table_id


def get_airtable_table(project=None):
    """Initializes and returns an Airtable Table object."""
    api_key, base_id, table_id = _get_airtable_config(project)

    if not api_key or api_key == 'YOUR_AIRTABLE_API_KEY': # Check against placeholder
        current_app.logger.error("Airtable API Key not configured or is using placeholder.")
        return None
    if not base_id:
        current_app.logger.error("Airtable Base ID not configured.")
        return None
    if not table_id:
        current_app.logger.error("Airtable Table ID not configured.")
        return None

    try:
        table = Table(api_key, base_id, table_id)
        # You can test connectivity here if needed, e.g., by trying to fetch one record or metadata
        # table.all(max_records=1) 
        return table
    except Exception as e:
        current_app.logger.error(f"Failed to initialize Airtable table: {e}")
        return None

def sync_part_to_airtable(part: Part):
    """
    Synchronizes a Part object's data to Airtable.
    This function will map the Part model fields to the Airtable columns
    and then create a new record in Airtable.

    Args:
        part (Part): The Part object to synchronize.

    Returns:
        dict: The Airtable record if successful, None otherwise.
    """
    table = get_airtable_table(part.project)
    if not table:
        current_app.logger.error(f"Airtable sync for part {part.part_number} failed: Table object not initialized.")
        return None

    # Prepare data, validating select options where necessary
    airtable_data = {}

    # Name (Text field - usually no options to validate)
    airtable_data[AIRTABLE_NAME] = f"{part.part_number}: {part.name}"

    # Subteam (Select field)
    if part.subteam:
        subteam_options = get_airtable_select_options(table, AIRTABLE_SUBTEAM)
        if subteam_options and part.subteam.name in subteam_options:
            airtable_data[AIRTABLE_SUBTEAM] = part.subteam.name
        elif subteam_options: # Options exist, but current value is not among them
            current_app.logger.warning(f"Airtable sync for part {part.part_number}: Subteam name \'{part.subteam.name}\' is not a valid option in Airtable. Field will be omitted. Valid options: {subteam_options}")
        # If subteam_options is empty (e.g., error fetching schema or not a select field), we might still try to send it or omit it.
        # For now, if options list is empty (implying not a select or error), we'll try sending the value.
        elif not subteam_options:
             airtable_data[AIRTABLE_SUBTEAM] = part.subteam.name # Attempt to send anyway

    # Subsystem (Select field)
    subsystem_needs_manual_update = False
    subsystem_name_for_update = None
    if part.subsystem:
        subsystem_options = get_airtable_select_options(table, AIRTABLE_SUBSYSTEM)
        if subsystem_options and part.subsystem.name in subsystem_options:
            airtable_data[AIRTABLE_SUBSYSTEM] = part.subsystem.name
        elif subsystem_options:
            current_app.logger.warning(f"Airtable sync for part {part.part_number}: Subsystem name \'{part.subsystem.name}\' is not a valid option in Airtable. Field will be omitted. Valid options: {subsystem_options}")
            # Mark for manual update instructions later
            subsystem_needs_manual_update = True
            subsystem_name_for_update = part.subsystem.name
        elif not subsystem_options:
            airtable_data[AIRTABLE_SUBSYSTEM] = part.subsystem.name # Attempt to send anyway

    # Manufacturing Quantity (Number field)
    airtable_data[AIRTABLE_MANUFACTURING_QUANTITY] = part.quantity

    # Status (Select field)
    if part.status:
        status_options = get_airtable_select_options(table, AIRTABLE_STATUS)
        if status_options and part.status in status_options:
            airtable_data[AIRTABLE_STATUS] = part.status
        elif status_options: # Status is not a valid option
            current_app.logger.warning(f"Airtable sync for part {part.part_number}: Status \'{part.status}\' is not a valid option in Airtable. Field will be omitted. Valid options: {status_options}. You may need to add this option in Airtable settings.")
        elif not status_options: # Not a select field or error fetching options, try sending
            airtable_data[AIRTABLE_STATUS] = part.status

    # Machine (Select field)
    if part.machine and part.machine.name:
        machine_options = get_airtable_select_options(table, AIRTABLE_MACHINE)
        if machine_options and part.machine.name in machine_options:
            airtable_data[AIRTABLE_MACHINE] = part.machine.name
        elif machine_options:
            current_app.logger.warning(f"Airtable sync for part {part.part_number}: Machine name \'{part.machine.name}\' is not a valid option in Airtable. Field will be omitted. Valid options: {machine_options}")
        elif not machine_options:
            airtable_data[AIRTABLE_MACHINE] = part.machine.name # Attempt to send anyway

    # Raw Material (Text field)
    airtable_data[AIRTABLE_RAW_MATERIAL] = part.raw_material

    # Post-process (Multiple Select field)
    if part.post_processes:
        pp_options = get_airtable_select_options(table, AIRTABLE_POST_PROCESS)
        valid_pp_names = []
        if pp_options: # If we have a list of valid options
            for pp in part.post_processes:
                if pp.name in pp_options:
                    valid_pp_names.append(pp.name)
                else:
                    current_app.logger.warning(f"Airtable sync for part {part.part_number}: Post-process name \'{pp.name}\' is not a valid option in Airtable. It will be excluded. Valid options: {pp_options}")
            if valid_pp_names: # Only add if there's at least one valid process
                 airtable_data[AIRTABLE_POST_PROCESS] = valid_pp_names
            elif part.post_processes: # Some processes were specified but none were valid
                current_app.logger.warning(f"Airtable sync for part {part.part_number}: No valid post-process options found for the provided names. \'Post-process\' field will be omitted.")
        elif not pp_options and part.post_processes: # Not a select field or error fetching options, try sending all
            airtable_data[AIRTABLE_POST_PROCESS] = [pp.name for pp in part.post_processes]

    # Notes (Text field)
    airtable_data[AIRTABLE_NOTES] = part.description

    # Remove keys with None values, as Airtable might not like them for certain field types
    # However, for select fields, sending None might clear it, which could be desired.
    # For now, let's filter None values, but this might need adjustment based on Airtable behavior.
    # final_airtable_data = {k: v for k, v in airtable_data.items() if v is not None}
    # Re-evaluating: pyairtable might handle None correctly by not sending the field or sending it as blank.
    # The main issue is sending a value that's not an option for a select field.
    # The logic above now omits fields if their value isn't a valid select option (and options were fetched).

    current_app.logger.info(f"Attempting to sync part {part.part_number} to Airtable with processed data: {airtable_data}")

    try:
        # Create a new record in Airtable
        record = table.create(airtable_data) # Use the filtered airtable_data
        record_id = record['id']
        current_app.logger.info(f"Successfully synced part {part.part_number} to Airtable. Record ID: {record_id}")
        
        # If subsystem needs manual update, provide complete workflow instructions
        if subsystem_needs_manual_update and subsystem_name_for_update:
            log_manual_airtable_instructions(subsystem_name_for_update, AIRTABLE_SUBSYSTEM)
            log_record_update_instructions(record_id, subsystem_name_for_update)
        
        return record
    except requests.exceptions.HTTPError as e_http:
        error_details = "No response content"
        if e_http.response is not None:
            try:
                error_details = e_http.response.json() # Airtable often returns JSON errors
            except ValueError: # If response is not JSON
                error_details = e_http.response.text
        current_app.logger.error(f"HTTPError syncing part {part.part_number} to Airtable: {e_http}. Response: {error_details}")
        return None
    except Exception as e:
        current_app.logger.error(f"Generic error syncing part {part.part_number} to Airtable: {e}", exc_info=True)
        return None

def log_manual_airtable_instructions(new_option_name: str, field_name: str = "Subsystem") -> None:
    """
    Logs detailed instructions for manually adding a new option to an Airtable field.
    
    Args:
        new_option_name (str): The name of the option that needs to be manually added
        field_name (str): The name of the Airtable field (default: "Subsystem")
    """
    current_app.logger.info("=" * 80)
    current_app.logger.info("MANUAL AIRTABLE ACTION REQUIRED")
    current_app.logger.info("=" * 80)
    current_app.logger.info(f"New assembly '{new_option_name}' was created but could not be automatically")
    current_app.logger.info(f"added to the Airtable '{field_name}' field options due to API restrictions.")
    current_app.logger.info("")
    current_app.logger.info("MANUAL STEPS TO ADD THE OPTION:")
    current_app.logger.info(f"1. Open your Airtable base in a web browser")
    current_app.logger.info(f"2. Navigate to the table containing the '{field_name}' field")
    current_app.logger.info(f"3. Click on the '{field_name}' field header to open field settings")
    current_app.logger.info(f"4. In the field configuration, look for 'Options' or 'Choices'")
    current_app.logger.info(f"5. Add a new option with the name: '{new_option_name}'")
    current_app.logger.info(f"6. Choose a color for the option (suggested: gray or any available color)")
    current_app.logger.info(f"7. Save the field settings")
    current_app.logger.info("")
    current_app.logger.info("After adding this option manually, parts created under this assembly")
    current_app.logger.info("will be able to sync properly to Airtable with the correct subsystem value.")
    current_app.logger.info("=" * 80)

def update_record_with_subsystem(record_id: str, subsystem_name: str) -> bool:
    """
    Update an existing Airtable record with a new subsystem value.
    This should be called AFTER the subsystem option has been manually added to the field choices.
    
    Args:
        record_id: The Airtable record ID to update
        subsystem_name: The subsystem name to set (must already exist in field choices)
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        api_key = current_app.config.get('AIRTABLE_API_KEY')
        base_id = current_app.config.get('AIRTABLE_BASE_ID')
        table_name = current_app.config.get('AIRTABLE_TABLE_NAME', 'Parts')
        
        if not all([api_key, base_id, record_id, subsystem_name]):
            current_app.logger.error("Missing required parameters for Airtable record update")
            return False
            
        if api_key == 'YOUR_AIRTABLE_API_KEY':
            current_app.logger.error("Airtable API Key is a placeholder. Record update will fail.")
            return False
        
        # Use direct API call for updating the record
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": {
                AIRTABLE_SUBSYSTEM: subsystem_name
            }
        }
        
        current_app.logger.info(f"Updating Airtable record {record_id} with subsystem: {subsystem_name}")
        
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            current_app.logger.info(f"Successfully updated Airtable record {record_id} with subsystem '{subsystem_name}'")
            return True
        else:
            current_app.logger.error(f"Failed to update Airtable record {record_id}. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        current_app.logger.error(f"Timeout updating Airtable record {record_id}")
        return False
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request error updating Airtable record {record_id}: {e}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error updating Airtable record {record_id}: {e}")
        return False

def log_record_update_instructions(record_id: str, subsystem_name: str):
    """
    Log detailed instructions for manually updating a record after adding the subsystem option.
    """
    current_app.logger.info("=" * 80)
    current_app.logger.info("MANUAL RECORD UPDATE INSTRUCTIONS")
    current_app.logger.info("=" * 80)
    current_app.logger.info(f"After manually adding '{subsystem_name}' to the Subsystem field options:")
    current_app.logger.info("")
    current_app.logger.info("STEP 2: Update the Record")
    current_app.logger.info(f"1. You can now update record {record_id} programmatically")
    current_app.logger.info("2. Call the update_record_with_subsystem() function:")
    current_app.logger.info(f"   update_record_with_subsystem('{record_id}', '{subsystem_name}')")
    current_app.logger.info("")
    current_app.logger.info("OR update manually in Airtable:")
    current_app.logger.info(f"1. Open the record with ID: {record_id}")
    current_app.logger.info(f"2. Set the 'Subsystem' field to: {subsystem_name}")
    current_app.logger.info("3. Save the record")
    current_app.logger.info("=" * 80)

# Example of how you might fetch options for validation (e.g., for Subteam/Subsystem)
# def get_airtable_field_options(field_name: str):
#     table = get_airtable_table()
#     if not table:
#         return []
#     try:
#         # This is a conceptual example. Pyairtable might not have a direct way
#         # to get field options easily. You might need to query all records
#         # and deduce options, or use Airtable's metadata API if available and supported.
#         # For "select" or "multiple select" fields, this is more complex.
#         # Often, these lists are managed within Airtable itself.
#         # A common approach is to have a separate table for these options if they are dynamic.
#         current_app.logger.warning(f"Fetching field options for '{field_name}' is not fully implemented.")
#         return [] # Placeholder
#     except Exception as e:
#         current_app.logger.error(f"Error fetching Airtable field options for '{field_name}': {e}")
#         return []


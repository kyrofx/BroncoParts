import requests
import json

# --- Configuration - Replace with your actual values ---
AIRTABLE_API_KEY = ""  # Your Personal Access Token or older API Key
AIRTABLE_BASE_ID = ""
AIRTABLE_TABLE_NAME_OR_ID = "" # e.g., "Tasks" or "tblXXXXXXXXXXXXXX"




# For updating an existing record:
EXISTING_RECORD_ID = "" # e.g., "recXXXXXXXXXXXXXX" (leave empty to skip update test)

# For creating a new record (or updating if EXISTING_RECORD_ID is set):
SINGLE_SELECT_FIELD_NAME = "Subsystem" # The name of your single select field
NEW_OPTION_VALUE = "Test Wowowowsdf" # The new option you want to add

# This is the field where your primary identifier is (e.g., "Name", "Task ID").
# It's needed for creating a new record so it has some identifying data.
# If your single select field is the only field you want to set for a new record,
# you can make this the same as SINGLE_SELECT_FIELD_NAME, but that's unusual.
PRIMARY_FIELD_NAME_FOR_CREATE = "Name"
PRIMARY_FIELD_VALUE_FOR_CREATE = "airtable test"

# --- End Configuration ---

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

def add_or_update_record_with_new_option(record_id=None):
    """
    Creates a new record or updates an existing one, attempting to add a new
    option to the single select field implicitly.
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME_OR_ID}"

    data_fields = {
        SINGLE_SELECT_FIELD_NAME: NEW_OPTION_VALUE
    }

    if record_id:
        # Update existing record
        payload = {
            "records": [
                {
                    "id": record_id,
                    "fields": data_fields
                }
            ],
            "typecast": True  # This is crucial for adding new options
        }
        http_method = 'patch'
        url_path = url # PATCH uses the base table URL
        print(f"Attempting to update record {record_id} with new option '{NEW_OPTION_VALUE}' for field '{SINGLE_SELECT_FIELD_NAME}'...")
    else:
        # Create new record
        # Add a primary field to ensure the record isn't empty beyond the new option
        data_fields[PRIMARY_FIELD_NAME_FOR_CREATE] = PRIMARY_FIELD_VALUE_FOR_CREATE
        payload = {
            "records": [
                {
                    "fields": data_fields
                }
            ],
            "typecast": True  # This is crucial for adding new options
        }
        http_method = 'post'
        url_path = url # POST uses the base table URL
        print(f"Attempting to create a new record with option '{NEW_OPTION_VALUE}' for field '{SINGLE_SELECT_FIELD_NAME}'...")

    try:
        if http_method == 'patch':
            response = requests.patch(url_path, headers=HEADERS, data=json.dumps(payload))
        else: # post
            response = requests.post(url_path, headers=HEADERS, data=json.dumps(payload))

        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        print("Successfully sent data to Airtable.")
        print("Response:", json.dumps(response.json(), indent=2))
        print(f"\nSUCCESS: Check your Airtable base. The option '{NEW_OPTION_VALUE}' should now exist in the '{SINGLE_SELECT_FIELD_NAME}' field,")
        if record_id:
            print(f"and record '{record_id}' should be updated.")
        else:
            print("and a new record should be created with this option selected.")
        print("If the option was already present, the record would just use the existing option.")

    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        print("Response content:", errh.response.content.decode())
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Oops: Something Else: {err}")
    except json.JSONDecodeError:
        print("Error decoding JSON response. Status code:", response.status_code)
        print("Response text:", response.text)


if __name__ == "__main__":
    if not AIRTABLE_API_KEY or AIRTABLE_API_KEY == "YOUR_AIRTABLE_API_KEY":
        print("ERROR: Please set your AIRTABLE_API_KEY in the script.")
    elif not AIRTABLE_BASE_ID or AIRTABLE_BASE_ID == "YOUR_BASE_ID":
        print("ERROR: Please set your AIRTABLE_BASE_ID in the script.")
    elif not AIRTABLE_TABLE_NAME_OR_ID or AIRTABLE_TABLE_NAME_OR_ID == "YOUR_TABLE_NAME_OR_ID":
        print("ERROR: Please set your AIRTABLE_TABLE_NAME_OR_ID in the script.")
    elif not SINGLE_SELECT_FIELD_NAME:
        print("ERROR: Please set your SINGLE_SELECT_FIELD_NAME in the script.")
    else:
        # --- Test 1: Update an existing record (if RECORD_ID is provided) ---
        if EXISTING_RECORD_ID and EXISTING_RECORD_ID != "OPTIONAL_RECORD_ID_TO_UPDATE":
            print("--- TESTING UPDATE ---")
            add_or_update_record_with_new_option(record_id=EXISTING_RECORD_ID)
            print("\n" + "="*30 + "\n")
        else:
            print("--- SKIPPING UPDATE TEST (EXISTING_RECORD_ID not set) ---\n")

        # --- Test 2: Create a new record ---
        if not PRIMARY_FIELD_NAME_FOR_CREATE:
            print("ERROR: Please set PRIMARY_FIELD_NAME_FOR_CREATE for creating a new record.")
        else:
            print("--- TESTING CREATE ---")
            add_or_update_record_with_new_option()
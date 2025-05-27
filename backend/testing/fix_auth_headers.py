#!/usr/bin/env python3
"""Script to fix get_auth_headers calls to use email instead of username."""

import os
import re

# Mapping of usernames to emails
USERNAME_TO_EMAIL = {
    'admin': 'admin@test.com',
    'editor': 'editor@test.com',
    'readonly': 'readonly@test.com'
}

def fix_auth_headers_in_file(file_path):
    """Fix get_auth_headers calls in a single file."""
    print(f"Processing {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match get_auth_headers calls with username
    pattern = r"get_auth_headers\(client,\s*'([^']+)',\s*'([^']+)'\)"
    
    def replace_func(match):
        username = match.group(1)
        password = match.group(2)
        
        if username in USERNAME_TO_EMAIL:
            email = USERNAME_TO_EMAIL[username]
            return f"get_auth_headers(client, '{email}', '{password}')"
        else:
            print(f"Warning: Unknown username '{username}' in {file_path}")
            return match.group(0)  # Return original if username not found
    
    content = re.sub(pattern, replace_func, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

def main():
    """Main function to process all test files."""
    test_dir = "tests"
    updated_files = []
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_auth_headers_in_file(file_path):
                    updated_files.append(file_path)
    
    print(f"\nUpdated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to analyze test failures and categorize them by type
"""

# Tests that return 404 - endpoints don't exist, should be removed
ENDPOINTS_404_NOT_FOUND = [
    # Authentication endpoints that don't exist
    "test_register_success",  # POST /api/register/<link_identifier>
    "test_register_invalid_link",  # POST /api/register/<link_identifier>
    "test_register_expired_link",  # POST /api/register/<link_identifier>
    "test_register_duplicate_username",  # POST /api/register/<link_identifier>
    "test_register_duplicate_email",  # POST /api/register/<link_identifier>
    "test_password_reset_request",  # POST /api/request-password-reset
    "test_password_reset_request_nonexistent_email",  # POST /api/request-password-reset
    
    # Machine endpoints that don't exist
    "test_get_machine_by_id",  # GET /api/machines/<id>
    "test_update_machine_as_admin",  # PUT/PATCH /api/machines/<id>
    "test_update_machine_as_readonly",  # PUT/PATCH /api/machines/<id>
    "test_delete_machine_as_admin",  # DELETE /api/machines/<id>
    "test_delete_machine_with_parts",  # DELETE /api/machines/<id>
    "test_get_machine_parts",  # GET /api/machines/<id>/parts
    
    # Post-process endpoints that don't exist
    "test_get_post_process_by_id",  # GET /api/post-processes/<id>
    "test_update_post_process_as_admin",  # PUT/PATCH /api/post-processes/<id>
    "test_delete_post_process_as_admin",  # DELETE /api/post-processes/<id>
    "test_delete_post_process_with_parts",  # DELETE /api/post-processes/<id>
    "test_get_post_process_parts",  # GET /api/post-processes/<id>/parts
    
    # Order item endpoints that don't exist
    "test_create_order_item",  # POST /api/orders/<id>/items
    "test_update_order_item",  # PUT/PATCH /api/orders/<id>/items/<item_id>
    "test_delete_order_item",  # DELETE /api/orders/<id>/items/<item_id>
    
    # Statistics endpoints that don't exist
    "test_get_dashboard_stats_success",  # GET /api/stats/dashboard
    "test_get_project_statistics",  # GET /api/stats/projects
    "test_get_user_statistics",  # GET /api/stats/users
    "test_get_material_usage_stats",  # GET /api/stats/materials
    "test_get_machine_utilization_stats",  # GET /api/stats/machines
    "test_get_time_based_stats",  # GET /api/stats/time-based
    "test_statistics_permission_readonly",  # GET /api/stats/*
    "test_statistics_permission_unauthorized",  # GET /api/stats/*
    "test_export_statistics_admin_only",  # GET /api/stats/export
    "test_order_statistics",  # GET /api/orders/statistics
    "test_get_project_statistics",  # GET /api/projects/<id>/statistics
    "test_registration_link_statistics",  # GET /api/registration-links/statistics
    
    # User endpoints that don't exist
    "test_get_current_user",  # GET /api/users/current
    "test_change_password",  # POST /api/change-password
    "test_change_password_wrong_current",  # POST /api/change-password
    "test_get_pending_users",  # GET /api/users/pending
    "test_bulk_user_actions",  # POST /api/users/bulk-actions
    
    # Search endpoints that don't exist
    "test_invalid_search_parameters",  # GET /api/search with invalid params
]

# Tests that return 405 METHOD NOT ALLOWED - endpoints exist but wrong HTTP method
ENDPOINTS_405_METHOD_NOT_ALLOWED = [
    # Machine endpoints - POST method not allowed
    "test_create_machine_as_admin",  # POST /api/machines
    "test_create_machine_as_editor",  # POST /api/machines
    "test_create_machine_as_readonly",  # POST /api/machines
    "test_create_machine_duplicate_name",  # POST /api/machines
    
    # Post-process endpoints - POST method not allowed
    "test_create_post_process_as_admin",  # POST /api/post-processes
    "test_create_post_process_as_editor",  # POST /api/post-processes
    "test_create_post_process_as_readonly",  # POST /api/post-processes
    "test_create_post_process_duplicate_name",  # POST /api/post-processes
    
    # User endpoints - POST method not allowed
    "test_create_user_as_admin",  # POST /api/users
    "test_create_user_as_non_admin",  # POST /api/users
    "test_create_user_duplicate_username",  # POST /api/users
    
    # Error handling test
    "test_method_not_allowed",  # Testing wrong HTTP method
]

# Data serialization issues - endpoints exist but return wrong format
DATA_SERIALIZATION_ISSUES = [
    # Tests expect list items but get wrapped objects
    "test_get_machines_as_readonly",  # TypeError: string indices must be integers
    "test_get_post_processes_as_readonly",  # TypeError: string indices must be integers  
    "test_get_parts_as_readonly",  # TypeError: string indices must be integers
    "test_get_projects_as_readonly",  # KeyError: 0
    "test_project_search",  # KeyError: 0
    "test_machine_and_post_process_search",  # KeyError: 0
    "test_get_users_as_admin",  # AssertionError: assert 1 == 3 (expect list, get wrapped)
    
    # Tests expect direct object properties but get different structure
    "test_get_order_by_id",  # KeyError: 'id'
    "test_get_part_by_id",  # KeyError: 'id'
    "test_get_project_by_id",  # KeyError: 'id'
    "test_create_project_as_editor",  # KeyError: 'name'
    "test_update_project_as_admin",  # KeyError: 'name'
    "test_create_assembly_with_hierarchy",  # KeyError: 'name'
    "test_update_part_as_editor",  # KeyError: 'name'
    "test_create_order_with_items",  # KeyError: 'order_number'
    "test_update_order_as_admin",  # KeyError: 'status'
    "test_part_inventory_management",  # KeyError: 'quantity_on_hand'
    "test_update_user_as_admin",  # KeyError: 'permission'
    "test_approve_user",  # KeyError: 'is_approved'
]

# Database constraint issues
DATABASE_CONSTRAINT_ISSUES = [
    "test_create_project_duplicate_prefix",  # UNIQUE constraint failed: projects.prefix
    "test_delete_project_with_parts",  # NOT NULL constraint failed: parts.project_id
    "test_duplicate_constraints",  # assert 400 == 201 (constraint not handled properly)
    "test_foreign_key_constraints",  # assert 400 == 404 (constraint error)
    "test_concurrent_modification",  # assert 400 == 201 (constraint issue)
    "test_airtable_service_error_handling",  # assert 400 == 201 (constraint issue)
]

# Error handling issues - wrong response format or status codes
ERROR_HANDLING_ISSUES = [
    "test_malformed_json_requests",  # TypeError: argument of type 'NoneType' is not iterable
    "test_missing_required_fields",  # AssertionError: assert 'error' in {'message': 'Error: Missing name or prefix'}
    "test_get_nonexistent_part",  # AttributeError: 'NoneType' object has no attribute 'get'
    "test_get_nonexistent_project",  # AttributeError: 'NoneType' object has no attribute 'get'
    "test_update_nonexistent_project",  # AttributeError: 'NoneType' object has no attribute 'get'
    "test_update_nonexistent_user",  # AttributeError: 'NoneType' object has no attribute 'get'
    "test_update_user_as_non_admin",  # Wrong error message format
]

# Business logic issues - correct endpoints but wrong behavior
BUSINESS_LOGIC_ISSUES = [
    "test_get_orders_as_readonly",  # assert 403 == 200 (wrong permission check)
    "test_create_order_as_editor",  # assert 400 == 201 (validation issue)
    "test_create_order_as_readonly",  # assert 400 == 403 (wrong permission check)
    "test_create_part_as_editor",  # assert 400 == 201 (validation issue)
    "test_create_part_with_post_processes",  # assert 400 == 201 (validation issue)
    "test_part_hierarchy_operations",  # assert 400 == 201 (validation issue)
    "test_collaborative_project_workflow",  # assert 400 == 201 (validation issue)
    "test_project_lifecycle_workflow",  # assert 400 == 201 (validation issue)
    "test_error_recovery_workflow",  # assert 400 == 404 (wrong error response)
]

# Data structure/format issues
DATA_STRUCTURE_ISSUES = [
    "test_part_search_and_filtering",  # AssertionError: assert 1 == 2 (data format)
    "test_get_project_parts",  # AssertionError: assert 1 == 2 (data format)
    "test_invalid_pagination_parameters",  # assert 200 == 400 (pagination not working)
]

# Model/database schema issues
MODEL_SCHEMA_ISSUES = [
    "test_authorization_edge_cases",  # sqlalchemy.exc.InvalidRequestError: Entity namespace for "users" has no property "role"
]

# Workflow tests that depend on non-existent endpoints
WORKFLOW_TESTS_TO_REMOVE = [
    "test_complete_registration_to_order_workflow",  # Uses non-existent register endpoint
]

print("TESTS TO DELETE (404 NOT FOUND):")
for test in ENDPOINTS_404_NOT_FOUND:
    print(f"  - {test}")

print(f"\nTotal tests to delete: {len(ENDPOINTS_404_NOT_FOUND)}")
print(f"Total METHOD NOT ALLOWED tests to delete: {len(ENDPOINTS_405_METHOD_NOT_ALLOWED)}")
print(f"Total workflow tests to delete: {len(WORKFLOW_TESTS_TO_REMOVE)}")
print(f"Total tests to delete: {len(ENDPOINTS_404_NOT_FOUND) + len(ENDPOINTS_405_METHOD_NOT_ALLOWED) + len(WORKFLOW_TESTS_TO_REMOVE)}")

print(f"\nISSUES TO FIX:")
print(f"  - Data serialization issues: {len(DATA_SERIALIZATION_ISSUES)}")
print(f"  - Database constraint issues: {len(DATABASE_CONSTRAINT_ISSUES)}")
print(f"  - Error handling issues: {len(ERROR_HANDLING_ISSUES)}")
print(f"  - Business logic issues: {len(BUSINESS_LOGIC_ISSUES)}")
print(f"  - Data structure issues: {len(DATA_STRUCTURE_ISSUES)}")
print(f"  - Model schema issues: {len(MODEL_SCHEMA_ISSUES)}")

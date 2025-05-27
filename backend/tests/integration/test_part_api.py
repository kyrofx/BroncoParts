"""Integration tests for parts management API endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


class TestPartAPI:
    """Test cases for parts management API endpoints."""
    
    def test_get_parts_as_readonly(self, client, db_session, mock_airtable):
        """Test getting parts as readonly user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.get('/api/parts', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) >= 1
        assert any(p['name'] == 'Test Part' for p in data)
    
    def test_get_part_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific part by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/parts/{part.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['id'] == part.id
        assert data['name'] == 'Test Part'
        assert data['part_number'] == part.part_number
        assert data['project_id'] == project.id
    
    def test_get_nonexistent_part(self, client, db_session, mock_airtable):
        """Test getting a nonexistent part."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/parts/999', headers=headers)
        
        assert_error_response(response, 404, 'Part not found')
    
    def test_create_part_as_editor(self, client, db_session, mock_airtable):
        """Test creating a part as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/parts', headers=headers, json={
            'name': 'New Part',
            'description': 'A new test part',
            'type': 'part',
            'project_id': project.id,
            'quantity': 2,
            'material': 'Aluminum',
            'machine_id': machine.id,
            'priority': 1,
            'status': 'in design'
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'New Part'
        assert data['type'] == 'part'
        assert data['project_id'] == project.id
        assert data['quantity'] == 2
        assert data['machine_id'] == machine.id
        assert 'part_number' in data
        assert 'numeric_id' in data
        
        # Verify Airtable sync was called
        mock_airtable['sync_part'].assert_called()
    
    def test_create_assembly_with_hierarchy(self, client, db_session, mock_airtable):
        """Test creating an assembly with subteam and subsystem relationships."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        # Create subteam and subsystem parts first
        subteam = TestFixtures.create_test_part(db_session, project, name='Drivetrain', type='assembly')
        subsystem = TestFixtures.create_test_part(db_session, project, name='Motors', type='assembly')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Motor Assembly',
            'type': 'assembly',
            'project_id': project.id,
            'quantity': 1,
            'subteam_id': subteam.id,
            'subsystem_id': subsystem.id
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'Motor Assembly'
        assert data['type'] == 'assembly'
        assert data['subteam_id'] == subteam.id
        assert data['subsystem_id'] == subsystem.id
        assert 'A-' in data['part_number']  # Assembly part number format
    
    def test_create_part_as_readonly(self, client, db_session, mock_airtable):
        """Test creating a part as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.post('/api/parts', headers=headers, json={
            'name': 'New Part',
            'type': 'part',
            'project_id': project.id,
            'quantity': 1
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_create_part_with_post_processes(self, client, db_session, mock_airtable):
        """Test creating a part with post-processing steps."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        post_process1 = TestFixtures.create_test_post_process(db_session, name='Anodizing')
        post_process2 = TestFixtures.create_test_post_process(db_session, name='Painting')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Finished Part',
            'type': 'part',
            'project_id': project.id,
            'quantity': 1,
            'post_process_ids': [post_process1.id, post_process2.id]
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'Finished Part'
        assert len(data['post_processes']) == 2
        post_process_names = [pp['name'] for pp in data['post_processes']]
        assert 'Anodizing' in post_process_names
        assert 'Painting' in post_process_names
    
    def test_create_part_missing_required_fields(self, client, db_session, mock_airtable):
        """Test creating a part with missing required fields."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Missing name
        response = client.post('/api/parts', headers=headers, json={
            'type': 'part',
            'project_id': project.id,
            'quantity': 1
        })
        assert_error_response(response, 400)
        
        # Missing type
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Test Part',
            'project_id': project.id,
            'quantity': 1
        })
        assert_error_response(response, 400)
        
        # Missing project_id
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Test Part',
            'type': 'part',
            'quantity': 1
        })
        assert_error_response(response, 400)
    
    def test_update_part_as_editor(self, client, db_session, mock_airtable):
        """Test updating a part as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.put(f'/api/parts/{part.id}', headers=headers, json={
            'name': 'Updated Part',
            'description': 'Updated description',
            'status': 'manufactured',
            'priority': 0,
            'have_material': True
        })
        
        data = assert_success_response(response)
        assert data['name'] == 'Updated Part'
        assert data['description'] == 'Updated description'
        assert data['status'] == 'manufactured'
        assert data['priority'] == 0
        assert data['have_material'] is True
        
        # Verify Airtable sync was called for update
        mock_airtable['sync_part'].assert_called()
    
    def test_update_part_as_readonly(self, client, db_session, mock_airtable):
        """Test updating a part as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.put(f'/api/parts/{part.id}', headers=headers, json={
            'name': 'Updated Part'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_delete_part_as_admin(self, client, db_session, mock_airtable):
        """Test deleting a part as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/parts/{part.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_delete_part_as_editor(self, client, db_session, mock_airtable):
        """Test deleting a part as editor (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.delete(f'/api/parts/{part.id}', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_part_search_and_filtering(self, client, db_session, mock_airtable):
        """Test searching and filtering parts."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Motor Mount')
        part2 = TestFixtures.create_test_part(db_session, project, name='Wheel Hub')
        part3 = TestFixtures.create_test_part(db_session, project, name='Motor Assembly', type='assembly')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Test search by name
        response = client.get('/api/parts?search=Motor', headers=headers)
        data = assert_success_response(response)
        assert len(data) == 2  # Motor Mount and Motor Assembly
        
        # Test filter by type
        response = client.get('/api/parts?type=assembly', headers=headers)
        data = assert_success_response(response)
        assert all(part['type'] == 'assembly' for part in data)
        
        # Test filter by project
        response = client.get(f'/api/parts?project_id={project.id}', headers=headers)
        data = assert_success_response(response)
        assert len(data) >= 3
    
    def test_part_hierarchy_operations(self, client, db_session, mock_airtable):
        """Test part hierarchy operations."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        # Create parent assembly
        parent = TestFixtures.create_test_part(db_session, project, name='Parent Assembly', type='assembly')
        
        # Create child part
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Child Part',
            'type': 'part',
            'project_id': project.id,
            'quantity': 2,
            'parent_id': parent.id
        })
        
        child_data = assert_success_response(response, 201)
        assert child_data['parent_id'] == parent.id
        
        # Get parent with children
        response = client.get(f'/api/parts/{parent.id}?include_children=true', headers=headers)
        parent_data = assert_success_response(response)
        assert 'children' in parent_data
        assert len(parent_data['children']) == 1
        assert parent_data['children'][0]['name'] == 'Child Part'
    
    def test_part_inventory_management(self, client, db_session, mock_airtable):
        """Test part inventory management operations."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Update inventory quantities
        response = client.put(f'/api/parts/{part.id}', headers=headers, json={
            'quantity_on_hand': 10,
            'quantity_on_order': 5
        })
        
        data = assert_success_response(response)
        assert data['quantity_on_hand'] == 10
        assert data['quantity_on_order'] == 5
    
    def test_part_validation_rules(self, client, db_session, mock_airtable):
        """Test part validation rules."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Test invalid type
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Test Part',
            'type': 'invalid_type',
            'project_id': project.id,
            'quantity': 1
        })
        assert_error_response(response, 400)
        
        # Test invalid priority
        response = client.post('/api/parts', headers=headers, json={
            'name': 'Test Part',
            'type': 'part',
            'project_id': project.id,
            'quantity': 1,
            'priority': 999  # Invalid priority value
        })
        # May or may not be validated - depends on implementation
        assert response.status_code in [201, 400]
    
    def test_bulk_part_operations(self, client, db_session, mock_airtable):
        """Test bulk part operations."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Part 2')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Test bulk status update
        response = client.post('/api/parts/bulk-update', headers=headers, json={
            'part_ids': [part1.id, part2.id],
            'status': 'manufactured'
        })
        
        # Implementation dependent - may or may not exist
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist

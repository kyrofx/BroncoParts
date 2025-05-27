"""Integration tests for machine and post-process management API endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


@pytest.mark.integration
class TestMachineAPI:
    """Test cases for machine management API endpoints."""
    
    def test_get_machines_as_readonly(self, client, db_session, mock_airtable):
        """Test getting machines as readonly user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.get('/api/machines', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) >= 1
        assert any(m['name'] == 'Test Machine' for m in data)
    
    def test_get_machine_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific machine by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/machines/{machine.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['id'] == machine.id
        assert data['name'] == 'Test Machine'
    
    def test_create_machine_as_admin(self, client, db_session, mock_airtable):
        """Test creating a machine as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/machines', headers=headers, json={
            'name': 'CNC Mill'
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'CNC Mill'
        assert 'created_at' in data
    
    def test_create_machine_as_editor(self, client, db_session, mock_airtable):
        """Test creating a machine as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/machines', headers=headers, json={
            'name': '3D Printer'
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == '3D Printer'
    
    def test_create_machine_as_readonly(self, client, db_session, mock_airtable):
        """Test creating a machine as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.post('/api/machines', headers=headers, json={
            'name': 'Laser Cutter'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_create_machine_duplicate_name(self, client, db_session, mock_airtable):
        """Test creating a machine with duplicate name."""
        admin = TestFixtures.create_test_admin_user(db_session)
        existing_machine = TestFixtures.create_test_machine(db_session, name='Duplicate Machine')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/machines', headers=headers, json={
            'name': 'Duplicate Machine'
        })
        
        assert_error_response(response, 400, 'Machine name already exists')
    
    def test_update_machine_as_admin(self, client, db_session, mock_airtable):
        """Test updating a machine as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/machines/{machine.id}', headers=headers, json={
            'name': 'Updated Machine Name'
        })
        
        data = assert_success_response(response)
        assert data['name'] == 'Updated Machine Name'
    
    def test_update_machine_as_readonly(self, client, db_session, mock_airtable):
        """Test updating a machine as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.put(f'/api/machines/{machine.id}', headers=headers, json={
            'name': 'Updated Name'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_delete_machine_as_admin(self, client, db_session, mock_airtable):
        """Test deleting a machine as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/machines/{machine.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_delete_machine_with_parts(self, client, db_session, mock_airtable):
        """Test deleting a machine that has associated parts."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        # Associate part with machine
        part.machine_id = machine.id
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/machines/{machine.id}', headers=headers)
        
        # Should either cascade or prevent deletion
        assert response.status_code in [200, 400]
    
    def test_get_machine_parts(self, client, db_session, mock_airtable):
        """Test getting parts associated with a machine."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Part 2')
        
        # Associate parts with machine
        part1.machine_id = machine.id
        part2.machine_id = machine.id
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/machines/{machine.id}/parts', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 2
        part_names = [part['name'] for part in data]
        assert 'Part 1' in part_names
        assert 'Part 2' in part_names


@pytest.mark.integration
class TestPostProcessAPI:
    """Test cases for post-process management API endpoints."""
    
    def test_get_post_processes_as_readonly(self, client, db_session, mock_airtable):
        """Test getting post processes as readonly user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.get('/api/post-processes', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) >= 1
        assert any(pp['name'] == 'Test Post Process' for pp in data)
    
    def test_get_post_process_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific post process by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/post-processes/{post_process.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['id'] == post_process.id
        assert data['name'] == 'Test Post Process'
    
    def test_create_post_process_as_admin(self, client, db_session, mock_airtable):
        """Test creating a post process as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/post-processes', headers=headers, json={
            'name': 'Anodizing'
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'Anodizing'
        assert 'created_at' in data
    
    def test_create_post_process_as_editor(self, client, db_session, mock_airtable):
        """Test creating a post process as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/post-processes', headers=headers, json={
            'name': 'Powder Coating'
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'Powder Coating'
    
    def test_create_post_process_as_readonly(self, client, db_session, mock_airtable):
        """Test creating a post process as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.post('/api/post-processes', headers=headers, json={
            'name': 'Heat Treatment'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_create_post_process_duplicate_name(self, client, db_session, mock_airtable):
        """Test creating a post process with duplicate name."""
        admin = TestFixtures.create_test_admin_user(db_session)
        existing_pp = TestFixtures.create_test_post_process(db_session, name='Duplicate Process')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/post-processes', headers=headers, json={
            'name': 'Duplicate Process'
        })
        
        assert_error_response(response, 400, 'Post process name already exists')
    
    def test_update_post_process_as_admin(self, client, db_session, mock_airtable):
        """Test updating a post process as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/post-processes/{post_process.id}', headers=headers, json={
            'name': 'Updated Process Name'
        })
        
        data = assert_success_response(response)
        assert data['name'] == 'Updated Process Name'
    
    def test_delete_post_process_as_admin(self, client, db_session, mock_airtable):
        """Test deleting a post process as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/post-processes/{post_process.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_delete_post_process_with_parts(self, client, db_session, mock_airtable):
        """Test deleting a post process that has associated parts."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        # Associate part with post process
        part.post_processes.append(post_process)
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/post-processes/{post_process.id}', headers=headers)
        
        # Should either cascade or prevent deletion
        assert response.status_code in [200, 400]
    
    def test_get_post_process_parts(self, client, db_session, mock_airtable):
        """Test getting parts associated with a post process."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        post_process = TestFixtures.create_test_post_process(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Part 2')
        
        # Associate parts with post process
        part1.post_processes.append(post_process)
        part2.post_processes.append(post_process)
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/post-processes/{post_process.id}/parts', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 2
        part_names = [part['name'] for part in data]
        assert 'Part 1' in part_names
        assert 'Part 2' in part_names
    
    def test_machine_and_post_process_search(self, client, db_session, mock_airtable):
        """Test searching machines and post processes."""
        admin = TestFixtures.create_test_admin_user(db_session)
        machine1 = TestFixtures.create_test_machine(db_session, name='CNC Mill')
        machine2 = TestFixtures.create_test_machine(db_session, name='3D Printer')
        pp1 = TestFixtures.create_test_post_process(db_session, name='CNC Finishing')
        pp2 = TestFixtures.create_test_post_process(db_session, name='3D Post Processing')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Search machines
        response = client.get('/api/machines?search=CNC', headers=headers)
        data = assert_success_response(response)
        assert len(data) == 1
        assert data[0]['name'] == 'CNC Mill'
        
        # Search post processes
        response = client.get('/api/post-processes?search=3D', headers=headers)
        data = assert_success_response(response)
        assert len(data) == 1
        assert data[0]['name'] == '3D Post Processing'

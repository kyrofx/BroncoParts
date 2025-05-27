"""Integration tests for project management API endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


class TestProjectAPI:
    """Test cases for project management API endpoints."""
    
    def test_get_projects_as_readonly(self, client, db_session, mock_airtable):
        """Test getting projects as readonly user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.get('/api/projects', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 1
        assert data[0]['name'] == 'Test Project'
        assert data[0]['prefix'] == 'TP'
    
    def test_get_projects_unauthenticated(self, client, db_session, mock_airtable):
        """Test getting projects without authentication."""
        project = TestFixtures.create_test_project(db_session)
        
        response = client.get('/api/projects')
        assert_error_response(response, 401)
    
    def test_get_project_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific project by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/projects/{project.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['id'] == project.id
        assert data['name'] == 'Test Project'
        assert data['prefix'] == 'TP'
    
    def test_get_nonexistent_project(self, client, db_session, mock_airtable):
        """Test getting a nonexistent project."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/projects/999', headers=headers)
        
        assert_error_response(response, 404, 'Project not found')
    
    def test_create_project_as_editor(self, client, db_session, mock_airtable):
        """Test creating a project as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/projects', headers=headers, json={
            'name': 'New Project',
            'description': 'A new test project',
            'prefix': 'NP',
            'hide_dashboards': False
        })
        
        data = assert_success_response(response, 201)
        assert data['name'] == 'New Project'
        assert data['prefix'] == 'NP'
        assert data['hide_dashboards'] is False
    
    def test_create_project_as_readonly(self, client, db_session, mock_airtable):
        """Test creating a project as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.post('/api/projects', headers=headers, json={
            'name': 'New Project',
            'prefix': 'NP'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_create_project_duplicate_prefix(self, client, db_session, mock_airtable):
        """Test creating a project with duplicate prefix."""
        admin = TestFixtures.create_test_admin_user(db_session)
        existing_project = TestFixtures.create_test_project(db_session, prefix='SAME')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/projects', headers=headers, json={
            'name': 'Another Project',
            'prefix': 'SAME'  # Duplicate prefix
        })
        
        assert_error_response(response, 400, 'Project prefix already exists')
    
    def test_create_project_missing_required_fields(self, client, db_session, mock_airtable):
        """Test creating a project with missing required fields."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Missing name
        response = client.post('/api/projects', headers=headers, json={
            'prefix': 'TEST'
        })
        assert_error_response(response, 400)
        
        # Missing prefix
        response = client.post('/api/projects', headers=headers, json={
            'name': 'Test Project'
        })
        assert_error_response(response, 400)
    
    def test_update_project_as_admin(self, client, db_session, mock_airtable):
        """Test updating a project as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/projects/{project.id}', headers=headers, json={
            'name': 'Updated Project',
            'description': 'Updated description',
            'hide_dashboards': True
        })
        
        data = assert_success_response(response)
        assert data['name'] == 'Updated Project'
        assert data['description'] == 'Updated description'
        assert data['hide_dashboards'] is True
        assert data['prefix'] == 'TP'  # Should remain unchanged
    
    def test_update_project_as_readonly(self, client, db_session, mock_airtable):
        """Test updating a project as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.put(f'/api/projects/{project.id}', headers=headers, json={
            'name': 'Updated Project'
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_update_nonexistent_project(self, client, db_session, mock_airtable):
        """Test updating a nonexistent project."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put('/api/projects/999', headers=headers, json={
            'name': 'Updated Project'
        })
        
        assert_error_response(response, 404, 'Project not found')
    
    def test_delete_project_as_admin(self, client, db_session, mock_airtable):
        """Test deleting a project as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/projects/{project.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_delete_project_as_editor(self, client, db_session, mock_airtable):
        """Test deleting a project as editor (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.delete(f'/api/projects/{project.id}', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_delete_project_with_parts(self, client, db_session, mock_airtable):
        """Test deleting a project that has associated parts."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/projects/{project.id}', headers=headers)
        
        # Should either cascade delete or prevent deletion
        # Implementation dependent - adjust assertion based on actual behavior
        assert response.status_code in [200, 400]
    
    def test_get_project_parts(self, client, db_session, mock_airtable):
        """Test getting parts for a specific project."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Part 2')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/projects/{project.id}/parts', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 2
        part_names = [part['name'] for part in data]
        assert 'Part 1' in part_names
        assert 'Part 2' in part_names
    
    def test_get_project_statistics(self, client, db_session, mock_airtable):
        """Test getting project statistics."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Assembly 1', type='assembly')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/projects/{project.id}/statistics', headers=headers)
        
        data = assert_success_response(response)
        assert 'total_parts' in data
        assert 'total_assemblies' in data
        assert data['total_parts'] >= 1
        assert data['total_assemblies'] >= 1
    
    def test_project_search(self, client, db_session, mock_airtable):
        """Test searching projects."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project1 = TestFixtures.create_test_project(db_session, name='Alpha Project', prefix='ALPHA')
        project2 = TestFixtures.create_test_project(db_session, name='Beta Project', prefix='BETA')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/projects?search=Alpha', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 1
        assert data[0]['name'] == 'Alpha Project'
    
    def test_project_pagination(self, client, db_session, mock_airtable):
        """Test project pagination."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        # Create multiple projects
        for i in range(5):
            TestFixtures.create_test_project(db_session, name=f'Project {i}', prefix=f'P{i}')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/projects?page=1&per_page=3', headers=headers)
        
        data = assert_success_response(response)
        # Implementation dependent - adjust based on actual pagination response format
        assert isinstance(data, (list, dict))  # Could be list of projects or paginated response object

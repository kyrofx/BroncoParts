import pytest
import json
from app.models import Project, Part, db
from tests.conftest import get_auth_headers


class TestProjectRoutes:
    
    @pytest.mark.api
    def test_get_projects_empty(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/projects', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['projects'] == []

    @pytest.mark.api
    def test_get_projects_with_data(self, client, readonly_token, sample_project):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/projects', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['projects']) == 1
        assert data['projects'][0]['name'] == 'Test Project'
        assert data['projects'][0]['prefix'] == 'TP'

    @pytest.mark.api
    def test_get_project_by_id(self, client, readonly_token, sample_project):
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/projects/{sample_project.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['project']['name'] == 'Test Project'
        assert data['project']['prefix'] == 'TP'
        assert data['project']['description'] == 'A test project for testing'

    @pytest.mark.api
    def test_get_project_not_found(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/projects/999', headers=headers)
        
        assert response.status_code == 404

    @pytest.mark.api
    def test_create_project_success(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        project_data = {
            'name': 'New Project',
            'prefix': 'NP',
            'description': 'A new test project',
            'hide_dashboards': True
        }
        
        response = client.post('/api/projects', headers=headers, json=project_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Project created successfully' in data['message']
        assert data['project']['name'] == 'New Project'
        assert data['project']['prefix'] == 'NP'
        assert data['project']['hide_dashboards'] is True

    @pytest.mark.api
    def test_create_project_missing_required_fields(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        # Missing name
        response = client.post('/api/projects', headers=headers, 
                             json={'prefix': 'NP'})
        assert response.status_code == 400
        
        # Missing prefix
        response = client.post('/api/projects', headers=headers, 
                             json={'name': 'New Project'})
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_project_duplicate_prefix(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)
        project_data = {
            'name': 'Another Project',
            'prefix': 'TP',  # Same as sample_project
            'description': 'Another test project'
        }
        
        response = client.post('/api/projects', headers=headers, json=project_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_project_readonly_forbidden(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        project_data = {
            'name': 'New Project',
            'prefix': 'NP',
            'description': 'A new test project'
        }
        
        response = client.post('/api/projects', headers=headers, json=project_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_update_project_success(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)
        update_data = {
            'name': 'Updated Project',
            'description': 'Updated description',
            'hide_dashboards': True
        }
        
        response = client.put(f'/api/projects/{sample_project.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Project updated successfully' in data['message']
        assert data['project']['name'] == 'Updated Project'
        assert data['project']['description'] == 'Updated description'
        assert data['project']['hide_dashboards'] is True

    @pytest.mark.api
    def test_update_project_partial(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)
        update_data = {'name': 'Partially Updated Project'}
        
        response = client.put(f'/api/projects/{sample_project.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['project']['name'] == 'Partially Updated Project'
        assert data['project']['prefix'] == 'TP'  # Should remain unchanged

    @pytest.mark.api
    def test_update_project_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        update_data = {'name': 'Updated Project'}
        
        response = client.put('/api/projects/999', headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_update_project_readonly_forbidden(self, client, readonly_token, sample_project):
        headers = get_auth_headers(readonly_token)
        update_data = {'name': 'Updated Project'}
        
        response = client.put(f'/api/projects/{sample_project.id}', 
                            headers=headers, json=update_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_project_success(self, client, admin_token, sample_project):
        headers = get_auth_headers(admin_token)
        
        response = client.delete(f'/api/projects/{sample_project.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Project deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_project_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        
        response = client.delete('/api/projects/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_project_editor_forbidden(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)

        response = client.delete(f'/api/projects/{sample_project.id}', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_onshape_config_crud(self, client, admin_token, sample_project):
        headers = get_auth_headers(admin_token)

        data = {
            'document_id': 'doc123',
            'workspace_id': 'ws123',
            'naming_scheme': 'OS'
        }
        resp = client.put(f'/api/projects/{sample_project.id}/onshape', headers=headers, json=data)
        assert resp.status_code == 200
        fetched = client.get(f'/api/projects/{sample_project.id}/onshape', headers=headers)
        assert fetched.status_code == 200
        info = json.loads(fetched.data)
        assert info['config']['document_id'] == 'doc123'

    @pytest.mark.api
    def test_get_project_tree(self, client, readonly_token, app, sample_project):
        # Create a hierarchical structure for testing
        with app.app_context():
            assembly = Part(
                name='Main Assembly',
                part_number='TP-A-0001',
                numeric_id=1,
                type='assembly',
                project_id=sample_project.id,
                quantity=1
            )
            db.session.add(assembly)
            db.session.commit()
            
            part1 = Part(
                name='Part 1',
                part_number='TP-P-0002',
                numeric_id=2,
                type='part',
                project_id=sample_project.id,
                parent_id=assembly.id,
                quantity=2
            )
            part2 = Part(
                name='Part 2',
                part_number='TP-P-0003',
                numeric_id=3,
                type='part',
                project_id=sample_project.id,
                parent_id=assembly.id,
                quantity=1
            )
            db.session.add_all([part1, part2])
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/projects/{sample_project.id}/tree', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tree' in data
        assert len(data['tree']) >= 1  # Should have at least the assembly

    @pytest.mark.api
    def test_get_project_assemblies(self, client, readonly_token, app, sample_project):
        # Create assemblies for testing
        with app.app_context():
            assembly1 = Part(
                name='Assembly 1',
                part_number='TP-A-0001',
                numeric_id=1,
                type='assembly',
                project_id=sample_project.id,
                quantity=1
            )
            assembly2 = Part(
                name='Assembly 2',
                part_number='TP-A-0002',
                numeric_id=2,
                type='assembly',
                project_id=sample_project.id,
                quantity=1
            )
            regular_part = Part(
                name='Regular Part',
                part_number='TP-P-0003',
                numeric_id=3,
                type='part',
                project_id=sample_project.id,
                quantity=1
            )
            db.session.add_all([assembly1, assembly2, regular_part])
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/projects/{sample_project.id}/assemblies', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'assemblies' in data
        assert len(data['assemblies']) == 2  # Only assemblies, not regular parts

    @pytest.mark.api
    def test_get_project_parts(self, client, readonly_token, app, sample_project):
        # Create parts for testing
        with app.app_context():
            part1 = Part(
                name='Part 1',
                part_number='TP-P-0001',
                numeric_id=1,
                type='part',
                project_id=sample_project.id,
                quantity=1
            )
            part2 = Part(
                name='Part 2',
                part_number='TP-P-0002',
                numeric_id=2,
                type='part',
                project_id=sample_project.id,
                quantity=2
            )
            db.session.add_all([part1, part2])
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/projects/{sample_project.id}/parts', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'parts' in data
        assert len(data['parts']) == 2

    @pytest.mark.api
    def test_project_routes_require_authentication(self, client):
        # Test all project routes without authentication
        endpoints = [
            ('GET', '/api/projects'),
            ('POST', '/api/projects'),
            ('GET', '/api/projects/1'),
            ('PUT', '/api/projects/1'),
            ('DELETE', '/api/projects/1'),
            ('GET', '/api/projects/1/tree'),
            ('GET', '/api/projects/1/assemblies'),
            ('GET', '/api/projects/1/parts')
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={})
            elif method == 'PUT':
                response = client.put(endpoint, json={})
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401
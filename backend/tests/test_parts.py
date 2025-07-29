import pytest
import json
from app.models import Part, db
from tests.conftest import get_auth_headers


class TestPartRoutes:
    
    @pytest.mark.api
    def test_get_parts_empty(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/parts', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['parts'] == []

    @pytest.mark.api
    def test_get_parts_with_data(self, client, readonly_token, sample_part):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/parts', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['parts']) >= 1
        
        # Find our test part
        test_part = None
        for part in data['parts']:
            if part['part_number'] == 'TP-P-0002':
                test_part = part
                break
        
        assert test_part is not None
        assert test_part['name'] == 'Test Part'
        assert test_part['type'] == 'part'

    @pytest.mark.api
    def test_get_parts_with_filtering(self, client, readonly_token, app, sample_project):
        # Create multiple parts for filtering tests
        with app.app_context():
            parts = [
                Part(name='Part A', part_number='TP-P-0001', numeric_id=1, 
                     type='part', project_id=sample_project.id, quantity=1, status='in design'),
                Part(name='Part B', part_number='TP-P-0002', numeric_id=2, 
                     type='part', project_id=sample_project.id, quantity=1, status='ready for manufacturing'),
                Part(name='Assembly A', part_number='TP-A-0003', numeric_id=3, 
                     type='assembly', project_id=sample_project.id, quantity=1, status='in design')
            ]
            db.session.add_all(parts)
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        
        # Test filtering by project
        response = client.get(f'/api/parts?project_id={sample_project.id}', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['parts']) == 3
        
        # Test filtering by type
        response = client.get('/api/parts?type=part', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        part_types = [part['type'] for part in data['parts']]
        assert all(ptype == 'part' for ptype in part_types)
        
        # Test filtering by status
        response = client.get('/api/parts?status=in design', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        statuses = [part['status'] for part in data['parts']]
        assert all(status == 'in design' for status in statuses)

    @pytest.mark.api
    def test_get_part_by_id(self, client, readonly_token, sample_part):
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/parts/{sample_part.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['part']['name'] == 'Test Part'
        assert data['part']['part_number'] == 'TP-P-0002'
        assert data['part']['type'] == 'part'
        assert data['part']['quantity'] == 5
        assert data['part']['raw_material'] == 'Steel'

    @pytest.mark.api
    def test_get_part_not_found(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/parts/999', headers=headers)
        
        assert response.status_code == 404

    @pytest.mark.api
    def test_create_part_success(self, client, editor_token, sample_project, sample_machine, sample_post_process):
        headers = get_auth_headers(editor_token)
        part_data = {
            'name': 'New Test Part',
            'description': 'A new test part',
            'type': 'part',
            'project_id': sample_project.id,
            'machine_id': sample_machine.id,
            'post_process_ids': [sample_post_process.id],
            'quantity': 3,
            'raw_material': 'Aluminum',
            'status': 'in design'
        }
        
        response = client.post('/api/parts', headers=headers, json=part_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Part created successfully' in data['message']
        assert data['part']['name'] == 'New Test Part'
        assert data['part']['type'] == 'part'
        assert data['part']['quantity'] == 3
        assert data['part']['raw_material'] == 'Aluminum'

    @pytest.mark.api
    def test_create_assembly_success(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)
        assembly_data = {
            'name': 'New Test Assembly',
            'description': 'A new test assembly',
            'type': 'assembly',
            'project_id': sample_project.id,
            'quantity': 1,
            'status': 'in design'
        }
        
        response = client.post('/api/parts', headers=headers, json=assembly_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Part created successfully' in data['message']
        assert data['part']['name'] == 'New Test Assembly'
        assert data['part']['type'] == 'assembly'
        assert data['part']['quantity'] == 1

    @pytest.mark.api
    def test_create_part_with_parent(self, client, editor_token, sample_assembly, sample_machine):
        headers = get_auth_headers(editor_token)
        part_data = {
            'name': 'Child Part',
            'description': 'A part that belongs to an assembly',
            'type': 'part',
            'project_id': sample_assembly.project_id,
            'parent_id': sample_assembly.id,
            'machine_id': sample_machine.id,
            'quantity': 2,
            'status': 'in design'
        }
        
        response = client.post('/api/parts', headers=headers, json=part_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['part']['parent_id'] == sample_assembly.id

    @pytest.mark.api
    def test_create_part_missing_required_fields(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        # Missing name
        response = client.post('/api/parts', headers=headers, 
                             json={'type': 'part', 'project_id': 1})
        assert response.status_code == 400
        
        # Missing type
        response = client.post('/api/parts', headers=headers, 
                             json={'name': 'Test Part', 'project_id': 1})
        assert response.status_code == 400
        
        # Missing project_id
        response = client.post('/api/parts', headers=headers, 
                             json={'name': 'Test Part', 'type': 'part'})
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_part_invalid_project(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        part_data = {
            'name': 'Test Part',
            'type': 'part',
            'project_id': 999,  # Non-existent project
            'quantity': 1
        }
        
        response = client.post('/api/parts', headers=headers, json=part_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_part_readonly_forbidden(self, client, readonly_token, sample_project):
        headers = get_auth_headers(readonly_token)
        part_data = {
            'name': 'Test Part',
            'type': 'part',
            'project_id': sample_project.id,
            'quantity': 1
        }
        
        response = client.post('/api/parts', headers=headers, json=part_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_update_part_success(self, client, editor_token, sample_part):
        headers = get_auth_headers(editor_token)
        update_data = {
            'name': 'Updated Part Name',
            'description': 'Updated description',
            'quantity': 10,
            'status': 'ready for manufacturing'
        }
        
        response = client.put(f'/api/parts/{sample_part.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Part updated successfully' in data['message']
        assert data['part']['name'] == 'Updated Part Name'
        assert data['part']['quantity'] == 10
        assert data['part']['status'] == 'ready for manufacturing'

    @pytest.mark.api
    def test_update_part_partial(self, client, editor_token, sample_part):
        headers = get_auth_headers(editor_token)
        update_data = {'quantity': 8}
        
        response = client.put(f'/api/parts/{sample_part.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['part']['quantity'] == 8
        assert data['part']['name'] == 'Test Part'  # Should remain unchanged

    @pytest.mark.api
    def test_update_part_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        update_data = {'name': 'Updated Part'}
        
        response = client.put('/api/parts/999', headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_update_part_readonly_forbidden(self, client, readonly_token, sample_part):
        headers = get_auth_headers(readonly_token)
        update_data = {'name': 'Updated Part'}
        
        response = client.put(f'/api/parts/{sample_part.id}', 
                            headers=headers, json=update_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_part_success(self, client, editor_token, sample_part):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/parts/{sample_part.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Part deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_part_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        response = client.delete('/api/parts/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_part_readonly_forbidden(self, client, readonly_token, sample_part):
        headers = get_auth_headers(readonly_token)
        
        response = client.delete(f'/api/parts/{sample_part.id}', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_get_derived_hierarchy_info(self, client, readonly_token, app, sample_project):
        # Create a hierarchical structure
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
            db.session.add_all([assembly1, assembly2])
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/parts/derived-hierarchy-info', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'subteams' in data
        assert 'subsystems' in data

    @pytest.mark.api
    def test_part_number_generation(self, client, editor_token, sample_project):
        """Test that part numbers are generated correctly based on project prefix and type"""
        headers = get_auth_headers(editor_token)
        
        # Create an assembly
        assembly_data = {
            'name': 'Test Assembly',
            'type': 'assembly',
            'project_id': sample_project.id,
            'quantity': 1
        }
        response = client.post('/api/parts', headers=headers, json=assembly_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'TP-A-' in data['part']['part_number']  # Assembly format
        
        # Create a part
        part_data = {
            'name': 'Test Part',
            'type': 'part',
            'project_id': sample_project.id,
            'quantity': 1
        }
        response = client.post('/api/parts', headers=headers, json=part_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'TP-P-' in data['part']['part_number']  # Part format

    @pytest.mark.api
    def test_part_relationships_in_response(self, client, readonly_token, sample_part):
        """Test that part responses include relationship data"""
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/parts/{sample_part.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        part_data = data['part']
        
        # Should include machine data
        assert 'machine' in part_data
        if part_data['machine']:
            assert 'name' in part_data['machine']
        
        # Should include post-process data
        assert 'post_processes' in part_data
        
        # Should include project data
        assert 'project' in part_data
        if part_data['project']:
            assert 'name' in part_data['project']

    @pytest.mark.api
    def test_parts_require_authentication(self, client):
        """Test that all part routes require authentication"""
        endpoints = [
            ('GET', '/api/parts'),
            ('POST', '/api/parts'),
            ('GET', '/api/parts/1'),
            ('PUT', '/api/parts/1'),
            ('DELETE', '/api/parts/1'),
            ('GET', '/api/parts/derived-hierarchy-info')
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
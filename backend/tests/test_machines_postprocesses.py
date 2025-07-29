import pytest
import json
from unittest.mock import patch, MagicMock
from app.models import Machine, PostProcess, db
from tests.conftest import get_auth_headers


class TestMachineRoutes:
    
    @pytest.mark.api
    def test_get_machines_empty(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/machines', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['machines'] == []

    @pytest.mark.api
    def test_get_machines_with_data(self, client, readonly_token, sample_machine):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/machines', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['machines']) == 1
        assert data['machines'][0]['name'] == 'Test Machine'
        assert data['machines'][0]['is_active'] is True

    @pytest.mark.api
    def test_create_machine_success(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        machine_data = {
            'name': 'CNC Mill',
            'is_active': True
        }
        
        response = client.post('/api/machines', headers=headers, json=machine_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Machine created successfully' in data['message']
        assert data['machine']['name'] == 'CNC Mill'
        assert data['machine']['is_active'] is True

    @pytest.mark.api
    def test_create_machine_missing_name(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        machine_data = {'is_active': True}
        
        response = client.post('/api/machines', headers=headers, json=machine_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_machine_duplicate_name(self, client, editor_token, sample_machine):
        headers = get_auth_headers(editor_token)
        machine_data = {
            'name': 'Test Machine',  # Same as sample_machine
            'is_active': True
        }
        
        response = client.post('/api/machines', headers=headers, json=machine_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_machine_readonly_forbidden(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        machine_data = {
            'name': 'New Machine',
            'is_active': True
        }
        
        response = client.post('/api/machines', headers=headers, json=machine_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_machine_success(self, client, editor_token, sample_machine):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/machines/{sample_machine.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Machine deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_machine_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        response = client.delete('/api/machines/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_machine_readonly_forbidden(self, client, readonly_token, sample_machine):
        headers = get_auth_headers(readonly_token)
        
        response = client.delete(f'/api/machines/{sample_machine.id}', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_get_machine_airtable_options(self, mock_get_options, mock_get_table, client, readonly_token):
        # Mock Airtable responses
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_get_options.return_value = ['CNC Mill', 'Lathe', '3D Printer']
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/machines/airtable-options', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'options' in data
        assert len(data['options']) == 3
        assert 'CNC Mill' in data['options']

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    def test_get_machine_airtable_options_no_table(self, mock_get_table, client, readonly_token):
        # Mock Airtable table not available
        mock_get_table.return_value = None
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/machines/airtable-options', headers=headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'Airtable not configured' in data['message']

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_machines_with_airtable(self, mock_get_options, mock_get_table, client, editor_token, app):
        # Mock Airtable responses
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_get_options.return_value = ['CNC Mill', 'Lathe', 'New Machine']
        
        # Add existing machine
        with app.app_context():
            existing_machine = Machine(name='CNC Mill', is_active=True)
            db.session.add(existing_machine)
            db.session.commit()
        
        headers = get_auth_headers(editor_token)
        response = client.post('/api/machines/sync-with-airtable', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sync_results' in data
        assert data['sync_results']['new_machines_created'] >= 0


class TestPostProcessRoutes:
    
    @pytest.mark.api
    def test_get_post_processes_empty(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/post-processes', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['post_processes'] == []

    @pytest.mark.api
    def test_get_post_processes_with_data(self, client, readonly_token, sample_post_process):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/post-processes', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['post_processes']) == 1
        assert data['post_processes'][0]['name'] == 'Test Post Process'
        assert data['post_processes'][0]['is_active'] is True

    @pytest.mark.api
    def test_create_post_process_success(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        pp_data = {
            'name': 'Anodizing',
            'description': 'Aluminum anodizing process',
            'is_active': True
        }
        
        response = client.post('/api/post-processes', headers=headers, json=pp_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Post-process created successfully' in data['message']
        assert data['post_process']['name'] == 'Anodizing'
        assert data['post_process']['description'] == 'Aluminum anodizing process'
        assert data['post_process']['is_active'] is True

    @pytest.mark.api
    def test_create_post_process_missing_name(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        pp_data = {'description': 'A process without name'}
        
        response = client.post('/api/post-processes', headers=headers, json=pp_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_post_process_duplicate_name(self, client, editor_token, sample_post_process):
        headers = get_auth_headers(editor_token)
        pp_data = {
            'name': 'Test Post Process',  # Same as sample_post_process
            'description': 'Duplicate process'
        }
        
        response = client.post('/api/post-processes', headers=headers, json=pp_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_post_process_readonly_forbidden(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        pp_data = {
            'name': 'New Process',
            'description': 'A new process'
        }
        
        response = client.post('/api/post-processes', headers=headers, json=pp_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_post_process_success(self, client, editor_token, sample_post_process):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/post-processes/{sample_post_process.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Post-process deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_post_process_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        response = client.delete('/api/post-processes/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_post_process_readonly_forbidden(self, client, readonly_token, sample_post_process):
        headers = get_auth_headers(readonly_token)
        
        response = client.delete(f'/api/post-processes/{sample_post_process.id}', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_get_post_process_airtable_options(self, mock_get_options, mock_get_table, client, readonly_token):
        # Mock Airtable responses
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_get_options.return_value = ['Anodizing', 'Powder Coating', 'Heat Treatment']
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/post-processes/airtable-options', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'options' in data
        assert len(data['options']) == 3
        assert 'Anodizing' in data['options']

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    def test_get_post_process_airtable_options_no_table(self, mock_get_table, client, readonly_token):
        # Mock Airtable table not available
        mock_get_table.return_value = None
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/post-processes/airtable-options', headers=headers)
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'Airtable not configured' in data['message']

    @pytest.mark.api
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_post_processes_with_airtable(self, mock_get_options, mock_get_table, client, editor_token, app):
        # Mock Airtable responses
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_get_options.return_value = ['Anodizing', 'Powder Coating', 'New Process']
        
        # Add existing post process
        with app.app_context():
            existing_pp = PostProcess(name='Anodizing', is_active=True)
            db.session.add(existing_pp)
            db.session.commit()
        
        headers = get_auth_headers(editor_token)
        response = client.post('/api/post-processes/sync-with-airtable', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sync_results' in data
        assert data['sync_results']['new_post_processes_created'] >= 0

    @pytest.mark.api
    def test_machine_and_post_process_routes_require_authentication(self, client):
        """Test that all machine and post-process routes require authentication"""
        endpoints = [
            ('GET', '/api/machines'),
            ('POST', '/api/machines'),
            ('DELETE', '/api/machines/1'),
            ('GET', '/api/machines/airtable-options'),
            ('POST', '/api/machines/sync-with-airtable'),
            ('GET', '/api/post-processes'),
            ('POST', '/api/post-processes'),
            ('DELETE', '/api/post-processes/1'),
            ('GET', '/api/post-processes/airtable-options'),
            ('POST', '/api/post-processes/sync-with-airtable')
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={})
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401


class TestAirtableIntegration:
    
    @pytest.mark.integration
    @patch('app.services.airtable_service.get_airtable_table')
    def test_airtable_sync_machine_creation(self, mock_get_table, client, editor_token, app):
        """Test that new machines created from Airtable sync are properly stored"""
        # Mock Airtable table
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        with patch('app.services.airtable_service.get_airtable_select_options') as mock_get_options:
            mock_get_options.return_value = ['CNC Mill', 'Lathe', 'Router']
            
            headers = get_auth_headers(editor_token)
            response = client.post('/api/machines/sync-with-airtable', headers=headers)
            
            assert response.status_code == 200
            
            # Verify machines were created in database
            with app.app_context():
                machines = Machine.query.all()
                machine_names = [m.name for m in machines]
                assert 'CNC Mill' in machine_names
                assert 'Lathe' in machine_names
                assert 'Router' in machine_names

    @pytest.mark.integration
    @patch('app.services.airtable_service.get_airtable_table')
    def test_airtable_sync_post_process_creation(self, mock_get_table, client, editor_token, app):
        """Test that new post processes created from Airtable sync are properly stored"""
        # Mock Airtable table
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        with patch('app.services.airtable_service.get_airtable_select_options') as mock_get_options:
            mock_get_options.return_value = ['Anodizing', 'Powder Coating', 'Heat Treatment']
            
            headers = get_auth_headers(editor_token)
            response = client.post('/api/post-processes/sync-with-airtable', headers=headers)
            
            assert response.status_code == 200
            
            # Verify post processes were created in database
            with app.app_context():
                post_processes = PostProcess.query.all()
                pp_names = [pp.name for pp in post_processes]
                assert 'Anodizing' in pp_names
                assert 'Powder Coating' in pp_names
                assert 'Heat Treatment' in pp_names

    @pytest.mark.integration
    def test_airtable_sync_handles_duplicates(self, client, editor_token, app, sample_machine):
        """Test that Airtable sync doesn't create duplicates of existing machines/post processes"""
        with patch('app.services.airtable_service.get_airtable_table') as mock_get_table:
            mock_table = MagicMock()
            mock_get_table.return_value = mock_table
            
            with patch('app.services.airtable_service.get_airtable_select_options') as mock_get_options:
                # Include existing machine name in Airtable options
                mock_get_options.return_value = ['Test Machine', 'New Machine']
                
                headers = get_auth_headers(editor_token)
                response = client.post('/api/machines/sync-with-airtable', headers=headers)
                
                assert response.status_code == 200
                
                # Verify no duplicate was created
                with app.app_context():
                    test_machines = Machine.query.filter_by(name='Test Machine').all()
                    assert len(test_machines) == 1  # Should still be only one
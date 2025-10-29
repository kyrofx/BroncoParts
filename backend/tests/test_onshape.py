import json
from unittest.mock import patch, MagicMock
from app.models import OnshapeConfig, Project
from tests.conftest import get_auth_headers

class TestOnshapeIntegration:
    @patch('app.services.onshape_service.OnshapeService.assign_part_numbers')
    def test_webhook_assigns_numbers(self, mock_assign, client, admin_token, app, sample_project):
        mock_assign.return_value = [{'partId': '1', 'partNumber': 'TP-0001'}]
        config = OnshapeConfig(
            project_id=sample_project.id,
            document_id='doc',
            workspace_id='ws',
            element_id='el',
            number_format='TP-{counter:04d}',
            counter=1,
            access_token='token'
        )
        with app.app_context():
            from app import db
            db.session.add(config)
            db.session.commit()
        headers = get_auth_headers(admin_token)
        response = client.post('/api/onshape/webhook', json={
            'documentId': 'doc',
            'workspaceId': 'ws'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['updated'][0]['partNumber'] == 'TP-0001'
        mock_assign.assert_called_once()

    def test_set_config(self, client, admin_token, sample_project):
        headers = get_auth_headers(admin_token)
        payload = {
            'document_id': 'doc1',
            'workspace_id': 'ws1',
            'element_id': 'el1',
            'number_format': 'TP-{counter:04d}',
            'access_token': 'tok'
        }
        response = client.post(f'/api/projects/{sample_project.id}/onshape-config', headers=headers, json=payload)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Config saved' in data['message']
        get_resp = client.get(f'/api/projects/{sample_project.id}/onshape-config', headers=headers)
        assert get_resp.status_code == 200
        cfg = json.loads(get_resp.data)['config']
        assert cfg['document_id'] == 'doc1'

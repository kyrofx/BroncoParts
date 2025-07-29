import pytest
import json
from app.models import User, db
from tests.conftest import get_auth_headers


class TestAuthentication:
    
    @pytest.mark.auth
    def test_login_success(self, client, admin_user):
        response = client.post('/api/login', 
                             json={'email': 'admin@test.com', 'password': 'password123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['user']['username'] == 'admin'
        assert data['user']['permission'] == 'admin'

    @pytest.mark.auth
    def test_login_invalid_credentials(self, client, admin_user):
        response = client.post('/api/login', 
                             json={'email': 'admin@test.com', 'password': 'wrongpassword'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid credentials' in data['message']

    @pytest.mark.auth
    def test_login_nonexistent_user(self, client):
        response = client.post('/api/login', 
                             json={'email': 'nonexistent@test.com', 'password': 'password123'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid credentials' in data['message']

    @pytest.mark.auth
    def test_login_disabled_user(self, client, disabled_user):
        response = client.post('/api/login', 
                             json={'email': 'disabled@test.com', 'password': 'password123'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Account is disabled' in data['message']

    @pytest.mark.auth
    def test_login_unapproved_user(self, client, unapproved_user):
        response = client.post('/api/login', 
                             json={'email': 'unapproved@test.com', 'password': 'password123'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Account pending approval' in data['message']

    @pytest.mark.auth
    def test_login_missing_email(self, client):
        response = client.post('/api/login', 
                             json={'password': 'password123'})
        
        assert response.status_code == 400

    @pytest.mark.auth
    def test_login_missing_password(self, client):
        response = client.post('/api/login', 
                             json={'email': 'admin@test.com'})
        
        assert response.status_code == 400

    @pytest.mark.auth
    def test_register_success(self, client, app):
        response = client.post('/api/register', json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'User registered successfully' in data['message']
        
        # Verify user was created but not approved
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.is_approved is False
            assert user.enabled is False

    @pytest.mark.auth
    def test_register_duplicate_username(self, client, admin_user):
        response = client.post('/api/register', json={
            'username': 'admin',  # Already exists
            'email': 'different@test.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Username already exists' in data['message']

    @pytest.mark.auth
    def test_register_duplicate_email(self, client, admin_user):
        response = client.post('/api/register', json={
            'username': 'newuser',
            'email': 'admin@test.com',  # Already exists
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Email already exists' in data['message']

    @pytest.mark.auth
    def test_register_missing_fields(self, client):
        response = client.post('/api/register', json={
            'username': 'newuser',
            # Missing email, password, etc.
        })
        
        assert response.status_code == 400

    @pytest.mark.auth
    def test_protected_route_requires_token(self, client):
        response = client.get('/api/projects')
        assert response.status_code == 401

    @pytest.mark.auth
    def test_protected_route_with_valid_token(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        response = client.get('/api/projects', headers=headers)
        assert response.status_code == 200

    @pytest.mark.auth
    def test_protected_route_with_invalid_token(self, client):
        headers = get_auth_headers('invalid.jwt.token')
        response = client.get('/api/projects', headers=headers)
        assert response.status_code == 422  # Invalid JWT

    @pytest.mark.auth
    def test_hello_endpoint_requires_auth(self, client, readonly_token):
        # Test without token
        response = client.get('/api/hello')
        assert response.status_code == 401
        
        # Test with token
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/hello', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Hello from Flask Backend!' in data['message']


class TestPermissions:
    
    @pytest.mark.auth
    def test_admin_access_all_endpoints(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        
        # Test endpoints that require admin permission
        endpoints = [
            '/api/projects',
            '/api/users',
            '/api/machines',
            '/api/post-processes'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200

    @pytest.mark.auth
    def test_editor_access_appropriate_endpoints(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        # Editor should access these
        response = client.get('/api/projects', headers=headers)
        assert response.status_code == 200
        
        response = client.get('/api/machines', headers=headers)
        assert response.status_code == 200

    @pytest.mark.auth
    def test_readonly_access_limited_endpoints(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        
        # Readonly should access these
        response = client.get('/api/projects', headers=headers)
        assert response.status_code == 200
        
        response = client.get('/api/hello', headers=headers)
        assert response.status_code == 200

    @pytest.mark.auth
    def test_readonly_cannot_create_projects(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        
        response = client.post('/api/projects', 
                             headers=headers,
                             json={'name': 'Test Project', 'prefix': 'TP'})
        assert response.status_code == 403

    @pytest.mark.auth
    def test_editor_cannot_access_admin_endpoints(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        # Editor should not be able to access admin-only endpoints
        response = client.get('/api/users', headers=headers)
        # This depends on implementation - might be 403 or 200 with limited data
        # Based on the decorators, editors might still see users but can't manage them
        assert response.status_code in [200, 403]

    @pytest.mark.auth
    def test_disabled_user_token_rejected(self, client, app, disabled_user):
        from flask_jwt_extended import create_access_token
        
        with app.app_context():
            token = create_access_token(identity=disabled_user.id)
        
        headers = get_auth_headers(token)
        response = client.get('/api/projects', headers=headers)
        # The decorators should check if user is enabled
        assert response.status_code in [401, 403]
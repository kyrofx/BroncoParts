import pytest
import json
from app.models import User, RegistrationLink, db
from tests.conftest import get_auth_headers
from datetime import datetime, timedelta


class TestUserRoutes:
    
    @pytest.mark.api
    def test_get_users_as_admin(self, client, admin_token, admin_user, editor_user, readonly_user):
        headers = get_auth_headers(admin_token)
        response = client.get('/api/users', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['users']) >= 3  # At least the three test users
        
        usernames = [user['username'] for user in data['users']]
        assert 'admin' in usernames
        assert 'editor' in usernames
        assert 'readonly' in usernames

    @pytest.mark.api
    def test_get_users_as_readonly(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/users', headers=headers)
        
        # Readonly users should still be able to see users (based on decorator)
        assert response.status_code == 200

    @pytest.mark.api
    def test_get_user_by_id(self, client, admin_token, editor_user):
        headers = get_auth_headers(admin_token)
        response = client.get(f'/api/users/{editor_user.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['username'] == 'editor'
        assert data['user']['email'] == 'editor@test.com'
        assert data['user']['permission'] == 'editor'

    @pytest.mark.api
    def test_get_user_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        response = client.get('/api/users/999', headers=headers)
        
        assert response.status_code == 404

    @pytest.mark.api
    def test_create_user_as_admin(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        user_data = {
            'username': 'newadminuser',
            'email': 'newadmin@test.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Admin',
            'permission': 'editor',
            'enabled': True
        }
        
        response = client.post('/api/admin/users', headers=headers, json=user_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'User created successfully' in data['message']
        assert data['user']['username'] == 'newadminuser'
        assert data['user']['permission'] == 'editor'
        assert data['user']['enabled'] is True

    @pytest.mark.api
    def test_create_user_duplicate_username(self, client, admin_token, admin_user):
        headers = get_auth_headers(admin_token)
        user_data = {
            'username': 'admin',  # Already exists
            'email': 'different@test.com',
            'password': 'password123',
            'permission': 'readonly'
        }
        
        response = client.post('/api/admin/users', headers=headers, json=user_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_user_duplicate_email(self, client, admin_token, admin_user):
        headers = get_auth_headers(admin_token)
        user_data = {
            'username': 'different',
            'email': 'admin@test.com',  # Already exists
            'password': 'password123',
            'permission': 'readonly'
        }
        
        response = client.post('/api/admin/users', headers=headers, json=user_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_user_editor_forbidden(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        user_data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'permission': 'readonly'
        }
        
        response = client.post('/api/admin/users', headers=headers, json=user_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_update_user_as_admin(self, client, admin_token, editor_user):
        headers = get_auth_headers(admin_token)
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'permission': 'readonly',
            'enabled': False
        }
        
        response = client.put(f'/api/users/{editor_user.id}', headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'User updated successfully' in data['message']
        assert data['user']['first_name'] == 'Updated'
        assert data['user']['permission'] == 'readonly'
        assert data['user']['enabled'] is False

    @pytest.mark.api
    def test_update_user_partial(self, client, admin_token, editor_user):
        headers = get_auth_headers(admin_token)
        update_data = {'enabled': False}
        
        response = client.put(f'/api/users/{editor_user.id}', headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['enabled'] is False
        assert data['user']['username'] == 'editor'  # Should remain unchanged

    @pytest.mark.api
    def test_update_user_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        update_data = {'enabled': False}
        
        response = client.put('/api/users/999', headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_update_user_editor_forbidden(self, client, editor_token, readonly_user):
        headers = get_auth_headers(editor_token)
        update_data = {'enabled': False}
        
        response = client.put(f'/api/users/{readonly_user.id}', headers=headers, json=update_data)
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_user_as_admin(self, client, admin_token, app):
        # Create a user to delete
        with app.app_context():
            user_to_delete = User(
                username='deleteuser',
                email='delete@test.com',
                permission='readonly'
            )
            user_to_delete.set_password('password')
            db.session.add(user_to_delete)
            db.session.commit()
            user_id = user_to_delete.id
        
        headers = get_auth_headers(admin_token)
        response = client.delete(f'/api/users/{user_id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'User deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_user_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        response = client.delete('/api/users/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_user_editor_forbidden(self, client, editor_token, readonly_user):
        headers = get_auth_headers(editor_token)
        response = client.delete(f'/api/users/{readonly_user.id}', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_approve_user(self, client, admin_token, unapproved_user):
        headers = get_auth_headers(admin_token)
        response = client.post(f'/api/users/{unapproved_user.id}/approve', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'User approved successfully' in data['message']
        assert data['user']['is_approved'] is True

    @pytest.mark.api
    def test_approve_user_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        response = client.post('/api/users/999/approve', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_approve_user_editor_forbidden(self, client, editor_token, unapproved_user):
        headers = get_auth_headers(editor_token)
        response = client.post(f'/api/users/{unapproved_user.id}/approve', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_change_user_password(self, client, admin_token, editor_user, app):
        headers = get_auth_headers(admin_token)
        password_data = {'new_password': 'newpassword123'}
        
        response = client.put(f'/api/users/{editor_user.id}/change-password', 
                            headers=headers, json=password_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Password changed successfully' in data['message']
        
        # Verify password was actually changed
        with app.app_context():
            user = User.query.get(editor_user.id)
            assert user.check_password('newpassword123')
            assert not user.check_password('password123')  # Old password should not work

    @pytest.mark.api
    def test_change_password_missing_password(self, client, admin_token, editor_user):
        headers = get_auth_headers(admin_token)
        password_data = {}  # Missing new_password
        
        response = client.put(f'/api/users/{editor_user.id}/change-password', 
                            headers=headers, json=password_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_change_password_user_not_found(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        password_data = {'new_password': 'newpassword123'}
        
        response = client.put('/api/users/999/change-password', 
                            headers=headers, json=password_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_change_password_editor_forbidden(self, client, editor_token, readonly_user):
        headers = get_auth_headers(editor_token)
        password_data = {'new_password': 'newpassword123'}
        
        response = client.put(f'/api/users/{readonly_user.id}/change-password', 
                            headers=headers, json=password_data)
        assert response.status_code == 403


class TestRegistrationLinkRoutes:
    
    @pytest.mark.api
    def test_get_registration_links_as_admin(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        response = client.get('/api/admin/registration-links', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['registration_links']) >= 1
        assert data['registration_links'][0]['custom_path'] == 'test-link'

    @pytest.mark.api
    def test_get_registration_links_editor_forbidden(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        response = client.get('/api/admin/registration-links', headers=headers)
        assert response.status_code == 403

    @pytest.mark.api
    def test_create_registration_link(self, client, admin_token):
        headers = get_auth_headers(admin_token)
        link_data = {
            'custom_path': 'new-link',
            'max_uses': 10,
            'default_permission': 'editor',
            'auto_enable_new_users': True,
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        response = client.post('/api/admin/registration-links', headers=headers, json=link_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Registration link created successfully' in data['message']
        assert data['registration_link']['custom_path'] == 'new-link'
        assert data['registration_link']['max_uses'] == 10

    @pytest.mark.api
    def test_create_registration_link_duplicate_path(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        link_data = {
            'custom_path': 'test-link',  # Same as sample_registration_link
            'max_uses': 5,
            'default_permission': 'readonly'
        }
        
        response = client.post('/api/admin/registration-links', headers=headers, json=link_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_get_registration_link_by_id(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        response = client.get(f'/api/admin/registration-links/{sample_registration_link.id}', 
                            headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['registration_link']['custom_path'] == 'test-link'

    @pytest.mark.api
    def test_update_registration_link(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        update_data = {
            'max_uses': 20,
            'default_permission': 'editor',
            'is_active': False
        }
        
        response = client.put(f'/api/admin/registration-links/{sample_registration_link.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['registration_link']['max_uses'] == 20
        assert data['registration_link']['default_permission'] == 'editor'
        assert data['registration_link']['is_active'] is False

    @pytest.mark.api
    def test_delete_registration_link(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        response = client.delete(f'/api/admin/registration-links/{sample_registration_link.id}', 
                               headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Registration link deleted successfully' in data['message']

    @pytest.mark.api
    def test_get_registration_link_info_public(self, client, sample_registration_link):
        # This should be accessible without authentication
        response = client.get(f'/api/register/{sample_registration_link.custom_path}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['link_info']['default_permission'] == 'readonly'
        assert data['link_info']['auto_enable_new_users'] is True

    @pytest.mark.api
    def test_get_registration_link_info_not_found(self, client):
        response = client.get('/api/register/nonexistent-link')
        assert response.status_code == 404

    @pytest.mark.api
    def test_register_via_link_success(self, client, sample_registration_link, app):
        user_data = {
            'username': 'linkuser',
            'email': 'linkuser@test.com',
            'password': 'password123',
            'first_name': 'Link',
            'last_name': 'User'
        }
        
        response = client.post(f'/api/register/{sample_registration_link.custom_path}', 
                             json=user_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'User registered successfully' in data['message']
        
        # Verify user was created with link settings
        with app.app_context():
            user = User.query.filter_by(username='linkuser').first()
            assert user is not None
            assert user.permission == sample_registration_link.default_permission
            assert user.enabled == sample_registration_link.auto_enable_new_users
            assert user.registered_via_link_id == sample_registration_link.id

    @pytest.mark.api
    def test_register_via_link_expired(self, client, app, admin_user):
        # Create an expired link
        with app.app_context():
            expired_link = RegistrationLink(
                custom_path='expired-link',
                max_uses=5,
                created_by_user_id=admin_user.id,
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
            )
            db.session.add(expired_link)
            db.session.commit()
        
        user_data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'password123'
        }
        
        response = client.post('/api/register/expired-link', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'expired' in data['message'].lower()

    @pytest.mark.api
    def test_register_via_link_max_uses_reached(self, client, app, admin_user):
        # Create a link that has reached max uses
        with app.app_context():
            full_link = RegistrationLink(
                custom_path='full-link',
                max_uses=1,
                current_uses=1,  # Already at max
                created_by_user_id=admin_user.id
            )
            db.session.add(full_link)
            db.session.commit()
        
        user_data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'password': 'password123'
        }
        
        response = client.post('/api/register/full-link', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'maximum' in data['message'].lower()

    @pytest.mark.api
    def test_create_user_via_link_admin(self, client, admin_token, sample_registration_link):
        headers = get_auth_headers(admin_token)
        user_data = {
            'username': 'adminlinkuser',
            'email': 'adminlink@test.com',
            'password': 'password123',
            'first_name': 'Admin',
            'last_name': 'Link',
            'registration_link_id': sample_registration_link.id
        }
        
        response = client.post('/api/admin/create_user_via_link', headers=headers, json=user_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'User created successfully' in data['message']

    @pytest.mark.api
    def test_user_routes_require_authentication(self, client):
        """Test that user management routes require authentication"""
        endpoints = [
            ('GET', '/api/users'),
            ('POST', '/api/admin/users'),
            ('GET', '/api/users/1'),
            ('PUT', '/api/users/1'),
            ('DELETE', '/api/users/1'),
            ('POST', '/api/users/1/approve'),
            ('PUT', '/api/users/1/change-password'),
            ('GET', '/api/admin/registration-links'),
            ('POST', '/api/admin/registration-links'),
            ('GET', '/api/admin/registration-links/1'),
            ('PUT', '/api/admin/registration-links/1'),
            ('DELETE', '/api/admin/registration-links/1'),
            ('POST', '/api/admin/create_user_via_link')
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
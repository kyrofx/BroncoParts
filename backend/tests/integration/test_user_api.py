"""Integration tests for user management API endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


class TestUserManagementAPI:
    """Test cases for user management API endpoints."""
    
    def test_get_users_as_admin(self, client, db_session, mock_airtable):
        """Test getting all users as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/users', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 3
        usernames = [user['username'] for user in data]
        assert 'admin' in usernames
        assert 'editor' in usernames
        assert 'readonly' in usernames
    
    def test_get_users_as_non_admin(self, client, db_session, mock_airtable):
        """Test getting users as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.get('/api/users', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_get_current_user(self, client, db_session, mock_airtable):
        """Test getting current user information."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/current-user', headers=headers)
        
        data = assert_success_response(response)
        assert data['username'] == 'admin'
        assert data['permission'] == 'admin'
        assert data['enabled'] is True
        assert data['is_approved'] is True
    
    def test_create_user_as_admin(self, client, db_session, mock_airtable):
        """Test creating a user as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/users', headers=headers, json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User',
            'permission': 'editor',
            'enabled': True
        })
        
        data = assert_success_response(response, 201)
        assert data['username'] == 'newuser'
        assert data['permission'] == 'editor'
        assert data['enabled'] is True
    
    def test_create_user_as_non_admin(self, client, db_session, mock_airtable):
        """Test creating a user as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/users', headers=headers, json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'permission': 'readonly'
        })
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_create_user_duplicate_username(self, client, db_session, mock_airtable):
        """Test creating a user with duplicate username."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/users', headers=headers, json={
            'username': 'admin',  # Already exists
            'email': 'another@test.com',
            'password': 'password123',
            'permission': 'readonly'
        })
        
        assert_error_response(response, 400, 'Username already exists')
    
    def test_update_user_as_admin(self, client, db_session, mock_airtable):
        """Test updating a user as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/users/{editor.id}', headers=headers, json={
            'permission': 'admin',
            'enabled': False
        })
        
        data = assert_success_response(response)
        assert data['permission'] == 'admin'
        assert data['enabled'] is False
    
    def test_update_user_as_non_admin(self, client, db_session, mock_airtable):
        """Test updating a user as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.put(f'/api/users/{readonly.id}', headers=headers, json={
            'permission': 'admin'
        })
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_update_nonexistent_user(self, client, db_session, mock_airtable):
        """Test updating a nonexistent user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put('/api/users/999', headers=headers, json={
            'permission': 'admin'
        })
        
        assert_error_response(response, 404, 'User not found')
    
    def test_delete_user_as_admin(self, client, db_session, mock_airtable):
        """Test deleting a user as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/users/{editor.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_delete_user_as_non_admin(self, client, db_session, mock_airtable):
        """Test deleting a user as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.delete(f'/api/users/{readonly.id}', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_approve_user(self, client, db_session, mock_airtable):
        """Test approving a user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        unapproved = TestFixtures.create_test_unapproved_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post(f'/api/users/{unapproved.id}/approve', headers=headers)
        
        data = assert_success_response(response)
        assert data['is_approved'] is True
    
    def test_approve_user_as_non_admin(self, client, db_session, mock_airtable):
        """Test approving a user as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        unapproved = TestFixtures.create_test_unapproved_user(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post(f'/api/users/{unapproved.id}/approve', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_change_password(self, client, db_session, mock_airtable):
        """Test changing user password."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/change-password', headers=headers, json={
            'current_password': 'password123',
            'new_password': 'newpassword123'
        })
        
        data = assert_success_response(response)
        assert 'Password changed successfully' in data['message']
        
        # Test login with new password
        login_response = client.post('/api/login', json={
            'username': 'admin',
            'password': 'newpassword123'
        })
        assert_success_response(login_response)
    
    def test_change_password_wrong_current(self, client, db_session, mock_airtable):
        """Test changing password with wrong current password."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/change-password', headers=headers, json={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        })
        
        assert_error_response(response, 400, 'Current password is incorrect')
    
    def test_get_pending_users(self, client, db_session, mock_airtable):
        """Test getting pending (unapproved) users."""
        admin = TestFixtures.create_test_admin_user(db_session)
        unapproved = TestFixtures.create_test_unapproved_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/users/pending', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) == 1
        assert data[0]['username'] == 'unapproved'
        assert data[0]['is_approved'] is False
    
    def test_bulk_user_actions(self, client, db_session, mock_airtable):
        """Test bulk user operations."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        # Test bulk enable/disable
        response = client.post('/api/users/bulk-update', headers=headers, json={
            'user_ids': [editor.id, readonly.id],
            'enabled': False
        })
        
        data = assert_success_response(response)
        assert 'users updated successfully' in data['message']

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
    


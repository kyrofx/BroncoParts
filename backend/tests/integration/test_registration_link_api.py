"""Integration tests for registration link management API endpoints."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


class TestRegistrationLinkAPI:
    """Test cases for registration link management API endpoints."""
    
    def test_get_registration_links_as_admin(self, client, db_session, mock_airtable):
        """Test getting registration links as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/admin/registration-links', headers=headers)
        
        data = assert_success_response(response)
        assert len(data['links']) >= 1
        assert any(link['custom_path'] == 'test-link' for link in data['links'])
    
    def test_get_registration_links_as_non_admin(self, client, db_session, mock_airtable):
        """Test getting registration links as non-admin (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.get('/api/admin/registration-links', headers=headers)
        
        assert_error_response(response, 403, 'Admin access required')
    
    def test_create_registration_link_as_admin(self, client, db_session, mock_airtable):
        """Test creating a registration link as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/admin/registration-links', headers=headers, json={
            'custom_path': 'new-signup-link',
            'max_uses': 5,
            'default_permission': 'editor',
            'auto_enable_new_users': True,
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
        })
        
        data = assert_success_response(response, 201)
        link_data = data['link']
        assert link_data['custom_path'] == 'new-signup-link'
        assert link_data['max_uses'] == 5
        assert link_data['default_permission'] == 'editor'
        assert link_data['auto_enable_new_users'] is True
        assert link_data['current_uses'] == 0
        assert link_data['is_active'] is True
        assert 'token' in link_data
        assert 'link_identifier' in link_data
    
    def test_create_registration_link_duplicate_path(self, client, db_session, mock_airtable):
        """Test creating a registration link with duplicate custom path."""
        admin = TestFixtures.create_test_admin_user(db_session)
        existing_link = TestFixtures.create_test_registration_link(db_session, admin, custom_path='duplicate')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/admin/registration-links', headers=headers, json={
            'custom_path': 'duplicate',
            'max_uses': 1,
            'default_permission': 'readonly'
        })
        
        assert_error_response(response, 400, 'Custom path')
    
    def test_create_registration_link_unlimited_uses(self, client, db_session, mock_airtable):
        """Test creating a registration link with unlimited uses."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/admin/registration-links', headers=headers, json={
            'custom_path': 'unlimited-link',
            'max_uses': -1,  # Unlimited
            'default_permission': 'readonly',
            'auto_enable_new_users': False
        })
        
        data = assert_success_response(response, 201)
        link_data = data['link']
        assert link_data['max_uses'] == -1
        assert link_data['auto_enable_new_users'] is False
    
    def test_create_single_use_link_with_fixed_user(self, client, db_session, mock_airtable):
        """Test creating a single-use link with fixed user details."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/admin/registration-links', headers=headers, json={
            'custom_path': 'single-user-link',
            'max_uses': 1,
            'default_permission': 'editor',
            'auto_enable_new_users': True,
            'fixed_username': 'predefined_user',
            'fixed_email': 'predefined@test.com'
        })
        
        data = assert_success_response(response, 201)
        link_data = data['link']
        assert link_data['max_uses'] == 1
        assert link_data['fixed_username'] == 'predefined_user'
        assert link_data['fixed_email'] == 'predefined@test.com'
    
    def test_get_registration_link_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific registration link by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/admin/registration-links/{reg_link.id}', headers=headers)
        
        data = assert_success_response(response)
        link_data = data['link']
        assert link_data['id'] == reg_link.id
        assert link_data['custom_path'] == 'test-link'
        assert link_data['creator_username'] == 'admin'
        assert 'is_currently_valid' in link_data
    
    def test_update_registration_link(self, client, db_session, mock_airtable):
        """Test updating a registration link."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/admin/registration-links/{reg_link.id}', headers=headers, json={
            'max_uses': 10,
            'default_permission': 'admin',
            'is_active': False
        })
        
        data = assert_success_response(response)
        link_data = data['link']
        assert link_data['max_uses'] == 10
        assert link_data['default_permission'] == 'admin'
        assert link_data['is_active'] is False
    
    def test_delete_registration_link(self, client, db_session, mock_airtable):
        """Test deleting a registration link."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/admin/registration-links/{reg_link.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_registration_link_validation_status(self, client, db_session, mock_airtable):
        """Test registration link validation status endpoint."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        # Test valid link
        response = client.get(f'/api/register/{reg_link.effective_link_path_segment}')
        
        data = assert_success_response(response)
        assert data['is_currently_valid'] is True
        assert 'message' in data
        
        # Test with expired link
        reg_link.expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        
        response = client.get(f'/api/register/{reg_link.effective_link_path_segment}')
        
        data = assert_success_response(response)
        assert data['is_currently_valid'] is False
        assert 'expired' in data['message'].lower()
    
    def test_registration_link_usage_tracking(self, client, db_session, mock_airtable):
        """Test registration link usage tracking."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        # Register a user with the link
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'newuser',
            'password': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_success_response(response, 201)
        
        # Check that usage count increased
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/admin/registration-links/{reg_link.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['link']['current_uses'] == 1
    
    def test_registration_link_max_uses_enforcement(self, client, db_session, mock_airtable):
        """Test that registration links enforce max uses limit."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        reg_link.max_uses = 1
        reg_link.current_uses = 1  # Already used up
        db_session.commit()
        
        # Try to register another user
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'anotheruser',
            'password': 'password123',
            'email': 'another@test.com',
            'first_name': 'Another',
            'last_name': 'User'
        })
        
        assert_error_response(response, 403, 'Link has reached its maximum number of uses.')
    
    def test_registration_link_inactive_enforcement(self, client, db_session, mock_airtable):
        """Test that inactive registration links cannot be used."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        reg_link.is_active = False
        db_session.commit()
        
        # Try to register with inactive link
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'newuser',
            'password': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_error_response(response, 403, 'Link is not active.')
    
    def test_registration_with_fixed_user_details(self, client, db_session, mock_airtable):
        """Test registration with fixed user details from link."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        reg_link.fixed_username = 'fixed_user'
        reg_link.fixed_email = 'fixed@test.com'
        db_session.commit()
        
        # Register with the fixed details
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'password': 'password123',
            'first_name': 'Fixed',
            'last_name': 'User'
        })
        
        data = assert_success_response(response, 201)
        assert data['user']['username'] == 'fixed_user'
        assert data['user']['email'] == 'fixed@test.com'

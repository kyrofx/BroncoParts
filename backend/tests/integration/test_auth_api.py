"""Integration tests for authentication endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationAPI:
    """Test cases for authentication-related API endpoints."""
    
    def test_login_success(self, client, db_session, mock_airtable):
        """Test successful user login."""
        user = TestFixtures.create_test_admin_user(db_session)
        
        response = client.post('/api/login', json={
            'email': 'admin@test.com',
            'password': 'password123'
        })
        
        data = assert_success_response(response)
        assert 'access_token' in data
        assert data['user']['username'] == 'admin'
        assert data['user']['permission'] == 'admin'
        assert data['user']['enabled'] is True
        assert data['user']['is_approved'] is True
    
    def test_login_invalid_credentials(self, client, db_session, mock_airtable):
        """Test login with invalid credentials."""
        user = TestFixtures.create_test_admin_user(db_session)
        
        response = client.post('/api/login', json={
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        })
        
        assert_error_response(response, 401, 'Invalid credentials')
    
    def test_login_nonexistent_user(self, client, db_session, mock_airtable):
        """Test login with nonexistent user."""
        response = client.post('/api/login', json={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        })
        
        assert_error_response(response, 401, 'Invalid credentials')
    
    def test_login_disabled_user(self, client, db_session, mock_airtable):
        """Test login with disabled user."""
        user = TestFixtures.create_test_disabled_user(db_session)
        
        response = client.post('/api/login', json={
            'email': 'disabled@test.com',
            'password': 'password123'
        })
        
        assert_error_response(response, 403, 'Account disabled')
    
    def test_login_unapproved_user(self, client, db_session, mock_airtable):
        """Test login with unapproved user."""
        user = TestFixtures.create_test_unapproved_user(db_session)
        
        response = client.post('/api/login', json={
            'email': 'unapproved@test.com',
            'password': 'password123'
        })
        
        assert_error_response(response, 403, 'Account not approved')
    
    def test_login_missing_fields(self, client, db_session, mock_airtable):
        """Test login with missing required fields."""
        # Missing password
        response = client.post('/api/login', json={
            'email': 'admin@test.com'
        })
        assert_error_response(response, 400)
        
        # Missing email
        response = client.post('/api/login', json={
            'password': 'password123'
        })
        assert_error_response(response, 400)
    
    def test_register_invalid_link(self, client, db_session, mock_airtable):
        """Test registration with invalid link."""
        response = client.post('/api/register/invalid-link', json={
            'username': 'newuser',
            'password': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_error_response(response, 404, 'Registration link not found')
    
    def test_register_expired_link(self, client, db_session, mock_airtable):
        """Test registration with expired link."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        # Set link as used up
        reg_link.current_uses = reg_link.max_uses
        db_session.commit()
        
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'newuser',
            'password': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_error_response(response, 400, 'Link has reached its maximum number of uses')
    
    def test_register_duplicate_username(self, client, db_session, mock_airtable):
        """Test registration with duplicate username."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'admin',  # Already exists
            'password': 'password123',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_error_response(response, 400, 'Username already exists')
    
    def test_register_duplicate_email(self, client, db_session, mock_airtable):
        """Test registration with duplicate email."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        response = client.post(f'/api/register/{reg_link.effective_link_path_segment}', json={
            'username': 'newuser',
            'password': 'password123',
            'email': 'admin@test.com',  # Already exists
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert_error_response(response, 400, 'Email already exists')
    

    
    def test_protected_endpoint_without_auth(self, client, db_session, mock_airtable):
        """Test accessing protected endpoint without authentication."""
        response = client.get('/api/users')
        assert_error_response(response, 401)
    
    def test_protected_endpoint_with_auth(self, client, db_session, mock_airtable):
        """Test accessing protected endpoint with authentication."""
        admin = TestFixtures.create_test_admin_user(db_session)
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        
        response = client.get('/api/users', headers=headers)
        assert_success_response(response)
    
    def test_token_expiration_handling(self, client, db_session, mock_airtable):
        """Test handling of expired tokens."""
        # This would require manipulating JWT expiration
        # For now, we test with an invalid token format
        response = client.get('/api/users', headers={
            'Authorization': 'Bearer invalid.token.format'
        })
        assert_error_response(response, 401)

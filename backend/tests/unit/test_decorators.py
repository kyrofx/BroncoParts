"""Unit tests for authentication decorators."""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from app.decorators import admin_required, editor_or_admin_required, readonly_or_higher_required


@pytest.mark.unit
class TestDecorators:
    """Test cases for authentication decorators."""
    
    @pytest.fixture
    def decorator_app(self):
        """Create a minimal Flask app for decorator testing."""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        jwt = JWTManager(app)
        
        @app.route('/admin-only')
        @admin_required
        def admin_only():
            return jsonify(message="Admin access granted")
        
        @app.route('/editor-or-admin')
        @editor_or_admin_required
        def editor_or_admin():
            return jsonify(message="Editor or admin access granted")
        
        @app.route('/readonly-or-higher')
        @readonly_or_higher_required
        def readonly_or_higher():
            return jsonify(message="Readonly or higher access granted")
        
        return app
    
    def create_test_token(self, app, user_data):
        """Helper to create JWT tokens with user data."""
        with app.app_context():
            return create_access_token(
                identity=user_data['username'],
                additional_claims=user_data
            )
    
    def test_admin_required_with_admin_user(self, decorator_app):
        """Test admin_required decorator with admin user."""
        admin_data = {
            'username': 'admin',
            'permission': 'admin',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, admin_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Admin access granted"
    
    def test_admin_required_with_non_admin_user(self, decorator_app):
        """Test admin_required decorator with non-admin user."""
        editor_data = {
            'username': 'editor',
            'permission': 'editor',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, editor_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 403
            data = response.get_json()
            assert "Admin access required" in data['message']
    
    def test_admin_required_with_disabled_admin(self, decorator_app):
        """Test admin_required decorator with disabled admin user."""
        disabled_admin_data = {
            'username': 'disabled_admin',
            'permission': 'admin',
            'enabled': False
        }
        
        token = self.create_test_token(decorator_app, disabled_admin_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 403
            data = response.get_json()
            assert "Account disabled" in data['message']
    
    def test_admin_required_without_token(self, decorator_app):
        """Test admin_required decorator without authentication token."""
        with decorator_app.test_client() as client:
            response = client.get('/admin-only')
            
            assert response.status_code == 401
    
    def test_admin_required_with_invalid_token(self, decorator_app):
        """Test admin_required decorator with invalid token."""
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': 'Bearer invalid-token'
            })
            
            assert response.status_code == 401
    
    def test_editor_or_admin_required_with_editor(self, decorator_app):
        """Test editor_or_admin_required decorator with editor user."""
        editor_data = {
            'username': 'editor',
            'permission': 'editor',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, editor_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/editor-or-admin', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Editor or admin access granted"
    
    def test_editor_or_admin_required_with_admin(self, decorator_app):
        """Test editor_or_admin_required decorator with admin user."""
        admin_data = {
            'username': 'admin',
            'permission': 'admin',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, admin_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/editor-or-admin', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Editor or admin access granted"
    
    def test_editor_or_admin_required_with_readonly(self, decorator_app):
        """Test editor_or_admin_required decorator with readonly user."""
        readonly_data = {
            'username': 'readonly',
            'permission': 'readonly',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, readonly_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/editor-or-admin', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 403
            data = response.get_json()
            assert "Editor or Admin access required" in data['message']
    
    def test_readonly_or_higher_required_with_readonly(self, decorator_app):
        """Test readonly_or_higher_required decorator with readonly user."""
        readonly_data = {
            'username': 'readonly',
            'permission': 'readonly',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, readonly_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/readonly-or-higher', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Readonly or higher access granted"
    
    def test_readonly_or_higher_required_with_editor(self, decorator_app):
        """Test readonly_or_higher_required decorator with editor user."""
        editor_data = {
            'username': 'editor',
            'permission': 'editor',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, editor_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/readonly-or-higher', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Readonly or higher access granted"
    
    def test_readonly_or_higher_required_with_admin(self, decorator_app):
        """Test readonly_or_higher_required decorator with admin user."""
        admin_data = {
            'username': 'admin',
            'permission': 'admin',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, admin_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/readonly-or-higher', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == "Readonly or higher access granted"
    
    def test_readonly_or_higher_required_with_invalid_permission(self, decorator_app):
        """Test readonly_or_higher_required decorator with invalid permission."""
        invalid_data = {
            'username': 'invalid',
            'permission': 'invalid_permission',
            'enabled': True
        }
        
        token = self.create_test_token(decorator_app, invalid_data)
        
        with decorator_app.test_client() as client:
            response = client.get('/readonly-or-higher', headers={
                'Authorization': f'Bearer {token}'
            })
            
            assert response.status_code == 403
            data = response.get_json()
            assert "Access denied" in data['message']
    
    @patch('app.decorators.verify_jwt_in_request')
    @patch('app.decorators.get_jwt')
    def test_decorator_exception_handling(self, mock_get_jwt, mock_verify_jwt, decorator_app):
        """Test decorator exception handling."""
        # Simulate JWT verification failure
        mock_verify_jwt.side_effect = Exception("JWT verification failed")
        
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': 'Bearer some-token'
            })
            
            assert response.status_code == 401
            data = response.get_json()
            assert "Authentication Error" in data['message']
    
    @patch('app.decorators.verify_jwt_in_request')
    @patch('app.decorators.get_jwt')
    def test_decorator_missing_jwt_payload(self, mock_get_jwt, mock_verify_jwt, decorator_app):
        """Test decorator behavior when JWT payload is missing."""
        mock_verify_jwt.return_value = None
        mock_get_jwt.return_value = None
        
        with decorator_app.test_client() as client:
            response = client.get('/admin-only', headers={
                'Authorization': 'Bearer some-token'
            })
            
            assert response.status_code == 401
            data = response.get_json()
            assert "Invalid token or token missing" in data['message']

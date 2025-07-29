import pytest
import json
from app.models import User, Project, Part, db
from tests.conftest import get_auth_headers


class TestStatsRoutes:
    
    @pytest.mark.api
    def test_get_active_users_stats(self, client, readonly_token, admin_user, editor_user, readonly_user, disabled_user):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/stats/active-users', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'active_users' in data
        
        # Should count enabled and approved users (admin, editor, readonly)
        # disabled_user is not enabled, so shouldn't be counted
        assert data['active_users'] >= 3

    @pytest.mark.api
    def test_get_projects_stats(self, client, readonly_token, sample_project):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/stats/projects', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'projects' in data
        assert data['projects'] >= 1  # At least the sample project

    @pytest.mark.api
    def test_get_parts_stats(self, client, readonly_token, sample_part):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/stats/parts', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'parts' in data
        assert data['parts'] >= 1  # At least the sample part and assembly

    @pytest.mark.api
    def test_stats_with_multiple_projects_and_parts(self, client, readonly_token, app):
        """Test stats with multiple projects and parts"""
        with app.app_context():
            # Create additional projects
            project1 = Project(name='Project 1', prefix='P1')
            project2 = Project(name='Project 2', prefix='P2')
            db.session.add_all([project1, project2])
            db.session.commit()
            
            # Create parts for these projects
            parts = [
                Part(name='Part 1', part_number='P1-P-0001', numeric_id=1, 
                     type='part', project_id=project1.id, quantity=1),
                Part(name='Part 2', part_number='P1-P-0002', numeric_id=2, 
                     type='part', project_id=project1.id, quantity=1),
                Part(name='Assembly 1', part_number='P2-A-0001', numeric_id=1, 
                     type='assembly', project_id=project2.id, quantity=1),
                Part(name='Part 3', part_number='P2-P-0002', numeric_id=2, 
                     type='part', project_id=project2.id, quantity=1)
            ]
            db.session.add_all(parts)
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        
        # Test project stats
        response = client.get('/api/stats/projects', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['projects'] >= 2
        
        # Test parts stats
        response = client.get('/api/stats/parts', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['parts'] >= 4

    @pytest.mark.api
    def test_stats_with_multiple_users(self, client, readonly_token, app):
        """Test user stats with various user states"""
        with app.app_context():
            # Create users with different states
            users = [
                User(username='active1', email='active1@test.com', 
                     permission='readonly', enabled=True, is_approved=True),
                User(username='active2', email='active2@test.com', 
                     permission='editor', enabled=True, is_approved=True),
                User(username='disabled1', email='disabled1@test.com', 
                     permission='readonly', enabled=False, is_approved=True),
                User(username='unapproved1', email='unapproved1@test.com', 
                     permission='readonly', enabled=True, is_approved=False),
                User(username='both_disabled', email='both@test.com', 
                     permission='readonly', enabled=False, is_approved=False)
            ]
            
            for user in users:
                user.set_password('password123')
            
            db.session.add_all(users)
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/stats/active-users', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should only count users that are both enabled AND approved
        # From fixtures: admin, editor, readonly (3)
        # From this test: active1, active2 (2)
        # Total: 5 active users
        assert data['active_users'] >= 5

    @pytest.mark.api
    def test_stats_empty_database(self, client, readonly_token, app):
        """Test stats with minimal data"""
        # This test uses a fresh database with only the readonly user
        headers = get_auth_headers(readonly_token)
        
        # Projects stats (should be 0 or very low)
        response = client.get('/api/stats/projects', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['projects'] >= 0
        
        # Parts stats (should be 0 or very low)  
        response = client.get('/api/stats/parts', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['parts'] >= 0
        
        # Users stats (should have at least the test users from fixtures)
        response = client.get('/api/stats/active-users', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['active_users'] >= 1  # At least the readonly user

    @pytest.mark.api
    def test_stats_data_types(self, client, readonly_token):
        """Test that stats return proper data types"""
        headers = get_auth_headers(readonly_token)
        
        endpoints = [
            '/api/stats/active-users',
            '/api/stats/projects', 
            '/api/stats/parts'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Should have exactly one key
            assert len(data) == 1
            
            # The value should be an integer
            key = list(data.keys())[0]
            assert isinstance(data[key], int)
            assert data[key] >= 0

    @pytest.mark.api
    def test_stats_require_authentication(self, client):
        """Test that all stats routes require authentication"""
        endpoints = [
            '/api/stats/active-users',
            '/api/stats/projects',
            '/api/stats/parts'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    @pytest.mark.api
    def test_stats_readonly_access(self, client, readonly_token):
        """Test that readonly users can access stats"""
        headers = get_auth_headers(readonly_token)
        
        endpoints = [
            '/api/stats/active-users',
            '/api/stats/projects',
            '/api/stats/parts'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200

    @pytest.mark.api
    def test_stats_editor_access(self, client, editor_token):
        """Test that editor users can access stats"""
        headers = get_auth_headers(editor_token)
        
        endpoints = [
            '/api/stats/active-users',
            '/api/stats/projects',
            '/api/stats/parts'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200

    @pytest.mark.api
    def test_stats_admin_access(self, client, admin_token):
        """Test that admin users can access stats"""
        headers = get_auth_headers(admin_token)
        
        endpoints = [
            '/api/stats/active-users',
            '/api/stats/projects',
            '/api/stats/parts'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200

    @pytest.mark.api
    def test_stats_consistency(self, client, readonly_token, app, sample_project):
        """Test that stats are consistent across multiple calls"""
        headers = get_auth_headers(readonly_token)
        
        # Get initial stats
        response1 = client.get('/api/stats/projects', headers=headers)
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        
        # Get stats again
        response2 = client.get('/api/stats/projects', headers=headers)
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        
        # Should be the same
        assert data1['projects'] == data2['projects']
        
        # Add a new project
        with app.app_context():
            new_project = Project(name='New Project', prefix='NP')
            db.session.add(new_project)
            db.session.commit()
        
        # Stats should reflect the change
        response3 = client.get('/api/stats/projects', headers=headers)
        assert response3.status_code == 200
        data3 = json.loads(response3.data)
        
        assert data3['projects'] == data1['projects'] + 1

    @pytest.mark.api
    def test_stats_performance(self, client, readonly_token, app):
        """Test that stats endpoints perform reasonably with more data"""
        # Create a moderate amount of test data
        with app.app_context():
            projects = []
            for i in range(10):
                project = Project(name=f'Project {i}', prefix=f'P{i:02d}')
                projects.append(project)
            db.session.add_all(projects)
            db.session.commit()
            
            parts = []
            for i, project in enumerate(projects):
                for j in range(5):  # 5 parts per project
                    part = Part(
                        name=f'Part {i}-{j}',
                        part_number=f'P{i:02d}-P-{j:04d}',
                        numeric_id=j+1,
                        type='part',
                        project_id=project.id,
                        quantity=1
                    )
                    parts.append(part)
            db.session.add_all(parts)
            db.session.commit()
        
        headers = get_auth_headers(readonly_token)
        
        # All stats endpoints should still respond quickly
        import time
        
        for endpoint in ['/api/stats/projects', '/api/stats/parts', '/api/stats/active-users']:
            start_time = time.time()
            response = client.get(endpoint, headers=headers)
            end_time = time.time()
            
            assert response.status_code == 200
            # Should respond within a reasonable time (adjust as needed)
            assert (end_time - start_time) < 5.0  # 5 seconds max
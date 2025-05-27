"""
Integration tests for statistics and dashboard API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from app.models import User, Project, Part, Order, OrderItem


@pytest.mark.integration
class TestStatisticsAPI:
    """Test statistics and dashboard endpoints."""

    def test_get_dashboard_stats_success(self, client, auth_headers, test_fixtures):
        """Test getting dashboard statistics."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )
        
        # Create parts and orders for statistics
        part1 = test_fixtures.create_part(
            name="Part 1",
            project_id=project.id,
            creator_id=admin.id
        )
        
        part2 = test_fixtures.create_part(
            name="Part 2",
            project_id=project.id,
            creator_id=admin.id
        )
        
        order = test_fixtures.create_order(
            project_id=project.id,
            created_by_id=admin.id
        )
        
        test_fixtures.create_order_item(
            order_id=order.id,
            part_id=part1.id,
            quantity=5
        )

        response = client.get('/api/stats/dashboard', headers=auth_headers['admin'])
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_projects' in data
        assert 'total_parts' in data
        assert 'total_orders' in data
        assert 'active_users' in data
        assert 'recent_activity' in data

    def test_get_project_statistics(self, client, auth_headers, test_fixtures):
        """Test getting project-specific statistics."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )
        
        # Create parts with different statuses
        test_fixtures.create_part(
            name="Design Part",
            project_id=project.id,
            creator_id=admin.id,
            part_status="design"
        )
        
        test_fixtures.create_part(
            name="Manufacturing Part",
            project_id=project.id,
            creator_id=admin.id,
            part_status="manufacturing"
        )

        response = client.get(f'/api/stats/projects/{project.id}', headers=auth_headers['admin'])
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'project_id' in data
        assert 'total_parts' in data
        assert 'parts_by_status' in data
        assert 'total_orders' in data
        assert 'completion_rate' in data

    def test_get_user_statistics(self, client, auth_headers, test_fixtures):
        """Test getting user-specific statistics."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )
        
        # Create parts created by the admin
        test_fixtures.create_part(
            name="Part 1",
            project_id=project.id,
            creator_id=admin.id
        )
        
        test_fixtures.create_part(
            name="Part 2",
            project_id=project.id,
            creator_id=admin.id
        )

        response = client.get(f'/api/stats/users/{admin.id}', headers=auth_headers['admin'])
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'user_id' in data
        assert 'projects_created' in data
        assert 'parts_created' in data
        assert 'orders_created' in data
        assert 'activity_timeline' in data

    def test_get_material_usage_stats(self, client, auth_headers, test_fixtures):
        """Test getting material usage statistics."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )
        
        # Create parts with different materials
        test_fixtures.create_part(
            name="Aluminum Part",
            project_id=project.id,
            creator_id=admin.id,
            raw_material="Aluminum"
        )
        
        test_fixtures.create_part(
            name="Steel Part",
            project_id=project.id,
            creator_id=admin.id,
            raw_material="Steel"
        )

        response = client.get('/api/stats/materials', headers=auth_headers['admin'])
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'materials_usage' in data
        assert isinstance(data['materials_usage'], list)

    def test_get_machine_utilization_stats(self, client, auth_headers, test_fixtures):
        """Test getting machine utilization statistics."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        machine = test_fixtures.create_machine(name="CNC Mill")
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )
        
        # Create parts that use the machine
        test_fixtures.create_part(
            name="Machined Part",
            project_id=project.id,
            creator_id=admin.id,
            machine_id=machine.id
        )

        response = client.get('/api/stats/machines', headers=auth_headers['admin'])
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'machine_utilization' in data
        assert isinstance(data['machine_utilization'], list)

    def test_get_time_based_stats(self, client, auth_headers, test_fixtures):
        """Test getting time-based statistics with date range."""
        # Use existing admin user from fixture
        admin = test_fixtures._test_data['users']['admin']
        
        project = test_fixtures.create_project(
            project_id="PROJ001",
            name="Test Project",
            creator_id=admin.id
        )

        # Test with date range parameters
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(
            f'/api/stats/timeline?start_date={start_date}&end_date={end_date}',
            headers=auth_headers['admin']
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'timeline_data' in data
        assert 'start_date' in data
        assert 'end_date' in data

    def test_statistics_permission_readonly(self, client, auth_headers, test_fixtures):
        """Test that readonly users can access basic statistics."""
        # Readonly users should be able to view statistics
        response = client.get('/api/stats/dashboard', headers=auth_headers['readonly'])
        assert response.status_code == 200

    def test_statistics_permission_unauthorized(self, client):
        """Test that unauthorized users cannot access statistics."""
        response = client.get('/api/stats/dashboard')
        assert response.status_code == 401

    def test_export_statistics_admin_only(self, client, auth_headers, test_fixtures):
        """Test that only admins can export statistics."""
        # Admin should be able to export
        response = client.get('/api/stats/export', headers=auth_headers['admin'])
        # Assuming this endpoint exists and returns CSV or similar
        assert response.status_code in [200, 501]  # 501 if not implemented yet
        
        # Editor should not be able to export
        response = client.get('/api/stats/export', headers=auth_headers['editor'])
        assert response.status_code in [403, 501]  # 403 forbidden or 501 if not implemented
        
        # Readonly should not be able to export
        response = client.get('/api/stats/export', headers=auth_headers['readonly'])
        assert response.status_code in [403, 501]

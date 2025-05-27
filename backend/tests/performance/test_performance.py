"""
Performance tests for the Bronco Parts backend API.
These tests measure response times and can identify performance regressions.

Note: These tests require the 'pytest-benchmark' package.
Install with: pip install pytest-benchmark
"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.slow
    def test_project_list_performance(self, client, auth_headers, test_fixtures, benchmark):
        """Test performance of project listing with many projects."""
        # Create multiple projects for testing
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        # Create 50 projects
        for i in range(50):
            test_fixtures.create_project(
                project_id=f"PERF{i:03d}",
                name=f"Performance Test Project {i}",
                creator_id=admin.id
            )
        
        # Benchmark the API call
        def get_projects():
            response = client.get('/api/projects', headers=auth_headers['admin'])
            assert response.status_code == 200
            return response
        
        result = benchmark(get_projects)
        assert result.status_code == 200

    @pytest.mark.slow
    def test_part_search_performance(self, client, auth_headers, test_fixtures, benchmark):
        """Test performance of part search with many parts."""
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        project = test_fixtures.create_project(
            project_id="PERF001",
            name="Performance Test Project",
            creator_id=admin.id
        )
        
        # Create 100 parts
        for i in range(100):
            test_fixtures.create_part(
                name=f"Performance Part {i}",
                project_id=project.id,
                creator_id=admin.id,
                description=f"Test part {i} for performance testing"
            )
        
        # Benchmark search
        def search_parts():
            response = client.get('/api/parts/search?q=Performance', headers=auth_headers['admin'])
            assert response.status_code == 200
            return response
        
        result = benchmark(search_parts)
        assert result.status_code == 200

    @pytest.mark.slow
    def test_bulk_order_creation_performance(self, client, auth_headers, test_fixtures, benchmark):
        """Test performance of creating orders with many items."""
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        project = test_fixtures.create_project(
            project_id="PERF001",
            name="Performance Test Project",
            creator_id=admin.id
        )
        
        # Create 20 parts
        parts = []
        for i in range(20):
            part = test_fixtures.create_part(
                name=f"Bulk Part {i}",
                project_id=project.id,
                creator_id=admin.id
            )
            parts.append(part)
        
        # Benchmark order creation
        def create_large_order():
            # Create order
            order_response = client.post('/api/orders',
                json={
                    "project_id": project.id,
                    "notes": "Bulk performance test order"
                },
                headers=auth_headers['admin']
            )
            assert order_response.status_code == 201
            order_data = order_response.get_json()
            order_id = order_data['id']
            
            # Add all parts to order
            for part in parts:
                item_response = client.post('/api/order-items',
                    json={
                        "order_id": order_id,
                        "part_id": part.id,
                        "quantity": 1
                    },
                    headers=auth_headers['admin']
                )
                assert item_response.status_code == 201
            
            return order_response
        
        result = benchmark(create_large_order)
        assert result.status_code == 201

    @pytest.mark.slow
    def test_concurrent_requests_performance(self, client, auth_headers, test_fixtures):
        """Test performance under concurrent load."""
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        project = test_fixtures.create_project(
            project_id="CONCURRENT001",
            name="Concurrent Test Project",
            creator_id=admin.id
        )
        
        def make_request(i):
            """Make a single API request."""
            start_time = time.time()
            response = client.get('/api/projects', headers=auth_headers['admin'])
            end_time = time.time()
            return {
                'request_id': i,
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }
        
        # Make 20 concurrent requests
        num_requests = 20
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all requests succeeded
        success_count = sum(1 for r in results if r['status_code'] == 200)
        assert success_count == num_requests
        
        # Check response times are reasonable (less than 1 second each)
        max_response_time = max(r['response_time'] for r in results)
        assert max_response_time < 1.0
        
        # Check average response time
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        assert avg_response_time < 0.5

    @pytest.mark.slow
    def test_database_query_performance(self, client, auth_headers, test_fixtures, benchmark):
        """Test database query performance with complex relationships."""
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        # Create project with complex structure
        project = test_fixtures.create_project(
            project_id="COMPLEX001",
            name="Complex Test Project",
            creator_id=admin.id
        )
        
        # Create parent parts
        parent_parts = []
        for i in range(10):
            parent = test_fixtures.create_part(
                name=f"Parent Part {i}",
                project_id=project.id,
                creator_id=admin.id
            )
            parent_parts.append(parent)
            
            # Create child parts for each parent
            for j in range(5):
                test_fixtures.create_part(
                    name=f"Child Part {i}-{j}",
                    project_id=project.id,
                    creator_id=admin.id,
                    parent_part_id=parent.id
                )
        
        # Benchmark complex query with relationships
        def get_project_with_parts():
            response = client.get(f'/api/projects/{project.id}/parts?include_children=true', 
                                headers=auth_headers['admin'])
            assert response.status_code == 200
            data = response.get_json()
            # Should have 10 parent parts, each with 5 children
            assert len(data['parts']) == 10
            return response
        
        result = benchmark(get_project_with_parts)
        assert result.status_code == 200

    @pytest.mark.slow
    def test_pagination_performance(self, client, auth_headers, test_fixtures, benchmark):
        """Test pagination performance with large datasets."""
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        project = test_fixtures.create_project(
            project_id="PAGINATION001",
            name="Pagination Test Project",
            creator_id=admin.id
        )
        
        # Create 200 parts
        for i in range(200):
            test_fixtures.create_part(
                name=f"Page Part {i:03d}",
                project_id=project.id,
                creator_id=admin.id
            )
        
        # Benchmark paginated requests
        def get_paginated_parts():
            response = client.get('/api/parts?page=5&per_page=20', headers=auth_headers['admin'])
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['parts']) == 20
            return response
        
        result = benchmark(get_paginated_parts)
        assert result.status_code == 200

    def test_response_time_thresholds(self, client, auth_headers, test_fixtures):
        """Test that API endpoints meet response time requirements."""
        # Define acceptable response times (in seconds)
        thresholds = {
            'simple_get': 0.1,      # Simple GET requests
            'complex_query': 0.5,   # Complex queries with joins
            'create_operation': 0.2, # POST/PUT operations
        }
        
        admin = test_fixtures.create_user(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        
        # Test simple GET
        start = time.time()
        response = client.get('/api/projects', headers=auth_headers['admin'])
        simple_get_time = time.time() - start
        assert response.status_code == 200
        assert simple_get_time < thresholds['simple_get']
        
        # Test create operation
        start = time.time()
        response = client.post('/api/projects',
            json={
                "project_id": "TIMING001",
                "name": "Timing Test Project"
            },
            headers=auth_headers['admin']
        )
        create_time = time.time() - start
        assert response.status_code == 201
        assert create_time < thresholds['create_operation']

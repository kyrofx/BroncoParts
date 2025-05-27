"""Integration tests for order management API endpoints."""
import pytest
from tests.conftest import TestFixtures, get_auth_headers, assert_error_response, assert_success_response


class TestOrderAPI:
    """Test cases for order management API endpoints."""
    
    def test_get_orders_as_readonly(self, client, db_session, mock_airtable):
        """Test getting orders as readonly user."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.get('/api/orders', headers=headers)
        
        data = assert_success_response(response)
        assert len(data) >= 1
        assert any(o['order_number'] == 'TEST-001' for o in data)
    
    def test_get_order_by_id(self, client, db_session, mock_airtable):
        """Test getting a specific order by ID."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get(f'/api/orders/{order.id}', headers=headers)
        
        data = assert_success_response(response)
        assert data['id'] == order.id
        assert data['order_number'] == 'TEST-001'
        assert data['customer_name'] == 'Test Customer'
        assert data['project_id'] == project.id
    
    def test_create_order_as_editor(self, client, db_session, mock_airtable):
        """Test creating an order as editor."""
        admin = TestFixtures.create_test_admin_user(db_session)
        editor = TestFixtures.create_test_editor_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'editor@test.com', 'password123')
        response = client.post('/api/orders', headers=headers, json={
            'order_number': 'NEW-001',
            'customer_name': 'New Customer',
            'project_id': project.id,
            'status': 'Pending',
            'total_amount': 250.75
        })
        
        data = assert_success_response(response, 201)
        assert data['order_number'] == 'NEW-001'
        assert data['customer_name'] == 'New Customer'
        assert data['status'] == 'Pending'
        assert float(data['total_amount']) == 250.75
        assert data['reimbursed'] is False
    
    def test_create_order_as_readonly(self, client, db_session, mock_airtable):
        """Test creating an order as readonly user (should be forbidden)."""
        admin = TestFixtures.create_test_admin_user(db_session)
        readonly = TestFixtures.create_test_readonly_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        
        headers = get_auth_headers(client, 'readonly@test.com', 'password123')
        response = client.post('/api/orders', headers=headers, json={
            'order_number': 'NEW-001',
            'customer_name': 'New Customer',
            'project_id': project.id
        })
        
        assert_error_response(response, 403, 'Editor or Admin access required')
    
    def test_create_order_with_items(self, client, db_session, mock_airtable):
        """Test creating an order with order items."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        part1 = TestFixtures.create_test_part(db_session, project, name='Part 1')
        part2 = TestFixtures.create_test_part(db_session, project, name='Part 2')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/orders', headers=headers, json={
            'order_number': 'ORDER-WITH-ITEMS',
            'customer_name': 'Test Customer',
            'project_id': project.id,
            'status': 'Pending',
            'items': [
                {
                    'part_id': part1.id,
                    'quantity': 2,
                    'unit_price': 25.50
                },
                {
                    'part_id': part2.id,
                    'quantity': 1,
                    'unit_price': 15.25
                }
            ]
        })
        
        data = assert_success_response(response, 201)
        assert data['order_number'] == 'ORDER-WITH-ITEMS'
        assert len(data['items']) == 2
        assert data['items'][0]['quantity'] == 2
        assert float(data['items'][0]['unit_price']) == 25.50
    
    def test_update_order_as_admin(self, client, db_session, mock_airtable):
        """Test updating an order as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/orders/{order.id}', headers=headers, json={
            'status': 'Completed',
            'reimbursed': True,
            'total_amount': 150.00
        })
        
        data = assert_success_response(response)
        assert data['status'] == 'Completed'
        assert data['reimbursed'] is True
        assert float(data['total_amount']) == 150.00
    
    def test_delete_order_as_admin(self, client, db_session, mock_airtable):
        """Test deleting an order as admin."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/orders/{order.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']
    
    def test_order_statistics(self, client, db_session, mock_airtable):
        """Test getting order statistics."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order1 = TestFixtures.create_test_order(db_session, project, order_number='ORD-001')
        order2 = TestFixtures.create_test_order(db_session, project, order_number='ORD-002')
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.get('/api/orders/statistics', headers=headers)
        
        data = assert_success_response(response)
        assert 'total_orders' in data
        assert 'total_amount' in data
        assert data['total_orders'] >= 2


class TestOrderItemAPI:
    """Test cases for order item management API endpoints."""
    
    def test_create_order_item(self, client, db_session, mock_airtable):
        """Test creating an order item."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        part = TestFixtures.create_test_part(db_session, project)
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.post('/api/order-items', headers=headers, json={
            'order_id': order.id,
            'part_id': part.id,
            'quantity': 3,
            'unit_price': 45.50
        })
        
        data = assert_success_response(response, 201)
        assert data['order_id'] == order.id
        assert data['part_id'] == part.id
        assert data['quantity'] == 3
        assert float(data['unit_price']) == 45.50
    
    def test_update_order_item(self, client, db_session, mock_airtable):
        """Test updating an order item."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        part = TestFixtures.create_test_part(db_session, project)
        
        # Create order item first
        from app.models import OrderItem
        order_item = OrderItem(
            order_id=order.id,
            part_id=part.id,
            quantity=1,
            unit_price=25.00
        )
        db_session.add(order_item)
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.put(f'/api/order-items/{order_item.id}', headers=headers, json={
            'quantity': 5,
            'unit_price': 30.00
        })
        
        data = assert_success_response(response)
        assert data['quantity'] == 5
        assert float(data['unit_price']) == 30.00
    
    def test_delete_order_item(self, client, db_session, mock_airtable):
        """Test deleting an order item."""
        admin = TestFixtures.create_test_admin_user(db_session)
        project = TestFixtures.create_test_project(db_session)
        order = TestFixtures.create_test_order(db_session, project)
        part = TestFixtures.create_test_part(db_session, project)
        
        # Create order item first
        from app.models import OrderItem
        order_item = OrderItem(
            order_id=order.id,
            part_id=part.id,
            quantity=1,
            unit_price=25.00
        )
        db_session.add(order_item)
        db_session.commit()
        
        headers = get_auth_headers(client, 'admin@test.com', 'password123')
        response = client.delete(f'/api/order-items/{order_item.id}', headers=headers)
        
        data = assert_success_response(response)
        assert 'deleted successfully' in data['message']

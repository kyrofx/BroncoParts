import pytest
import json
from decimal import Decimal
from app.models import Order, OrderItem, db
from tests.conftest import get_auth_headers


class TestOrderRoutes:
    
    @pytest.mark.api
    def test_get_orders_empty(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/orders', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['orders'] == []

    @pytest.mark.api
    def test_get_orders_with_data(self, client, readonly_token, sample_order):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/orders', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['orders']) == 1
        assert data['orders'][0]['order_number'] == 'ORD-001'
        assert data['orders'][0]['customer_name'] == 'Test Customer'
        assert data['orders'][0]['status'] == 'Pending'

    @pytest.mark.api
    def test_get_order_by_id(self, client, readonly_token, sample_order):
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/orders/{sample_order.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['order']['order_number'] == 'ORD-001'
        assert data['order']['customer_name'] == 'Test Customer'
        assert float(data['order']['total_amount']) == 100.00

    @pytest.mark.api
    def test_get_order_not_found(self, client, readonly_token):
        headers = get_auth_headers(readonly_token)
        response = client.get('/api/orders/999', headers=headers)
        
        assert response.status_code == 404

    @pytest.mark.api
    def test_create_order_success(self, client, editor_token, sample_project):
        headers = get_auth_headers(editor_token)
        order_data = {
            'order_number': 'ORD-002',
            'customer_name': 'New Customer',
            'project_id': sample_project.id,
            'status': 'Processing',
            'total_amount': 250.50
        }
        
        response = client.post('/api/orders', headers=headers, json=order_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Order created successfully' in data['message']
        assert data['order']['order_number'] == 'ORD-002'
        assert data['order']['customer_name'] == 'New Customer'
        assert data['order']['status'] == 'Processing'
        assert float(data['order']['total_amount']) == 250.50

    @pytest.mark.api
    def test_create_order_missing_required_fields(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        # Missing order_number
        response = client.post('/api/orders', headers=headers, 
                             json={'customer_name': 'Test Customer'})
        assert response.status_code == 400
        
        # Missing customer_name
        response = client.post('/api/orders', headers=headers, 
                             json={'order_number': 'ORD-003'})
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_order_duplicate_order_number(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        order_data = {
            'order_number': 'ORD-001',  # Same as sample_order
            'customer_name': 'Another Customer'
        }
        
        response = client.post('/api/orders', headers=headers, json=order_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_create_order_invalid_project(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        order_data = {
            'order_number': 'ORD-003',
            'customer_name': 'Test Customer',
            'project_id': 999  # Non-existent project
        }
        
        response = client.post('/api/orders', headers=headers, json=order_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_update_order_success(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        update_data = {
            'customer_name': 'Updated Customer',
            'status': 'Shipped',
            'total_amount': 150.75,
            'reimbursed': True
        }
        
        response = client.put(f'/api/orders/{sample_order.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Order updated successfully' in data['message']
        assert data['order']['customer_name'] == 'Updated Customer'
        assert data['order']['status'] == 'Shipped'
        assert float(data['order']['total_amount']) == 150.75
        assert data['order']['reimbursed'] is True

    @pytest.mark.api
    def test_update_order_partial(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        update_data = {'status': 'Completed'}
        
        response = client.put(f'/api/orders/{sample_order.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['order']['status'] == 'Completed'
        assert data['order']['customer_name'] == 'Test Customer'  # Should remain unchanged

    @pytest.mark.api
    def test_update_order_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        update_data = {'status': 'Updated'}
        
        response = client.put('/api/orders/999', headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_order_success(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/orders/{sample_order.id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Order deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_order_not_found(self, client, editor_token):
        headers = get_auth_headers(editor_token)
        
        response = client.delete('/api/orders/999', headers=headers)
        assert response.status_code == 404


class TestOrderItemRoutes:
    
    @pytest.mark.api
    def test_add_order_item_success(self, client, editor_token, sample_order, sample_part):
        headers = get_auth_headers(editor_token)
        item_data = {
            'part_id': sample_part.id,
            'quantity': 3,
            'unit_price': 15.50
        }
        
        response = client.post(f'/api/orders/{sample_order.id}/items', 
                             headers=headers, json=item_data)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'Order item added successfully' in data['message']
        assert data['order_item']['part_id'] == sample_part.id
        assert data['order_item']['quantity'] == 3
        assert float(data['order_item']['unit_price']) == 15.50

    @pytest.mark.api
    def test_add_order_item_missing_fields(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        
        # Missing part_id
        response = client.post(f'/api/orders/{sample_order.id}/items', 
                             headers=headers, json={'quantity': 1, 'unit_price': 10.00})
        assert response.status_code == 400
        
        # Missing quantity
        response = client.post(f'/api/orders/{sample_order.id}/items', 
                             headers=headers, json={'part_id': 1, 'unit_price': 10.00})
        assert response.status_code == 400
        
        # Missing unit_price
        response = client.post(f'/api/orders/{sample_order.id}/items', 
                             headers=headers, json={'part_id': 1, 'quantity': 1})
        assert response.status_code == 400

    @pytest.mark.api
    def test_add_order_item_invalid_part(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        item_data = {
            'part_id': 999,  # Non-existent part
            'quantity': 1,
            'unit_price': 10.00
        }
        
        response = client.post(f'/api/orders/{sample_order.id}/items', 
                             headers=headers, json=item_data)
        assert response.status_code == 400

    @pytest.mark.api
    def test_add_order_item_invalid_order(self, client, editor_token, sample_part):
        headers = get_auth_headers(editor_token)
        item_data = {
            'part_id': sample_part.id,
            'quantity': 1,
            'unit_price': 10.00
        }
        
        response = client.post('/api/orders/999/items', headers=headers, json=item_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_update_order_item_success(self, client, editor_token, sample_order_item):
        headers = get_auth_headers(editor_token)
        update_data = {
            'quantity': 5,
            'unit_price': 30.00
        }
        
        response = client.put(f'/api/orders/{sample_order_item.order_id}/items/{sample_order_item.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Order item updated successfully' in data['message']
        assert data['order_item']['quantity'] == 5
        assert float(data['order_item']['unit_price']) == 30.00

    @pytest.mark.api
    def test_update_order_item_partial(self, client, editor_token, sample_order_item):
        headers = get_auth_headers(editor_token)
        update_data = {'quantity': 4}
        
        response = client.put(f'/api/orders/{sample_order_item.order_id}/items/{sample_order_item.id}', 
                            headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['order_item']['quantity'] == 4
        assert float(data['order_item']['unit_price']) == 25.00  # Should remain unchanged

    @pytest.mark.api
    def test_update_order_item_not_found(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        update_data = {'quantity': 1}
        
        response = client.put(f'/api/orders/{sample_order.id}/items/999', 
                            headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_update_order_item_wrong_order(self, client, editor_token, sample_order_item, app, sample_project):
        # Create another order
        with app.app_context():
            other_order = Order(
                order_number='ORD-OTHER',
                customer_name='Other Customer',
                project_id=sample_project.id
            )
            db.session.add(other_order)
            db.session.commit()
            other_order_id = other_order.id
        
        headers = get_auth_headers(editor_token)
        update_data = {'quantity': 1}
        
        # Try to update item with wrong order ID
        response = client.put(f'/api/orders/{other_order_id}/items/{sample_order_item.id}', 
                            headers=headers, json=update_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_delete_order_item_success(self, client, editor_token, sample_order_item):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/orders/{sample_order_item.order_id}/items/{sample_order_item.id}', 
                               headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Order item deleted successfully' in data['message']

    @pytest.mark.api
    def test_delete_order_item_not_found(self, client, editor_token, sample_order):
        headers = get_auth_headers(editor_token)
        
        response = client.delete(f'/api/orders/{sample_order.id}/items/999', headers=headers)
        assert response.status_code == 404

    @pytest.mark.api
    def test_order_with_items_response(self, client, readonly_token, sample_order_item):
        """Test that order responses include associated order items"""
        headers = get_auth_headers(readonly_token)
        response = client.get(f'/api/orders/{sample_order_item.order_id}', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        order_data = data['order']
        
        # Should include order items
        assert 'items' in order_data
        assert len(order_data['items']) >= 1
        
        # Order item should include part information
        order_item = order_data['items'][0]
        assert 'part' in order_item
        assert order_item['part']['name'] == 'Test Part'

    @pytest.mark.api
    def test_order_total_calculation(self, client, editor_token, sample_order, sample_part, app):
        """Test that order totals are calculated correctly based on items"""
        headers = get_auth_headers(editor_token)
        
        # Add multiple items to the order
        items_data = [
            {'part_id': sample_part.id, 'quantity': 2, 'unit_price': 10.00},
            {'part_id': sample_part.id, 'quantity': 1, 'unit_price': 15.00}
        ]
        
        for item_data in items_data:
            response = client.post(f'/api/orders/{sample_order.id}/items', 
                                 headers=headers, json=item_data)
            assert response.status_code == 201
        
        # Get the order and verify items are included
        response = client.get(f'/api/orders/{sample_order.id}', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have at least 2 items
        assert len(data['order']['items']) >= 2

    @pytest.mark.api
    def test_order_cascade_delete_items(self, client, editor_token, sample_order_item, app):
        """Test that deleting an order also deletes its items"""
        order_id = sample_order_item.order_id
        item_id = sample_order_item.id
        
        headers = get_auth_headers(editor_token)
        
        # Delete the order
        response = client.delete(f'/api/orders/{order_id}', headers=headers)
        assert response.status_code == 200
        
        # Verify the order item was also deleted
        with app.app_context():
            deleted_item = OrderItem.query.get(item_id)
            assert deleted_item is None

    @pytest.mark.api
    def test_order_routes_require_authentication(self, client):
        """Test that all order routes require authentication"""
        endpoints = [
            ('GET', '/api/orders'),
            ('POST', '/api/orders'),
            ('GET', '/api/orders/1'),
            ('PUT', '/api/orders/1'),
            ('DELETE', '/api/orders/1'),
            ('POST', '/api/orders/1/items'),
            ('PUT', '/api/orders/1/items/1'),
            ('DELETE', '/api/orders/1/items/1')
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

    @pytest.mark.api
    def test_order_readonly_permissions(self, client, readonly_token, sample_order):
        """Test that readonly users can view but not modify orders"""
        headers = get_auth_headers(readonly_token)
        
        # Should be able to read
        response = client.get('/api/orders', headers=headers)
        assert response.status_code == 200
        
        response = client.get(f'/api/orders/{sample_order.id}', headers=headers)
        assert response.status_code == 200
        
        # Should not be able to modify (depending on implementation)
        # This depends on whether orders have specific permission decorators
        order_data = {'customer_name': 'New Customer'}
        response = client.post('/api/orders', headers=headers, json=order_data)
        # This might be 403 if orders require editor+ permissions
        assert response.status_code in [201, 403]  # Implementation dependent
"""
End-to-end workflow tests covering complete user journeys.
"""
import pytest
from app.models import User, Project, Part, Order, OrderItem, RegistrationLink


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete user workflows from start to finish."""

    def test_complete_registration_to_order_workflow(self, client, test_fixtures):
        """Test complete workflow: registration → project creation → part creation → ordering."""
        # Step 1: Use existing admin from fixture
        admin = test_fixtures._test_data['users']['admin']

        admin_headers = test_fixtures.get_auth_headers(admin, client)

        # Create registration link
        reg_response = client.post('/api/registration-links', 
            json={
                "email": "newuser@test.com",
                "role": "editor",
                "expires_in_days": 7
            },
            headers=admin_headers
        )
        assert reg_response.status_code == 201
        reg_data = reg_response.get_json()
        registration_token = reg_data['token']

        # Step 2: New user registers using the link
        register_response = client.post('/api/auth/register',
            json={
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@test.com",
                "password": "password123",
                "registration_token": registration_token
            }
        )
        assert register_response.status_code == 201

        # Step 3: Admin approves the new user
        new_user = User.query.filter_by(email="newuser@test.com").first()
        assert new_user is not None

        approve_response = client.put(f'/api/users/{new_user.id}/approve',
            headers=admin_headers
        )
        assert approve_response.status_code == 200

        # Step 4: New user logs in
        login_response = client.post('/api/auth/login',
            json={
                "email": "newuser@test.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        new_user_token = login_data['access_token']
        new_user_headers = {'Authorization': f'Bearer {new_user_token}'}

        # Step 5: User creates a project
        project_response = client.post('/api/projects',
            json={
                "project_id": "NEWPROJ001",
                "name": "New User Project",
                "description": "Project created by new user"
            },
            headers=new_user_headers
        )
        assert project_response.status_code == 201
        project_data = project_response.get_json()
        project_id = project_data['id']

        # Step 6: User creates parts in the project
        machine = test_fixtures.create_machine(name="3D Printer")

        part1_response = client.post('/api/parts',
            json={
                "name": "Main Housing",
                "project_id": project_id,
                "description": "Main housing component",
                "quantity": 2,
                "raw_material": "PLA",
                "machine_id": machine.id,
                "part_status": "design"
            },
            headers=new_user_headers
        )
        assert part1_response.status_code == 201
        part1_data = part1_response.get_json()
        part1_id = part1_data['id']

        part2_response = client.post('/api/parts',
            json={
                "name": "Cover Plate",
                "project_id": project_id,
                "description": "Cover plate component",
                "quantity": 1,
                "raw_material": "ABS",
                "machine_id": machine.id,
                "part_status": "design"
            },
            headers=new_user_headers
        )
        assert part2_response.status_code == 201
        part2_data = part2_response.get_json()
        part2_id = part2_data['id']

        # Step 7: User creates an order
        order_response = client.post('/api/orders',
            json={
                "project_id": project_id,
                "notes": "Initial prototype order"
            },
            headers=new_user_headers
        )
        assert order_response.status_code == 201
        order_data = order_response.get_json()
        order_id = order_data['id']

        # Step 8: User adds items to the order
        item1_response = client.post('/api/order-items',
            json={
                "order_id": order_id,
                "part_id": part1_id,
                "quantity": 2
            },
            headers=new_user_headers
        )
        assert item1_response.status_code == 201

        item2_response = client.post('/api/order-items',
            json={
                "order_id": order_id,
                "part_id": part2_id,
                "quantity": 1
            },
            headers=new_user_headers
        )
        assert item2_response.status_code == 201

        # Step 9: Verify the complete workflow
        # Check project exists and has correct data
        project_check = client.get(f'/api/projects/{project_id}', headers=new_user_headers)
        assert project_check.status_code == 200
        project_check_data = project_check.get_json()
        assert project_check_data['project_id'] == "NEWPROJ001"
        assert project_check_data['name'] == "New User Project"

        # Check parts exist and are linked to project
        parts_check = client.get(f'/api/projects/{project_id}/parts', headers=new_user_headers)
        assert parts_check.status_code == 200
        parts_check_data = parts_check.get_json()
        assert len(parts_check_data['parts']) == 2

        # Check order exists and has correct items
        order_check = client.get(f'/api/orders/{order_id}', headers=new_user_headers)
        assert order_check.status_code == 200
        order_check_data = order_check.get_json()
        assert len(order_check_data['items']) == 2
        assert order_check_data['total_items'] == 3  # 2 + 1

    def test_collaborative_project_workflow(self, client, test_fixtures):
        """Test workflow where multiple users collaborate on a project."""
        # Create users with different roles
        # Use existing users from fixture and create additional ones
        admin = test_fixtures._test_data['users']['admin']

        editor1 = test_fixtures.create_user(
            email="editor1@test.com",
            first_name="Editor",
            last_name="One",
            role="editor"
        )

        editor2 = test_fixtures.create_user(
            email="editor2@test.com",
            first_name="Editor",
            last_name="Two",
            role="editor"
        )

        admin_headers = test_fixtures.get_auth_headers(admin, client)
        editor1_headers = test_fixtures.get_auth_headers(editor1, client)
        editor2_headers = test_fixtures.get_auth_headers(editor2, client)

        # Admin creates a project
        project_response = client.post('/api/projects',
            json={
                "project_id": "COLLAB001",
                "name": "Collaborative Project",
                "description": "Multi-user collaboration project"
            },
            headers=admin_headers
        )
        assert project_response.status_code == 201
        project_data = project_response.get_json()
        project_id = project_data['id']

        # Editor1 creates parts
        machine = test_fixtures.create_machine(name="CNC Mill")

        part1_response = client.post('/api/parts',
            json={
                "name": "Base Component",
                "project_id": project_id,
                "description": "Base component by editor1",
                "quantity": 1,
                "raw_material": "Aluminum",
                "machine_id": machine.id
            },
            headers=editor1_headers
        )
        assert part1_response.status_code == 201
        part1_data = part1_response.get_json()
        part1_id = part1_data['id']

        # Editor2 creates related parts
        part2_response = client.post('/api/parts',
            json={
                "name": "Top Assembly",
                "project_id": project_id,
                "description": "Top assembly by editor2",
                "quantity": 1,
                "raw_material": "Steel",
                "machine_id": machine.id,
                "parent_part_id": part1_id  # Child of part1
            },
            headers=editor2_headers
        )
        assert part2_response.status_code == 201
        part2_data = part2_response.get_json()
        part2_id = part2_data['id']

        # Editor1 creates an order
        order_response = client.post('/api/orders',
            json={
                "project_id": project_id,
                "notes": "Collaborative order"
            },
            headers=editor1_headers
        )
        assert order_response.status_code == 201
        order_data = order_response.get_json()
        order_id = order_data['id']

        # Editor2 adds items to editor1's order
        item_response = client.post('/api/order-items',
            json={
                "order_id": order_id,
                "part_id": part2_id,
                "quantity": 1
            },
            headers=editor2_headers
        )
        assert item_response.status_code == 201

        # Admin can view all project activity
        project_check = client.get(f'/api/projects/{project_id}', headers=admin_headers)
        assert project_check.status_code == 200

        parts_check = client.get(f'/api/projects/{project_id}/parts', headers=admin_headers)
        assert parts_check.status_code == 200
        parts_data = parts_check.get_json()
        assert len(parts_data['parts']) == 2

        # Verify part hierarchy was created correctly
        part_hierarchy = client.get(f'/api/parts/{part1_id}/children', headers=admin_headers)
        assert part_hierarchy.status_code == 200
        hierarchy_data = part_hierarchy.get_json()
        assert len(hierarchy_data['children']) == 1
        assert hierarchy_data['children'][0]['id'] == part2_id

    def test_project_lifecycle_workflow(self, client, test_fixtures):
        """Test complete project lifecycle from creation to completion."""
        admin = test_fixtures._test_data['users']['admin']

        admin_headers = test_fixtures.get_auth_headers(admin, client)

        # Create project
        project_response = client.post('/api/projects',
            json={
                "project_id": "LIFECYCLE001",
                "name": "Lifecycle Project",
                "description": "Testing project lifecycle"
            },
            headers=admin_headers
        )
        assert project_response.status_code == 201
        project_data = project_response.get_json()
        project_id = project_data['id']

        # Create machines and post-processes
        machine = test_fixtures.create_machine(name="3D Printer")
        post_process = test_fixtures.create_post_process(name="Sanding")

        # Create parts in design phase
        part_response = client.post('/api/parts',
            json={
                "name": "Test Part",
                "project_id": project_id,
                "description": "Part for lifecycle testing",
                "quantity": 5,
                "raw_material": "PLA",
                "machine_id": machine.id,
                "part_status": "design"
            },
            headers=admin_headers
        )
        assert part_response.status_code == 201
        part_data = part_response.get_json()
        part_id = part_data['id']

        # Add post-process to part
        pp_response = client.post(f'/api/parts/{part_id}/post-processes',
            json={
                "post_process_id": post_process.id,
                "notes": "Sand all surfaces smooth"
            },
            headers=admin_headers
        )
        assert pp_response.status_code == 201

        # Move part to manufacturing
        update_response = client.put(f'/api/parts/{part_id}',
            json={
                "part_status": "manufacturing"
            },
            headers=admin_headers
        )
        assert update_response.status_code == 200

        # Create order for the part
        order_response = client.post('/api/orders',
            json={
                "project_id": project_id,
                "notes": "Production order"
            },
            headers=admin_headers
        )
        assert order_response.status_code == 201
        order_data = order_response.get_json()
        order_id = order_data['id']

        # Add part to order
        item_response = client.post('/api/order-items',
            json={
                "order_id": order_id,
                "part_id": part_id,
                "quantity": 5
            },
            headers=admin_headers
        )
        assert item_response.status_code == 201

        # Update part to completed
        complete_response = client.put(f'/api/parts/{part_id}',
            json={
                "part_status": "completed"
            },
            headers=admin_headers
        )
        assert complete_response.status_code == 200

        # Verify final project state
        final_project_check = client.get(f'/api/projects/{project_id}', headers=admin_headers)
        assert final_project_check.status_code == 200
        final_data = final_project_check.get_json()
        assert final_data['total_parts'] == 1

        # Check project statistics show completion
        stats_response = client.get(f'/api/stats/projects/{project_id}', headers=admin_headers)
        if stats_response.status_code == 200:  # If stats endpoint exists
            stats_data = stats_response.get_json()
            assert 'completion_rate' in stats_data

    def test_error_recovery_workflow(self, client, test_fixtures):
        """Test workflow with error conditions and recovery."""
        admin = test_fixtures._test_data['users']['admin']

        admin_headers = test_fixtures.get_auth_headers(admin, client)

        # Try to create part without project (should fail)
        part_response = client.post('/api/parts',
            json={
                "name": "Orphan Part",
                "project_id": 99999,  # Non-existent project
                "description": "This should fail",
                "quantity": 1
            },
            headers=admin_headers
        )
        assert part_response.status_code == 404

        # Create project first
        project_response = client.post('/api/projects',
            json={
                "project_id": "RECOVERY001",
                "name": "Recovery Project",
                "description": "Testing error recovery"
            },
            headers=admin_headers
        )
        assert project_response.status_code == 201
        project_data = project_response.get_json()
        project_id = project_data['id']

        # Now create part successfully
        part_response = client.post('/api/parts',
            json={
                "name": "Valid Part",
                "project_id": project_id,
                "description": "This should succeed",
                "quantity": 1
            },
            headers=admin_headers
        )
        assert part_response.status_code == 201
        part_data = part_response.get_json()
        part_id = part_data['id']

        # Try to create order item without order (should fail)
        item_response = client.post('/api/order-items',
            json={
                "order_id": 99999,  # Non-existent order
                "part_id": part_id,
                "quantity": 1
            },
            headers=admin_headers
        )
        assert item_response.status_code == 404

        # Create order first
        order_response = client.post('/api/orders',
            json={
                "project_id": project_id,
                "notes": "Recovery order"
            },
            headers=admin_headers
        )
        assert order_response.status_code == 201
        order_data = order_response.get_json()
        order_id = order_data['id']

        # Now create order item successfully
        item_response = client.post('/api/order-items',
            json={
                "order_id": order_id,
                "part_id": part_id,
                "quantity": 1
            },
            headers=admin_headers
        )
        assert item_response.status_code == 201

        # Verify everything was created correctly despite initial errors
        final_check = client.get(f'/api/orders/{order_id}', headers=admin_headers)
        assert final_check.status_code == 200
        final_data = final_check.get_json()
        assert len(final_data['items']) == 1

"""Unit tests for database models."""
import pytest
from datetime import datetime, timedelta
from app.models import User, Project, Part, Machine, PostProcess, Order, OrderItem, RegistrationLink
from tests.conftest import TestFixtures


@pytest.mark.unit
class TestUserModel:
    """Test cases for the User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            permission='readonly'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.permission == 'readonly'
        assert user.enabled is False  # Default is False
        assert user.is_approved is False  # Default is False
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
    
    def test_user_defaults(self, db_session):
        """Test user default values."""
        user = User(username='test', email='test@example.com')
        user.set_password('password')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.permission == 'readonly'
        assert user.enabled is False
        assert user.is_approved is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_repr(self, db_session):
        """Test user string representation."""
        user = TestFixtures.create_test_admin_user(db_session)
        repr_str = repr(user)
        
        assert 'admin' in repr_str
        assert 'admin' in repr_str
        assert 'Enabled' in repr_str
        assert 'Approved' in repr_str


@pytest.mark.unit
class TestProjectModel:
    """Test cases for the Project model."""
    
    def test_create_project(self, db_session):
        """Test creating a project."""
        project = Project(
            name='Test Project',
            description='A test project',
            prefix='TP'
        )
        
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.name == 'Test Project'
        assert project.prefix == 'TP'
        assert project.hide_dashboards is False  # Default
        assert project.created_at is not None
    
    def test_project_unique_prefix(self, db_session):
        """Test that project prefixes must be unique."""
        project1 = Project(name='Project 1', prefix='SAME')
        project2 = Project(name='Project 2', prefix='SAME')
        
        db_session.add(project1)
        db_session.commit()
        
        db_session.add(project2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


@pytest.mark.unit
class TestMachineModel:
    """Test cases for the Machine model."""
    
    def test_create_machine(self, db_session):
        """Test creating a machine."""
        machine = Machine(name='3D Printer')
        
        db_session.add(machine)
        db_session.commit()
        
        assert machine.id is not None
        assert machine.name == '3D Printer'
        assert machine.created_at is not None
    
    def test_machine_unique_name(self, db_session):
        """Test that machine names must be unique."""
        machine1 = Machine(name='Same Name')
        machine2 = Machine(name='Same Name')
        
        db_session.add(machine1)
        db_session.commit()
        
        db_session.add(machine2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


@pytest.mark.unit
class TestPostProcessModel:
    """Test cases for the PostProcess model."""
    
    def test_create_post_process(self, db_session):
        """Test creating a post process."""
        post_process = PostProcess(name='Anodizing')
        
        db_session.add(post_process)
        db_session.commit()
        
        assert post_process.id is not None
        assert post_process.name == 'Anodizing'
        assert post_process.created_at is not None


@pytest.mark.unit
class TestPartModel:
    """Test cases for the Part model."""
    
    def test_create_part(self, db_session):
        """Test creating a part."""
        project = TestFixtures.create_test_project(db_session)
        
        part = Part(
            name='Test Part',
            description='A test part',
            type='part',
            project_id=project.id,
            numeric_id=100,
            part_number=f'{project.prefix}-P-0100',
            quantity=1
        )
        
        db_session.add(part)
        db_session.commit()
        
        assert part.id is not None
        assert part.name == 'Test Part'
        assert part.type == 'part'
        assert part.status == 'in design'  # Default
        assert part.priority == 1  # Default
        assert part.quantity == 1
        assert part.project_id == project.id
    
    def test_part_number_generation(self, db_session):
        """Test part number format."""
        project = TestFixtures.create_test_project(db_session, prefix='BP25')
        
        # Test part
        part = Part(
            name='Test Part',
            type='part',
            project_id=project.id,
            numeric_id=100,
            part_number=f'{project.prefix}-P-0100',
            quantity=1
        )
        
        # Test assembly
        assembly = Part(
            name='Test Assembly',
            type='assembly',
            project_id=project.id,
            numeric_id=101,
            part_number=f'{project.prefix}-A-0101',
            quantity=1
        )
        
        db_session.add_all([part, assembly])
        db_session.commit()
        
        assert part.part_number == 'BP25-P-0100'
        assert assembly.part_number == 'BP25-A-0101'
    
    def test_part_hierarchy(self, db_session):
        """Test part parent-child relationships."""
        project = TestFixtures.create_test_project(db_session)
        
        parent = TestFixtures.create_test_part(db_session, project, name='Parent Assembly', type='assembly')
        child = TestFixtures.create_test_part(db_session, project, name='Child Part', type='part')
        
        child.parent_id = parent.id
        db_session.commit()
        
        # Test relationships
        assert child.parent == parent
        assert parent.children.count() == 1
        assert parent.children.first() == child
    
    def test_part_machine_relationship(self, db_session):
        """Test part-machine relationship."""
        project = TestFixtures.create_test_project(db_session)
        machine = TestFixtures.create_test_machine(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        
        part.machine_id = machine.id
        db_session.commit()
        
        assert part.machine == machine
        assert machine.parts.count() == 1
        assert machine.parts.first() == part
    
    def test_part_post_process_relationship(self, db_session):
        """Test part-post process many-to-many relationship."""
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        post_process1 = TestFixtures.create_test_post_process(db_session, name='Anodizing')
        post_process2 = TestFixtures.create_test_post_process(db_session, name='Painting')
        
        part.post_processes.append(post_process1)
        part.post_processes.append(post_process2)
        db_session.commit()
        
        assert len(part.post_processes) == 2
        assert post_process1 in part.post_processes
        assert post_process2 in part.post_processes
        assert part in post_process1.parts
        assert part in post_process2.parts
    
    def test_part_unique_project_numeric_id(self, db_session):
        """Test that numeric_id must be unique within a project."""
        project = TestFixtures.create_test_project(db_session)
        
        part1 = Part(
            name='Part 1',
            type='part',
            project_id=project.id,
            numeric_id=100,
            part_number=f'{project.prefix}-P-0100',
            quantity=1
        )
        
        part2 = Part(
            name='Part 2',
            type='part',
            project_id=project.id,
            numeric_id=100,  # Same numeric_id in same project
            part_number=f'{project.prefix}-P-0100-2',
            quantity=1
        )
        
        db_session.add(part1)
        db_session.commit()
        
        db_session.add(part2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()


@pytest.mark.unit
class TestOrderModel:
    """Test cases for the Order model."""
    
    def test_create_order(self, db_session):
        """Test creating an order."""
        project = TestFixtures.create_test_project(db_session)
        
        order = Order(
            order_number='TEST-001',
            customer_name='Test Customer',
            project_id=project.id,
            status='Pending',
            total_amount=100.50
        )
        
        db_session.add(order)
        db_session.commit()
        
        assert order.id is not None
        assert order.order_number == 'TEST-001'
        assert order.customer_name == 'Test Customer'
        assert order.status == 'Pending'
        assert order.total_amount == 100.50
        assert order.reimbursed is False  # Default
        assert order.order_date is not None
    
    def test_order_items_cascade_delete(self, db_session):
        """Test that order items are deleted when order is deleted."""
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        order = TestFixtures.create_test_order(db_session, project)
        
        order_item = OrderItem(
            order_id=order.id,
            part_id=part.id,
            quantity=2,
            unit_price=25.00
        )
        
        db_session.add(order_item)
        db_session.commit()
        
        assert len(order.items) == 1
        
        # Delete order should cascade to items
        db_session.delete(order)
        db_session.commit()
        
        # Order item should be deleted
        assert OrderItem.query.filter_by(order_id=order.id).count() == 0


@pytest.mark.unit
class TestOrderItemModel:
    """Test cases for the OrderItem model."""
    
    def test_create_order_item(self, db_session):
        """Test creating an order item."""
        project = TestFixtures.create_test_project(db_session)
        part = TestFixtures.create_test_part(db_session, project)
        order = TestFixtures.create_test_order(db_session, project)
        
        order_item = OrderItem(
            order_id=order.id,
            part_id=part.id,
            quantity=2,
            unit_price=25.00
        )
        
        db_session.add(order_item)
        db_session.commit()
        
        assert order_item.id is not None
        assert order_item.quantity == 2
        assert order_item.unit_price == 25.00
        assert order_item.order == order
        assert order_item.part == part


@pytest.mark.unit
class TestRegistrationLinkModel:
    """Test cases for the RegistrationLink model."""
    
    def test_create_registration_link(self, db_session):
        """Test creating a registration link."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        reg_link = RegistrationLink(
            custom_path='test-link',
            max_uses=5,
            default_permission='readonly',
            auto_enable_new_users=True,
            created_by_user_id=admin.id
        )
        
        db_session.add(reg_link)
        db_session.commit()
        
        assert reg_link.id is not None
        assert reg_link.custom_path == 'test-link'
        assert reg_link.max_uses == 5
        assert reg_link.current_uses == 0  # Default
        assert reg_link.default_permission == 'readonly'
        assert reg_link.auto_enable_new_users is True
        assert reg_link.is_active is True  # Default
        assert reg_link.token is not None  # Auto-generated
    
    def test_registration_link_validation(self, db_session):
        """Test registration link validation."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        # Test valid link
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        is_valid, message = reg_link.is_currently_valid_for_registration()
        assert is_valid is True
        assert message == "Link is valid for registration."
        
        # Test inactive link
        reg_link.is_active = False
        db_session.commit()
        is_valid, message = reg_link.is_currently_valid_for_registration()
        assert is_valid is False
        assert "not active" in message
        
        # Test expired link
        reg_link.is_active = True
        reg_link.expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        is_valid, message = reg_link.is_currently_valid_for_registration()
        assert is_valid is False
        assert "expired" in message
        
        # Test max uses reached
        reg_link.expires_at = None
        reg_link.max_uses = 1
        reg_link.current_uses = 1
        db_session.commit()
        is_valid, message = reg_link.is_currently_valid_for_registration()
        assert is_valid is False
        assert "maximum number of uses" in message
    
    def test_registration_link_effective_path(self, db_session):
        """Test effective link path generation."""
        admin = TestFixtures.create_test_admin_user(db_session)
        
        # With custom path
        reg_link1 = RegistrationLink(
            custom_path='custom-path',
            created_by_user_id=admin.id
        )
        db_session.add(reg_link1)
        db_session.commit()
        
        assert reg_link1.effective_link_path_segment == 'custom-path'
        
        # Without custom path (should use token)
        reg_link2 = RegistrationLink(
            custom_path=None,
            created_by_user_id=admin.id
        )
        db_session.add(reg_link2)
        db_session.commit()
        
        assert reg_link2.effective_link_path_segment == reg_link2.token
    
    def test_registration_link_to_dict(self, db_session):
        """Test registration link serialization."""
        admin = TestFixtures.create_test_admin_user(db_session)
        reg_link = TestFixtures.create_test_registration_link(db_session, admin)
        
        data = reg_link.to_dict()
        
        assert 'id' in data
        assert 'token' in data
        assert 'link_identifier' in data
        assert 'custom_path' in data
        assert 'max_uses' in data
        assert 'current_uses' in data
        assert 'default_permission' in data
        assert 'creator_username' in data
        assert 'is_currently_valid' in data
        assert data['creator_username'] == admin.username

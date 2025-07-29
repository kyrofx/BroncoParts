import pytest
from datetime import datetime, timedelta
from app.models import User, Project, Part, Machine, PostProcess, Order, OrderItem, RegistrationLink
from app import db
from sqlalchemy.exc import IntegrityError


class TestUserModel:
    
    @pytest.mark.models
    def test_user_creation(self, app):
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                permission='readonly'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.permission == 'readonly'
            assert user.enabled is False  # Default
            assert user.is_approved is False  # Default
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')

    @pytest.mark.models
    def test_user_unique_constraints(self, app):
        with app.app_context():
            user1 = User(username='testuser', email='test@example.com', permission='readonly')
            user1.set_password('password')
            db.session.add(user1)
            db.session.commit()
            
            # Test unique username
            user2 = User(username='testuser', email='different@example.com', permission='readonly')
            user2.set_password('password')
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            
            db.session.rollback()
            
            # Test unique email
            user3 = User(username='different', email='test@example.com', permission='readonly')
            user3.set_password('password')
            db.session.add(user3)
            with pytest.raises(IntegrityError):
                db.session.commit()

    @pytest.mark.models
    def test_user_to_dict(self, app):
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                permission='admin',
                enabled=True,
                is_approved=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            assert user_dict['username'] == 'testuser'
            assert user_dict['email'] == 'test@example.com'
            assert user_dict['permission'] == 'admin'
            assert user_dict['enabled'] is True
            assert user_dict['is_approved'] is True
            assert 'password_hash' not in user_dict


class TestProjectModel:
    
    @pytest.mark.models
    def test_project_creation(self, app):
        with app.app_context():
            project = Project(
                name='Test Project',
                prefix='TP',
                description='A test project'
            )
            db.session.add(project)
            db.session.commit()
            
            assert project.id is not None
            assert project.name == 'Test Project'
            assert project.prefix == 'TP'
            assert project.description == 'A test project'
            assert project.hide_dashboards is False

    @pytest.mark.models
    def test_project_unique_prefix(self, app):
        with app.app_context():
            project1 = Project(name='Project 1', prefix='TP')
            project2 = Project(name='Project 2', prefix='TP')
            
            db.session.add(project1)
            db.session.commit()
            
            db.session.add(project2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestMachineModel:
    
    @pytest.mark.models
    def test_machine_creation(self, app):
        with app.app_context():
            machine = Machine(name='CNC Mill', is_active=True)
            db.session.add(machine)
            db.session.commit()
            
            assert machine.id is not None
            assert machine.name == 'CNC Mill'
            assert machine.is_active is True

    @pytest.mark.models
    def test_machine_unique_name(self, app):
        with app.app_context():
            machine1 = Machine(name='CNC Mill')
            machine2 = Machine(name='CNC Mill')
            
            db.session.add(machine1)
            db.session.commit()
            
            db.session.add(machine2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestPostProcessModel:
    
    @pytest.mark.models
    def test_post_process_creation(self, app):
        with app.app_context():
            pp = PostProcess(
                name='Anodizing',
                description='Aluminum anodizing process',
                is_active=True
            )
            db.session.add(pp)
            db.session.commit()
            
            assert pp.id is not None
            assert pp.name == 'Anodizing'
            assert pp.description == 'Aluminum anodizing process'
            assert pp.is_active is True

    @pytest.mark.models
    def test_post_process_unique_name(self, app):
        with app.app_context():
            pp1 = PostProcess(name='Anodizing')
            pp2 = PostProcess(name='Anodizing')
            
            db.session.add(pp1)
            db.session.commit()
            
            db.session.add(pp2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestPartModel:
    
    @pytest.mark.models
    def test_part_creation(self, app, sample_project, sample_machine, sample_post_process):
        with app.app_context():
            part = Part(
                name='Test Part',
                part_number='TP-P-0001',
                numeric_id=1,
                description='A test part',
                type='part',
                project_id=sample_project.id,
                machine_id=sample_machine.id,
                status='in design',
                quantity=5,
                raw_material='Steel'
            )
            part.post_processes.append(sample_post_process)
            db.session.add(part)
            db.session.commit()
            
            assert part.id is not None
            assert part.name == 'Test Part'
            assert part.part_number == 'TP-P-0001'
            assert part.numeric_id == 1
            assert part.type == 'part'
            assert part.machine_id == sample_machine.id
            assert len(part.post_processes) == 1
            assert part.post_processes[0].name == 'Test Post Process'

    @pytest.mark.models
    def test_part_unique_constraints(self, app, sample_project):
        with app.app_context():
            part1 = Part(
                name='Part 1',
                part_number='TP-P-0001',
                numeric_id=1,
                type='part',
                project_id=sample_project.id,
                quantity=1
            )
            db.session.add(part1)
            db.session.commit()
            
            # Test unique part_number
            part2 = Part(
                name='Part 2',
                part_number='TP-P-0001',
                numeric_id=2,
                type='part',
                project_id=sample_project.id,
                quantity=1
            )
            db.session.add(part2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            
            db.session.rollback()
            
            # Test unique project_id + numeric_id combination
            part3 = Part(
                name='Part 3',
                part_number='TP-P-0002',
                numeric_id=1,  # Same numeric_id as part1
                type='part',
                project_id=sample_project.id,  # Same project as part1
                quantity=1
            )
            db.session.add(part3)
            with pytest.raises(IntegrityError):
                db.session.commit()

    @pytest.mark.models
    def test_part_hierarchical_relationships(self, app, sample_project):
        with app.app_context():
            # Create assembly
            assembly = Part(
                name='Assembly',
                part_number='TP-A-0001',
                numeric_id=1,
                type='assembly',
                project_id=sample_project.id,
                quantity=1
            )
            db.session.add(assembly)
            db.session.commit()
            
            # Create parts under assembly
            part1 = Part(
                name='Part 1',
                part_number='TP-P-0002',
                numeric_id=2,
                type='part',
                project_id=sample_project.id,
                parent_id=assembly.id,
                quantity=2
            )
            part2 = Part(
                name='Part 2',
                part_number='TP-P-0003',
                numeric_id=3,
                type='part',
                project_id=sample_project.id,
                parent_id=assembly.id,
                quantity=1
            )
            db.session.add_all([part1, part2])
            db.session.commit()
            
            # Test relationships
            assert len(list(assembly.children)) == 2
            assert part1.parent.id == assembly.id
            assert part2.parent.id == assembly.id


class TestOrderModel:
    
    @pytest.mark.models
    def test_order_creation(self, app, sample_project):
        with app.app_context():
            order = Order(
                order_number='ORD-001',
                customer_name='Test Customer',
                project_id=sample_project.id,
                status='Pending',
                total_amount=150.00
            )
            db.session.add(order)
            db.session.commit()
            
            assert order.id is not None
            assert order.order_number == 'ORD-001'
            assert order.customer_name == 'Test Customer'
            assert order.status == 'Pending'
            assert float(order.total_amount) == 150.00

    @pytest.mark.models
    def test_order_unique_order_number(self, app):
        with app.app_context():
            order1 = Order(order_number='ORD-001', customer_name='Customer 1')
            order2 = Order(order_number='ORD-001', customer_name='Customer 2')
            
            db.session.add(order1)
            db.session.commit()
            
            db.session.add(order2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestOrderItemModel:
    
    @pytest.mark.models
    def test_order_item_creation(self, app, sample_order, sample_part):
        with app.app_context():
            order_item = OrderItem(
                order_id=sample_order.id,
                part_id=sample_part.id,
                quantity=3,
                unit_price=25.50
            )
            db.session.add(order_item)
            db.session.commit()
            
            assert order_item.id is not None
            assert order_item.order_id == sample_order.id
            assert order_item.part_id == sample_part.id
            assert order_item.quantity == 3
            assert float(order_item.unit_price) == 25.50

    @pytest.mark.models
    def test_order_cascade_delete(self, app, sample_order, sample_part):
        with app.app_context():
            order_item = OrderItem(
                order_id=sample_order.id,
                part_id=sample_part.id,
                quantity=1,
                unit_price=10.00
            )
            db.session.add(order_item)
            db.session.commit()
            
            order_item_id = order_item.id
            
            # Delete the order
            db.session.delete(sample_order)
            db.session.commit()
            
            # Order item should be deleted due to cascade
            deleted_item = OrderItem.query.get(order_item_id)
            assert deleted_item is None


class TestRegistrationLinkModel:
    
    @pytest.mark.models
    def test_registration_link_creation(self, app, admin_user):
        with app.app_context():
            link = RegistrationLink(
                custom_path='test-link',
                max_uses=10,
                default_permission='readonly',
                auto_enable_new_users=True,
                created_by_user_id=admin_user.id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(link)
            db.session.commit()
            
            assert link.id is not None
            assert link.custom_path == 'test-link'
            assert link.max_uses == 10
            assert link.current_uses == 0
            assert link.default_permission == 'readonly'
            assert link.auto_enable_new_users is True
            assert link.is_active is True

    @pytest.mark.models
    def test_registration_link_validation(self, app, admin_user):
        with app.app_context():
            # Valid link
            valid_link = RegistrationLink(
                max_uses=5,
                created_by_user_id=admin_user.id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(valid_link)
            db.session.commit()
            
            is_valid, message = valid_link.is_currently_valid_for_registration()
            assert is_valid is True
            assert "valid" in message.lower()

    @pytest.mark.models
    def test_registration_link_expired(self, app, admin_user):
        with app.app_context():
            expired_link = RegistrationLink(
                max_uses=5,
                created_by_user_id=admin_user.id,
                expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
            )
            db.session.add(expired_link)
            db.session.commit()
            
            is_valid, message = expired_link.is_currently_valid_for_registration()
            assert is_valid is False
            assert "expired" in message.lower()

    @pytest.mark.models
    def test_registration_link_max_uses_reached(self, app, admin_user):
        with app.app_context():
            link = RegistrationLink(
                max_uses=2,
                current_uses=2,  # Already at max
                created_by_user_id=admin_user.id
            )
            db.session.add(link)
            db.session.commit()
            
            is_valid, message = link.is_currently_valid_for_registration()
            assert is_valid is False
            assert "maximum" in message.lower()

    @pytest.mark.models
    def test_registration_link_effective_path(self, app, admin_user):
        with app.app_context():
            # Link with custom path
            link_with_path = RegistrationLink(
                custom_path='custom-link',
                created_by_user_id=admin_user.id
            )
            db.session.add(link_with_path)
            db.session.commit()
            
            assert link_with_path.effective_link_path_segment == 'custom-link'
            
            # Link without custom path (uses token)
            link_without_path = RegistrationLink(
                created_by_user_id=admin_user.id
            )
            db.session.add(link_without_path)
            db.session.commit()
            
            assert link_without_path.effective_link_path_segment == link_without_path.token

    @pytest.mark.models
    def test_registration_link_to_dict(self, app, admin_user):
        with app.app_context():
            link = RegistrationLink(
                custom_path='test-link',
                max_uses=5,
                default_permission='editor',
                created_by_user_id=admin_user.id
            )
            db.session.add(link)
            db.session.commit()
            
            link_dict = link.to_dict()
            assert link_dict['custom_path'] == 'test-link'
            assert link_dict['max_uses'] == 5
            assert link_dict['current_uses'] == 0
            assert link_dict['default_permission'] == 'editor'
            assert link_dict['creator_username'] == admin_user.username
            assert 'is_currently_valid' in link_dict
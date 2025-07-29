import pytest
import tempfile
import os
from app import create_app, db
from app.models import User, Project, Part, Machine, PostProcess, Order, OrderItem, RegistrationLink
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'JWT_SECRET_KEY': 'test-secret-key',
        'AIRTABLE_API_KEY': 'test-airtable-key',
        'AIRTABLE_BASE_ID': 'test-base-id',
        'AIRTABLE_TABLE_ID': 'test-table-id',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture 
def admin_user(app):
    with app.app_context():
        user = User(
            username='admin',
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            permission='admin',
            enabled=True,
            is_approved=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def editor_user(app):
    with app.app_context():
        user = User(
            username='editor',
            email='editor@test.com',
            first_name='Editor',
            last_name='User',
            permission='editor',
            enabled=True,
            is_approved=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def readonly_user(app):
    with app.app_context():
        user = User(
            username='readonly',
            email='readonly@test.com',
            first_name='Read',
            last_name='Only',
            permission='readonly',
            enabled=True,
            is_approved=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def disabled_user(app):
    with app.app_context():
        user = User(
            username='disabled',
            email='disabled@test.com',
            first_name='Disabled',
            last_name='User',
            permission='readonly',
            enabled=False,
            is_approved=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def unapproved_user(app):
    with app.app_context():
        user = User(
            username='unapproved',
            email='unapproved@test.com',
            first_name='Unapproved',
            last_name='User',
            permission='readonly',
            enabled=True,
            is_approved=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_token(app, admin_user):
    with app.app_context():
        return create_access_token(identity=admin_user.id)


@pytest.fixture
def editor_token(app, editor_user):
    with app.app_context():
        return create_access_token(identity=editor_user.id)


@pytest.fixture
def readonly_token(app, readonly_user):
    with app.app_context():
        return create_access_token(identity=readonly_user.id)


@pytest.fixture
def sample_project(app):
    with app.app_context():
        project = Project(
            name='Test Project',
            prefix='TP',
            description='A test project for testing'
        )
        db.session.add(project)
        db.session.commit()
        return project


@pytest.fixture
def sample_machine(app):
    with app.app_context():
        machine = Machine(
            name='Test Machine',
            is_active=True
        )
        db.session.add(machine)
        db.session.commit()
        return machine


@pytest.fixture
def sample_post_process(app):
    with app.app_context():
        post_process = PostProcess(
            name='Test Post Process',
            description='A test post process',
            is_active=True
        )
        db.session.add(post_process)
        db.session.commit()
        return post_process


@pytest.fixture
def sample_assembly(app, sample_project):
    with app.app_context():
        assembly = Part(
            name='Test Assembly',
            part_number='TP-A-0001',
            numeric_id=1,
            description='A test assembly',
            type='assembly',
            project_id=sample_project.id,
            status='in design',
            quantity=1
        )
        db.session.add(assembly)
        db.session.commit()
        return assembly


@pytest.fixture
def sample_part(app, sample_project, sample_machine, sample_post_process, sample_assembly):
    with app.app_context():
        part = Part(
            name='Test Part',
            part_number='TP-P-0002',
            numeric_id=2,
            description='A test part',
            type='part',
            project_id=sample_project.id,
            parent_id=sample_assembly.id,
            machine_id=sample_machine.id,
            status='in design',
            quantity=5,
            raw_material='Steel'
        )
        part.post_processes.append(sample_post_process)
        db.session.add(part)
        db.session.commit()
        return part


@pytest.fixture
def sample_order(app, sample_project):
    with app.app_context():
        order = Order(
            order_number='ORD-001',
            customer_name='Test Customer',
            project_id=sample_project.id,
            status='Pending',
            total_amount=100.00
        )
        db.session.add(order)
        db.session.commit()
        return order


@pytest.fixture
def sample_order_item(app, sample_order, sample_part):
    with app.app_context():
        order_item = OrderItem(
            order_id=sample_order.id,
            part_id=sample_part.id,
            quantity=2,
            unit_price=25.00
        )
        db.session.add(order_item)
        db.session.commit()
        return order_item


@pytest.fixture
def sample_registration_link(app, admin_user):
    with app.app_context():
        link = RegistrationLink(
            custom_path='test-link',
            max_uses=5,
            default_permission='readonly',
            auto_enable_new_users=True,
            created_by_user_id=admin_user.id,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(link)
        db.session.commit()
        return link


def get_auth_headers(token):
    return {'Authorization': f'Bearer {token}'}
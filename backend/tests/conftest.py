"""Test configuration and utilities for the BroncoPartsV2 backend."""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import User, Project, Part, Machine, PostProcess, Order, OrderItem, RegistrationLink


class TestConfig:
    """Test configuration class."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-secret-key'
    # Mock Airtable configuration
    AIRTABLE_API_KEY = 'test-airtable-key'
    AIRTABLE_BASE_ID = 'test-base-id'
    AIRTABLE_TABLE_ID = 'test-table-id'


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Patch Airtable service to prevent real API calls
    with patch('app.services.airtable_service.Table') as mock_table:
        mock_table.return_value = MagicMock()

        # Set test environment variables
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
        os.environ['AIRTABLE_API_KEY'] = 'test-airtable-key'
        os.environ['AIRTABLE_BASE_ID'] = 'test-base-id'
        os.environ['AIRTABLE_TABLE_ID'] = 'test-table-id'

        app = create_app()
        app.config.from_object(TestConfig)

        # Create application context
        ctx = app.app_context()
        ctx.push()

        yield app

        ctx.pop()


@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for each test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def mock_airtable():
    """Mock Airtable service to prevent real API calls during tests."""
    with patch('app.services.airtable_service.Table') as mock_table, \
         patch('app.services.airtable_service._update_airtable_field_choices') as mock_update, \
         patch('app.services.airtable_service.sync_part_to_airtable') as mock_sync:

        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.create.return_value = {'id': 'test-airtable-id'}
        mock_table_instance.update.return_value = {'id': 'test-airtable-id'}
        mock_update.return_value = True
        mock_sync.return_value = True

        yield {
            'table': mock_table,
            'update_choices': mock_update,
            'sync_part': mock_sync,
            'table_instance': mock_table_instance
        }


class TestFixtures:
    """Test data fixtures and helper methods."""

    @staticmethod
    def create_part(project_id=None, name="Test Part", creator_id=None, **kwargs):
        """Create a part for tests (matching test expectations)."""
        from app import db
        db_session = db.session

        # If project_id is provided, use it
        if project_id is not None:
            project = Project.query.get(project_id)
            if project is None:
                raise ValueError(f"Project with ID {project_id} not found")
        else:
            # Create a default project if none provided
            project = TestFixtures.create_test_project(db_session)

        # Generate part number based on name if not provided
        part_number = kwargs.get('part_number', f"TP-{name.replace(' ', '-').upper()}-001")

        # Get next numeric ID for this project to avoid unique constraint violation
        from sqlalchemy import func
        max_numeric_id = db_session.query(func.max(Part.numeric_id)).filter_by(project_id=project.id).scalar()
        next_numeric_id = (max_numeric_id or 0) + 1

        # Create part with only valid fields
        part_data = {
            'part_number': part_number,
            'name': name,
            'description': kwargs.get('description', f"A test part for {name}"),
            'raw_material': kwargs.get('raw_material', 'Steel'),
            'project_id': project.id,
            'quantity': kwargs.get('quantity', 1),
            'status': kwargs.get('status', kwargs.get('part_status', 'in design')),  # Use status, fallback to part_status, then default
            'machine_id': kwargs.get('machine_id'),
            'type': kwargs.get('type', 'part'),
            'numeric_id': kwargs.get('numeric_id', next_numeric_id)  # Use next available numeric_id if not provided
        }

        # Remove None values to avoid SQLAlchemy errors
        part_data = {k: v for k, v in part_data.items() if v is not None}

        part = Part(**part_data)
        db_session.add(part)
        db_session.commit()
        return part

    @staticmethod
    def create_machine(name="Test Machine", **kwargs):
        """Create a machine for tests (matching test expectations)."""
        from app import db
        import random
        db_session = db.session

        # Check if machine with this name already exists
        existing_machine = Machine.query.filter_by(name=name).first()
        if existing_machine:
            # If it exists, either return it or create with a unique name
            if kwargs.get('return_existing', True):
                return existing_machine
            else:
                # Add random suffix to make name unique
                name = f"{name}-{random.randint(1000, 9999)}"

        machine = Machine(
            name=name
        )
        db_session.add(machine)
        db_session.commit()
        return machine

    @staticmethod
    def create_post_process(name="Test Post Process", **kwargs):
        """Create a post process for tests (matching test expectations)."""
        from app import db
        db_session = db.session

        post_process = PostProcess(
            name=name
        )
        db_session.add(post_process)
        db_session.commit()
        return post_process

    @staticmethod
    def create_order(project_id=None, created_by_id=None, **kwargs):
        """Create an order for tests (matching test expectations)."""
        from app import db
        import random
        db_session = db.session

        # If project_id is provided, use it
        if project_id is not None:
            project = Project.query.get(project_id)
            if project is None:
                raise ValueError(f"Project with ID {project_id} not found")

        # Generate a random order number if not provided
        order_number = kwargs.get('order_number', f"ORDER-{random.randint(1000, 9999)}")

        order = Order(
            order_number=order_number,
            customer_name=kwargs.get('customer_name', "Test Customer"),
            project_id=project_id,
            status=kwargs.get('status', "Pending"),
            total_amount=kwargs.get('total_amount', 100.00),
            reimbursed=kwargs.get('reimbursed', False)
        )
        db_session.add(order)
        db_session.commit()
        return order

    @staticmethod
    def create_order_item(order_id=None, part_id=None, **kwargs):
        """Create an order item for tests (matching test expectations)."""
        from app import db
        from decimal import Decimal
        db_session = db.session

        # Validate order_id and part_id
        if order_id is None:
            raise ValueError("order_id is required")
        if part_id is None:
            raise ValueError("part_id is required")

        order = Order.query.get(order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")

        part = Part.query.get(part_id)
        if not part:
            raise ValueError(f"Part with ID {part_id} not found")

        # Create order item
        order_item = OrderItem(
            order_id=order_id,
            part_id=part_id,
            quantity=kwargs.get('quantity', 1),
            unit_price=Decimal(str(kwargs.get('unit_price', 10.00)))
        )
        db_session.add(order_item)

        # Update order total_amount
        if 'update_total' not in kwargs or kwargs['update_total']:
            order.total_amount += order_item.unit_price * order_item.quantity

        db_session.commit()
        return order_item

    @staticmethod
    def create_test_admin_user(db_session):
        """Create a test admin user."""
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email='admin@test.com').first()
        if existing_admin:
            return existing_admin

        admin = User(
            username='admin',
            email='admin@test.com',
            first_name='Admin',
            last_name='User',
            permission='admin',
            enabled=True,
            is_approved=True
        )
        admin.set_password('password123')
        db_session.add(admin)
        db_session.commit()
        return admin

    @staticmethod
    def create_test_editor_user(db_session):
        """Create a test editor user."""
        # Check if editor user already exists
        existing_editor = User.query.filter_by(email='editor@test.com').first()
        if existing_editor:
            return existing_editor

        editor = User(
            username='editor',
            email='editor@test.com',
            first_name='Editor',
            last_name='User',
            permission='editor',
            enabled=True,
            is_approved=True
        )
        editor.set_password('password123')
        db_session.add(editor)
        db_session.commit()
        return editor

    @staticmethod
    def create_test_readonly_user(db_session):
        """Create a test readonly user."""
        # Check if readonly user already exists
        existing_readonly = User.query.filter_by(email='readonly@test.com').first()
        if existing_readonly:
            return existing_readonly

        readonly = User(
            username='readonly',
            email='readonly@test.com',
            first_name='Readonly',
            last_name='User',
            permission='readonly',
            enabled=True,
            is_approved=True
        )
        readonly.set_password('password123')
        db_session.add(readonly)
        db_session.commit()
        return readonly

    @staticmethod
    def create_test_disabled_user(db_session):
        """Create a test disabled user."""
        # Check if disabled user already exists
        existing_disabled = User.query.filter_by(email='disabled@test.com').first()
        if existing_disabled:
            return existing_disabled

        disabled = User(
            username='disabled',
            email='disabled@test.com',
            first_name='Disabled',
            last_name='User',
            permission='readonly',
            enabled=False,
            is_approved=True
        )
        disabled.set_password('password123')
        db_session.add(disabled)
        db_session.commit()
        return disabled

    @staticmethod
    def create_test_unapproved_user(db_session):
        """Create a test unapproved user."""
        # Check if unapproved user already exists
        existing_unapproved = User.query.filter_by(email='unapproved@test.com').first()
        if existing_unapproved:
            return existing_unapproved

        unapproved = User(
            username='unapproved',
            email='unapproved@test.com',
            first_name='Unapproved',
            last_name='User',
            permission='readonly',
            enabled=True,
            is_approved=False
        )
        unapproved.set_password('password123')
        db_session.add(unapproved)
        db_session.commit()
        return unapproved

    @staticmethod
    def create_test_project(db_session, name="Test Project", prefix="TP"):
        """Create a test project."""
        project = Project(
            name=name,
            description="A test project",
            prefix=prefix,
            hide_dashboards=False
        )
        db_session.add(project)
        db_session.commit()
        return project

    @staticmethod
    def create_test_machine(db_session, name="Test Machine"):
        """Create a test machine."""
        machine = Machine(name=name)
        db_session.add(machine)
        db_session.commit()
        return machine

    @staticmethod
    def create_test_post_process(db_session, name="Test Post Process"):
        """Create a test post process."""
        post_process = PostProcess(name=name)
        db_session.add(post_process)
        db_session.commit()
        return post_process

    @staticmethod
    def create_test_part(db_session, project, name="Test Part", type="part", quantity=1):
        """Create a test part."""
        # Get next numeric ID for this project
        last_part = Part.query.filter_by(project_id=project.id).order_by(Part.numeric_id.desc()).first()
        next_numeric_id = (last_part.numeric_id + 1) if last_part else 100

        part = Part(
            name=name,
            description="A test part",
            type=type,
            project_id=project.id,
            numeric_id=next_numeric_id,
            part_number=f"{project.prefix}-{'A' if type == 'assembly' else 'P'}-{next_numeric_id:04d}",
            quantity=quantity,
            status="in design",
            priority=1
        )
        db_session.add(part)
        db_session.commit()
        return part

    @staticmethod
    def create_test_order(db_session, project, order_number="TEST-001"):
        """Create a test order."""
        order = Order(
            order_number=order_number,
            customer_name="Test Customer",
            project_id=project.id,
            status="Pending",
            total_amount=100.00
        )
        db_session.add(order)
        db_session.commit()
        return order

    @staticmethod
    def create_test_registration_link(db_session, admin_user, custom_path="test-link"):
        """Create a test registration link."""
        reg_link = RegistrationLink(
            custom_path=custom_path,
            max_uses=1,
            default_permission='readonly',
            auto_enable_new_users=True,
            created_by_user_id=admin_user.id
        )
        db_session.add(reg_link)
        db_session.commit()
        return reg_link

    @staticmethod
    def create_project(db_session=None, project_id=None, name="Test Project", creator_id=None, **kwargs):
        """Create a project for workflow tests (matching test expectations)."""
        from app import db
        if db_session is None:
            db_session = db.session

        # Extract prefix from project_id (e.g., "PROJ001" -> "PROJ")
        prefix = kwargs.get('prefix', project_id[:4] if project_id else "TEST")

        project = Project(
            name=name,
            description=kwargs.get('description', f"A test project created for {name}"),
            prefix=prefix,
            hide_dashboards=kwargs.get('hide_dashboards', False)
        )
        db_session.add(project)
        db_session.commit()
        return project

    @staticmethod
    def create_user(db_session=None, email="test@test.com", first_name="Test", last_name="User", role="readonly", **kwargs):
        """Create a user for workflow tests."""
        from app import db
        if db_session is None:
            db_session = db.session

        # Map role to permission
        permission_map = {
            'admin': 'admin',
            'editor': 'editor',
            'readonly': 'readonly'
        }
        permission = permission_map.get(role, 'readonly')

        user = User(
            username=email.split('@')[0],
            email=email,
            first_name=first_name,
            last_name=last_name,
            permission=permission,
            enabled=True,
            is_approved=True
        )
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        return user

    @staticmethod
    def get_auth_headers(user, client=None):
        """Get authentication headers for a user."""
        if client is None:
            # Return headers that can be used with requests
            return {'Authorization': f'Bearer mock-token-{user.id}'}

        # Use actual login if client is provided
        login_response = client.post('/api/login', json={
            'email': user.email,
            'password': 'password123'
        })

        if login_response.status_code == 200:
            token = login_response.get_json()['access_token']
            return {'Authorization': f'Bearer {token}'}
        else:
            raise Exception(f"Login failed: {login_response.get_json()}")


def get_auth_headers(client, email, password):
    """Helper function to get authentication headers for API requests."""
    login_response = client.post('/api/login', json={
        'email': email,
        'password': password
    })

    if login_response.status_code == 200:
        token = login_response.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        raise Exception(f"Login failed: {login_response.get_json()}")


def assert_error_response(response, expected_status, expected_message=None):
    """Helper function to assert error responses."""
    assert response.status_code == expected_status
    data = response.get_json()
    if expected_message:
        assert expected_message in data.get('message', '')


def assert_success_response(response, expected_status=200):
    """Helper function to assert successful responses."""
    assert response.status_code == expected_status
    return response.get_json()


@pytest.fixture
def test_users(db_session):
    """Create all test users once and reuse across tests that need them."""
    # Create users only once per test function
    admin = TestFixtures.create_test_admin_user(db_session)
    editor = TestFixtures.create_test_editor_user(db_session)
    readonly = TestFixtures.create_test_readonly_user(db_session)
    disabled = TestFixtures.create_test_disabled_user(db_session)
    unapproved = TestFixtures.create_test_unapproved_user(db_session)

    return {
        'admin': admin,
        'editor': editor,
        'readonly': readonly,
        'disabled': disabled,
        'unapproved': unapproved
    }


@pytest.fixture
def auth_headers(client, test_users):
    """Create authentication headers for different user types."""
    try:
        admin_headers = get_auth_headers(client, 'admin@test.com', 'password123')
    except:
        admin_headers = {}

    try:
        editor_headers = get_auth_headers(client, 'editor@test.com', 'password123')
    except:
        editor_headers = {}

    try:
        readonly_headers = get_auth_headers(client, 'readonly@test.com', 'password123')
    except:
        readonly_headers = {}

    return {
        'admin': admin_headers,
        'editor': editor_headers,
        'readonly': readonly_headers,
        'disabled': {},  # Cannot login - account disabled
        'unapproved': {}  # Cannot login - account not approved
    }


@pytest.fixture
def test_fixtures(test_users, db_session, mock_airtable):
    """Create comprehensive test data fixtures."""
    # Use existing users from test_users fixture
    admin = test_users['admin']
    editor = test_users['editor']
    readonly = test_users['readonly']

    # Create projects
    project1 = TestFixtures.create_test_project(db_session, "Test Project", "TP")
    project2 = TestFixtures.create_test_project(db_session, "Alpha Project", "AP")

    # Create machines and post-processes
    machine1 = TestFixtures.create_test_machine(db_session, "Test Machine")
    machine2 = TestFixtures.create_test_machine(db_session, "CNC Mill")
    post_process1 = TestFixtures.create_test_post_process(db_session, "Test Post Process")
    post_process2 = TestFixtures.create_test_post_process(db_session, "Anodizing")

    # Create parts
    part1 = TestFixtures.create_test_part(db_session, project1, "Test Part", "part", 1)
    part2 = TestFixtures.create_test_part(db_session, project1, "Motor Mount", "part", 2)
    assembly1 = TestFixtures.create_test_part(db_session, project1, "Motor Assembly", "assembly", 1)

    # Create orders
    order1 = TestFixtures.create_test_order(db_session, project1, "ORDER-001")

    # Create registration link
    reg_link = TestFixtures.create_test_registration_link(db_session, admin, "test-registration")

    # Add methods to TestFixtures class
    @staticmethod
    def create_part(db_session=None, project_id=None, name="Test Part", creator_id=None, **kwargs):
        """Create a part for tests (matching test expectations)."""
        from app import db
        if db_session is None:
            db_session = db.session

        # If project_id is provided, use it
        if project_id is not None:
            project = Project.query.get(project_id)
            if project is None:
                raise ValueError(f"Project with ID {project_id} not found")
        else:
            # Create a default project if none provided
            project = TestFixtures.create_test_project(db_session)

        # Generate part number based on name if not provided
        part_number = kwargs.get('part_number', f"TP-{name.replace(' ', '-').upper()}-001")

        part = Part(
            part_number=part_number,
            name=name,
            description=kwargs.get('description', f"A test part for {name}"),
            raw_material=kwargs.get('raw_material', 'Steel'),
            project_id=project.id,
            creator_id=creator_id,
            quantity=kwargs.get('quantity', 1),
            part_status=kwargs.get('part_status', 'design'),
            machine_id=kwargs.get('machine_id'),
            type=kwargs.get('type', 'part')
        )
        db_session.add(part)
        db_session.commit()
        return part

    @staticmethod
    def create_machine(db_session=None, name="Test Machine", **kwargs):
        """Create a machine for tests (matching test expectations)."""
        from app import db
        if db_session is None:
            db_session = db.session

        machine = Machine(
            name=name
        )
        db_session.add(machine)
        db_session.commit()
        return machine

    @staticmethod
    def create_post_process(db_session=None, name="Test Post Process", **kwargs):
        """Create a post process for tests (matching test expectations)."""
        from app import db
        if db_session is None:
            db_session = db.session

        post_process = PostProcess(
            name=name
        )
        db_session.add(post_process)
        db_session.commit()
        return post_process

    # Store the created fixtures as attributes on the TestFixtures class for access
    TestFixtures._test_data = {
        'users': {
            'admin': admin,
            'editor': editor,
            'readonly': readonly
        },
        'projects': {
            'project1': project1,
            'project2': project2
        },
        'machines': {
            'machine1': machine1,
            'machine2': machine2
        },
        'post_processes': {
            'post_process1': post_process1,
            'post_process2': post_process2
        },
        'parts': {
            'part1': part1,
            'part2': part2,
            'assembly1': assembly1
        },
        'orders': {
            'order1': order1
        },
        'registration_links': {
            'reg_link': reg_link
        }
    }

    # Add methods to TestFixtures class
    TestFixtures.create_part = TestFixtures.create_part
    TestFixtures.create_machine = TestFixtures.create_machine
    TestFixtures.create_post_process = TestFixtures.create_post_process

    return TestFixtures

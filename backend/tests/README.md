# Test Suite Documentation

This directory contains a comprehensive test suite for the Bronco Parts backend Flask application.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_models.py         # Database model tests
│   └── test_decorators.py     # Authentication decorator tests
├── integration/                # Integration tests (require database)
│   ├── __init__.py
│   ├── test_auth_api.py       # Authentication endpoints
│   ├── test_user_api.py       # User management endpoints
│   ├── test_project_api.py    # Project management endpoints
│   ├── test_part_api.py       # Parts management endpoints
│   ├── test_order_api.py      # Order management endpoints
│   ├── test_registration_link_api.py  # Registration link endpoints
│   ├── test_machine_postprocess_api.py  # Machine/PostProcess endpoints
│   ├── test_statistics_api.py # Statistics and dashboard endpoints
│   ├── test_workflows.py      # End-to-end workflow tests
│   └── test_error_handling.py # Error handling and edge cases
└── fixtures/                   # Test data and utilities
    └── __init__.py
```

## Test Categories

### Unit Tests
- **Models**: Test database models, relationships, and validations
- **Decorators**: Test authentication and authorization decorators
- Fast execution, no external dependencies

### Integration Tests
- **API Endpoints**: Test all REST API endpoints
- **Authentication**: Login, registration, token handling
- **CRUD Operations**: Create, read, update, delete operations
- **Role-based Access**: Test permissions for admin, editor, readonly roles
- **Business Logic**: Complex workflows and data relationships

### Workflow Tests
- **End-to-End**: Complete user journeys from registration to ordering
- **Collaboration**: Multi-user workflows
- **Project Lifecycle**: Full project from creation to completion
- **Error Recovery**: Testing error conditions and recovery

## Running Tests

### Prerequisites

1. Install testing dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:
```

### Basic Usage

Run all tests:
```bash
python run_tests.py
```

Run with coverage:
```bash
python run_tests.py --coverage
```

Generate HTML coverage report:
```bash
python run_tests.py --html
```

### Specific Test Types

Run only unit tests:
```bash
python run_tests.py --unit
```

Run only integration tests:
```bash
python run_tests.py --integration
```

Run fast tests (no coverage):
```bash
python run_tests.py --fast
```

### Advanced Usage

Run specific test file:
```bash
python run_tests.py --file tests/unit/test_models.py
```

Run tests matching pattern:
```bash
python run_tests.py --pattern "test_user"
```

Verbose output:
```bash
python run_tests.py --verbose
```

### Direct pytest Usage

You can also run pytest directly:

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Specific test file
pytest tests/unit/test_models.py

# With coverage
pytest --cov=app --cov-report=html

# Verbose mode
pytest -v

# Run tests matching pattern
pytest -k "test_user_creation"
```

## Test Configuration

### pytest.ini
- Test discovery settings
- Coverage configuration
- Test markers
- Warning filters

### .coveragerc
- Coverage reporting configuration
- Files to include/exclude
- Output formats

### conftest.py
- Test fixtures and utilities
- Database setup for testing
- Authentication helpers
- Mock configurations

## Test Fixtures

The test suite includes comprehensive fixtures for creating test data:

- **Users**: Different roles (admin, editor, readonly)
- **Projects**: Test projects with various configurations
- **Parts**: Parts with relationships and hierarchy
- **Orders**: Orders and order items
- **Machines/PostProcesses**: Lookup data
- **Registration Links**: Invitation links

## Mocking

### Airtable Integration
The test suite mocks the Airtable service to prevent real API calls during testing. This ensures:
- Tests run in isolation
- No dependency on external services
- Faster test execution
- Predictable test results

### Database
Tests use SQLite in-memory database for:
- Fast test execution
- Isolated test environment
- No persistent data between tests
- Easy cleanup

## Best Practices

### Writing Tests
1. Use descriptive test names that explain what is being tested
2. Follow the Arrange-Act-Assert pattern
3. Test both success and failure scenarios
4. Use appropriate test markers
5. Keep tests independent and isolated

### Test Data
1. Use fixtures for creating test data
2. Create minimal data needed for each test
3. Clean up after each test (handled automatically)
4. Use factories for complex data creation

### Authentication
1. Use auth_headers fixtures for authenticated requests
2. Test different permission levels
3. Verify authorization is enforced
4. Test token handling and expiration

## Coverage Goals

The test suite aims for:
- **Overall coverage**: >80%
- **Critical paths**: >95%
- **API endpoints**: 100%
- **Models**: 100%
- **Business logic**: >90%

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
python run_tests.py --coverage

# Check coverage threshold (configured in pytest.ini)
pytest --cov=app --cov-fail-under=80
```

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure test database is properly configured
2. **Import errors**: Check PYTHONPATH and module imports
3. **Fixture errors**: Verify fixture dependencies and scope
4. **Permission errors**: Check file permissions on test files

### Debug Mode

Run tests with debug output:
```bash
pytest -v -s --tb=long
```

### Test Database Issues

If database tests fail, try:
```bash
# Clear any existing test database
rm -f test.db

# Reset database migrations (if applicable)
flask db upgrade
```

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate test markers
3. Update this documentation if needed
4. Ensure tests pass in isolation
5. Maintain or improve coverage

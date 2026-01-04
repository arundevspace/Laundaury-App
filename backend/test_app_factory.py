"""
Test suite for Flask app factory (INFRA-1)
Tests the acceptance criteria:
- App starts without error
- All blueprints registered
- /health returns 200
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app


class TestAppFactory:
    """Test Flask app factory initialization"""
    
    def test_app_creation_without_error(self):
        """Test that the app can be created without errors"""
        app = create_app()
        assert app is not None
        assert app.name == 'app.app'
    
    def test_app_config_loaded(self):
        """Test that configuration is loaded correctly"""
        app = create_app()
        # Check that essential config values are set
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
        assert 'SECRET_KEY' in app.config
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] is False
    
    def test_database_initialized(self):
        """Test that database is initialized"""
        app = create_app()
        # Check that db is available in extensions
        assert 'sqlalchemy' in app.extensions
    
    def test_blueprints_registered(self):
        """Test that all blueprints are registered"""
        app = create_app()
        
        # Get all registered blueprints
        registered_blueprints = list(app.blueprints.keys())
        
        # Check that expected blueprints are registered
        assert 'user' in registered_blueprints, "user blueprint should be registered"
        assert 'order' in registered_blueprints, "order blueprint should be registered"
    
    def test_blueprint_url_prefixes(self):
        """Test that blueprints have correct URL prefixes"""
        app = create_app()
        
        # Check URL rules to verify prefixes
        rules = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}
        
        # Verify user blueprint routes
        assert any('/user/' in rule for rule in rules.keys()), "user routes should have /user prefix"
        
        # Verify order blueprint routes
        assert any('/orders/' in rule for rule in rules.keys()), "order routes should have /orders prefix"
    
    def test_health_endpoint_exists(self):
        """Test that /health endpoint is registered"""
        app = create_app()
        
        # Check if /health route exists
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/health' in rules, "/health endpoint should be registered"
    
    def test_health_endpoint_returns_200(self):
        """Test that /health endpoint returns 200 status"""
        app = create_app()
        client = app.test_client()
        
        # Make request to /health endpoint
        response = client.get('/health')
        
        # Verify response
        assert response.status_code == 200, "/health endpoint should return 200"
        assert response.json == {'status': 'OK'}, "/health should return correct JSON"
    
    def test_health_endpoint_methods(self):
        """Test that /health endpoint only accepts GET"""
        app = create_app()
        client = app.test_client()
        
        # GET should work
        response = client.get('/health')
        assert response.status_code == 200
        
        # POST should not be allowed
        response = client.post('/health')
        assert response.status_code == 405  # Method Not Allowed


def run_tests():
    """Run all tests and print results"""
    print("=" * 70)
    print("Flask App Factory Verification Tests (INFRA-1)")
    print("=" * 70)
    
    test_instance = TestAppFactory()
    tests = [
        ('App Creation', test_instance.test_app_creation_without_error),
        ('Config Loaded', test_instance.test_app_config_loaded),
        ('Database Initialized', test_instance.test_database_initialized),
        ('Blueprints Registered', test_instance.test_blueprints_registered),
        ('Blueprint URL Prefixes', test_instance.test_blueprint_url_prefixes),
        ('Health Endpoint Exists', test_instance.test_health_endpoint_exists),
        ('Health Endpoint Returns 200', test_instance.test_health_endpoint_returns_200),
        ('Health Endpoint Methods', test_instance.test_health_endpoint_methods),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}: PASSED")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name}: ERROR - {e}")
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)
    
    if failed == 0:
        print("\n✓ All acceptance criteria met!")
        print("  - App starts without error")
        print("  - All blueprints registered")
        print("  - /health returns 200")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

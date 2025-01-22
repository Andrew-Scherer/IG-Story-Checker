"""
Tests for API route registration
"""

def test_api_routes(client):
    """Test that all API routes are registered with correct prefixes"""
    
    # Get all registered routes
    routes = [str(rule) for rule in client.application.url_map.iter_rules()]
    
    # Required API routes
    required_routes = [
        '/api/niches',
        '/api/niches/<niche_id>',
        '/api/profiles',
        '/api/profiles/<profile_id>',
        '/api/batches',
        '/api/settings',
        '/api/proxies'
    ]
    
    # Verify each required route exists
    for route in required_routes:
        assert any(route in r for r in routes), f"Missing {route} route"

def test_api_endpoints(client, create_niche, create_profile):
    """Test that API endpoints return correct status codes"""
    
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile("testuser", niche_id=niche.id)
    
    # Test GET endpoints return 200
    assert client.get('/api/niches').status_code == 200
    assert client.get('/api/profiles').status_code == 200
    assert client.get('/api/batches').status_code == 200
    assert client.get('/api/settings').status_code == 200
    assert client.get('/api/proxies').status_code == 200
    
    # Test POST endpoints require data
    headers = {'Content-Type': 'application/json'}
    assert client.post('/api/niches', json={}, headers=headers).status_code == 400
    assert client.post('/api/profiles', json={}, headers=headers).status_code == 400
    
    # Test GET single resource
    assert client.get(f'/api/niches/{niche.id}').status_code == 200
    assert client.get(f'/api/profiles/{profile.id}').status_code == 200

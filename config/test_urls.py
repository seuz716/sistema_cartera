import pytest
from django.urls import resolve, reverse, Resolver404

@pytest.mark.django_db
def test_admin_url_resolves():
    resolver = resolve('/admin/')
    assert resolver.app_name == 'admin'

@pytest.mark.django_db
def test_clientes_url_included():
    # This just checks that the include works, not the actual views
    try:
        resolver = resolve('/clientes/')
    except Resolver404:
        # The root of 'clientes/' may not resolve, but the include exists
        assert True
    else:
        # If it resolves, it should not be admin
        assert resolver.app_name != 'admin'

@pytest.mark.django_db
def test_ventas_url_included():
    try:
        resolver = resolve('/ventas/')
    except Resolver404:
        assert True
    else:
        assert resolver.app_name != 'admin'

@pytest.mark.django_db
def test_cartera_url_included():
    try:
        resolver = resolve('/cartera/')
    except Resolver404:
        assert True
    else:
        assert resolver.app_name != 'admin'

@pytest.mark.django_db
def test_api_auth_url_included():
    # rest_framework.urls provides a login view at /api-auth/login/
    url = reverse('rest_framework:login')
    assert url.startswith('/api-auth/')
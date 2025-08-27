"""
Custom test runner configuration for TripAI project.

This module provides utilities to run different types of tests:
- Unit tests: Fast, isolated tests for individual components
- Integration tests: Tests for component interactions
- Functional tests: End-to-end user workflow tests
"""

import os
import sys
import pytest
import unittest
from django.test.runner import DiscoverRunner
from django.conf import settings


class CustomTestRunner(DiscoverRunner):
    """
    Custom Django test runner that supports different test categories
    and integrates with pytest for DRF API testing.
    """
    
    def setup_test_environment(self, **kwargs):
        """Set up test environment with proper configurations."""
        super().setup_test_environment(**kwargs)
        # Disable caching during tests
        settings.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        }
        # Use in-memory database for faster tests
        settings.DATABASES['default']['NAME'] = ':memory:'
        
    def run_tests(self, test_labels, **kwargs):
        """Run tests with proper categorization."""
        if not test_labels:
            test_labels = ['tests']
            
        # Run Django tests first
        django_result = super().run_tests(test_labels, **kwargs)
        
        # Run pytest for DRF API tests
        pytest_args = [
            'tests/',
            '-v',
            '--tb=short',
            '--cov=home',
            '--cov-report=term-missing'
        ]
        
        pytest_result = pytest.main(pytest_args)
        
        return django_result + (1 if pytest_result != 0 else 0)


def run_unit_tests():
    """Run only unit tests."""
    return pytest.main([
        'tests/unit/',
        '-v',
        '--tb=short'
    ])


def run_integration_tests():
    """Run only integration tests."""
    return pytest.main([
        'tests/integration/',
        '-v',
        '--tb=short'
    ])


def run_functional_tests():
    """Run only functional tests."""
    return pytest.main([
        'tests/functional/',
        '-v',
        '--tb=short',
        '--disable-warnings'
    ])


def run_api_tests():
    """Run DRF API-specific tests."""
    return pytest.main([
        'tests/',
        '-v',
        '-k', 'api',
        '--tb=short'
    ])


if __name__ == '__main__':
    # Allow running specific test categories from command line
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    test_runners = {
        'unit': run_unit_tests,
        'integration': run_integration_tests,
        'functional': run_functional_tests,
        'api': run_api_tests,
    }
    
    if test_type in test_runners:
        exit_code = test_runners[test_type]()
        sys.exit(exit_code)
    else:
        print("Available test types: unit, integration, functional, api")
        sys.exit(1)

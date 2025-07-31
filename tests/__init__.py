"""
Test Suite for Manga Descriptor Development

This package contains all testing modules for the refactored manga description
generation system. Tests verify the integration between refactored components
and validate the functionality of individual modules.

Test modules:
    test_basic_functions: Tests basic utilities (content detection, title processing)
    test_integration: Tests component integration (future)
    test_workflow: Tests complete workflow functionality (future)
"""

import sys
import os

# Add refactor modules to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'refactor'))
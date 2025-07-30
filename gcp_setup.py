"""
Google Cloud Platform Setup Module

This module handles Google Cloud authentication, Vertex AI initialization,
and other infrastructure setup tasks for the manga description system.

Functions:
    setup_environment: Initialize GCP authentication and services
    initialize_vertex_ai: Setup Vertex AI with project configuration
    verify_dependencies: Check required dependencies and services
    setup_logging: Configure logging for the application
"""

import os
import logging
from typing import Tuple, Optional

# Google Cloud imports
try:
    import google.auth
    from google.auth.credentials import Credentials
    GCP_AUTH_AVAILABLE = True
except ImportError:
    GCP_AUTH_AVAILABLE = False

try:
    import vertexai
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


def setup_environment() -> bool:
    """
    Initialize Google Cloud authentication and basic environment setup.
    
    Returns:
        True if authentication successful, False otherwise
    """
    try:
        if not GCP_AUTH_AVAILABLE:
            print("❌ Google Cloud authentication libraries not available")
            print("Install with: pip install google-auth google-auth-oauthlib")
            return False
        
        # Initialize default credentials
        credentials, project_id = google.auth.default()
        print(f"✓ Authenticated with project: {project_id}")
        
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("Please run: gcloud auth application-default login")
        return False


def initialize_vertex_ai(project_id: str, location: str = "us-central1") -> bool:
    """
    Initialize Vertex AI with project configuration.
    
    Args:
        project_id: Google Cloud project ID
        location: GCP region for Vertex AI services
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        if not VERTEX_AI_AVAILABLE:
            print("❌ Vertex AI libraries not available")
            print("Install with: pip install google-cloud-aiplatform")
            return False
        
        vertexai.init(project=project_id, location=location)
        print(f"✓ Vertex AI initialized for project {project_id} in {location}")
        
        return True
    except Exception as e:
        print(f"❌ Vertex AI initialization failed: {e}")
        return False


def verify_dependencies() -> dict:
    """
    Check availability of required dependencies and services.
    
    Returns:
        Dictionary with dependency status
    """
    dependencies = {
        'google_auth': GCP_AUTH_AVAILABLE,
        'vertex_ai': VERTEX_AI_AVAILABLE,
        'google_cloud_storage': GCS_AVAILABLE,
    }
    
    # Check for optional dependencies
    try:
        import gcsfs
        dependencies['gcsfs'] = True
    except ImportError:
        dependencies['gcsfs'] = False
    
    try:
        from google import genai
        dependencies['google_genai'] = True
    except ImportError:
        dependencies['google_genai'] = False
    
    # Print status
    print("\\n=== Dependency Check ===")
    for dep, available in dependencies.items():
        status = "✓" if available else "❌"
        print(f"{status} {dep}: {'Available' if available else 'Not available'}")
    
    return dependencies


def setup_logging(
    level: str = "INFO", 
    format_string: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom log format string
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[]
    )
    
    logger = logging.getLogger('manga_descriptor')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    logger.info(f"Logging configured at {level} level")
    return logger


def check_gcp_project_access(project_id: str) -> bool:
    """
    Verify access to specific GCP project and services.
    
    Args:
        project_id: Google Cloud project ID to check
        
    Returns:
        True if project is accessible, False otherwise
    """
    try:
        if not GCS_AVAILABLE:
            print("❌ Google Cloud Storage client not available")
            return False
        
        # Try to access the project via Storage client
        storage_client = storage.Client(project=project_id)
        # This will raise an exception if we don't have access
        list(storage_client.list_buckets(max_results=1))
        
        print(f"✓ Project {project_id} is accessible")
        return True
    except Exception as e:
        print(f"❌ Cannot access project {project_id}: {e}")
        return False


def setup_full_environment(
    project_id: str, 
    location: str = "us-central1",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> dict:
    """
    Complete environment setup including auth, services, and logging.
    
    Args:
        project_id: Google Cloud project ID
        location: GCP region for services
        log_level: Logging level
        log_file: Optional log file path
        
    Returns:
        Dictionary with setup results
    """
    print("=== Starting Full Environment Setup ===")
    
    results = {
        'auth_success': False,
        'vertex_ai_success': False,
        'project_access': False,
        'dependencies': {},
        'logger': None
    }
    
    # Setup logging first
    try:
        logger = setup_logging(log_level, log_file=log_file)
        results['logger'] = logger
        logger.info("Environment setup started")
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
    
    # Check dependencies
    results['dependencies'] = verify_dependencies()
    
    # Setup authentication
    results['auth_success'] = setup_environment()
    
    # Initialize Vertex AI if auth succeeded
    if results['auth_success']:
        results['vertex_ai_success'] = initialize_vertex_ai(project_id, location)
        results['project_access'] = check_gcp_project_access(project_id)
    
    # Summary
    print("\\n=== Environment Setup Complete ===")
    all_good = (
        results['auth_success'] and 
        results['vertex_ai_success'] and 
        results['project_access']
    )
    
    if all_good:
        print("✅ All systems ready!")
    else:
        print("⚠️ Some setup issues detected. Check logs above.")
    
    return results
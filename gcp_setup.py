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
from typing import Tuple, Optional
from datetime import datetime

# Import centralized logging
from ..utils.logging import get_logger, log_gcp_operation, log_performance

# Load environment variables
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

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


def load_environment_config(env_file_path: str = None) -> dict:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file_path: Path to .env file (optional)
        
    Returns:
        Dictionary with configuration values
    """
    # Load .env file if available
    if DOTENV_AVAILABLE and env_file_path:
        load_dotenv(env_file_path)
    elif DOTENV_AVAILABLE:
        # Try to find .env file in common locations
        possible_paths = [
            '.env',
            '../.env',
            '../../.env',
            os.path.join(os.path.dirname(__file__), '../../main/.env')
        ]
        for path in possible_paths:
            if os.path.exists(path):
                load_dotenv(path)
                print(f"✓ Loaded environment from {path}")
                break
    
    # Get configuration with defaults
    config = {
        'gcp_project_id': os.getenv('GCP_PROJECT_ID', 'unext-ai-sandbox'),
        'gcp_location': os.getenv('GCP_LOCATION', 'us-central1'),
        'gcp_bucket_name': os.getenv('GCP_BUCKET_NAME', 'ci_team_test'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_file': os.getenv('LOG_FILE', f'logs/manga_descriptor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        'environment': os.getenv('ENVIRONMENT', 'development')
    }
    
    return config


@log_performance("GCP Authentication")
def setup_environment() -> bool:
    """
    Initialize Google Cloud authentication and basic environment setup.
    
    Returns:
        True if authentication successful, False otherwise
    """
    logger = get_logger()
    
    try:
        if not GCP_AUTH_AVAILABLE:
            logger.error("Google Cloud authentication libraries not available")
            logger.info("Install with: pip install google-auth google-auth-oauthlib")
            return False
        
        log_gcp_operation("Initializing default credentials")
        
        # Initialize default credentials
        credentials, project_id = google.auth.default()
        
        log_gcp_operation("Authentication successful", project_id=project_id)
        
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        logger.info("Please run: gcloud auth application-default login")
        return False


@log_performance("Vertex AI Initialization")
def initialize_vertex_ai(project_id: str, location: str = None) -> bool:
    """
    Initialize Vertex AI with project configuration.
    
    Args:
        project_id: Google Cloud project ID
        location: GCP region for Vertex AI services (defaults to environment config)
        
    Returns:
        True if initialization successful, False otherwise
    """
    logger = get_logger()
    
    # Get location from environment if not provided
    if location is None:
        config = load_environment_config()
        location = config['gcp_location']
    
    try:
        if not VERTEX_AI_AVAILABLE:
            logger.error("Vertex AI libraries not available")
            logger.info("Install with: pip install google-cloud-aiplatform")
            return False
        
        log_gcp_operation("Initializing Vertex AI", project_id=project_id, details={"location": location})
        
        vertexai.init(project=project_id, location=location)
        
        log_gcp_operation("Vertex AI initialization successful", project_id=project_id, details={"location": location})
        
        return True
    except Exception as e:
        logger.error(f"Vertex AI initialization failed: {e}")
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



def check_gcp_project_access(project_id: str) -> bool:
    """
    Verify access to specific GCP project and services.
    
    Args:
        project_id: Google Cloud project ID to check
        
    Returns:
        True if project is accessible, False otherwise
    """
    try:
        # Instead of checking storage buckets, just verify we can authenticate
        # and the project ID matches what we got from authentication
        credentials, auth_project_id = google.auth.default()
        
        if project_id != auth_project_id:
            print(f"❌ Project ID mismatch: requested {project_id}, authenticated for {auth_project_id}")
            return False
        
        # Try to verify Vertex AI access instead of storage
        if VERTEX_AI_AVAILABLE:
            try:
                # This is a lightweight check that doesn't require special permissions
                import vertexai
                vertexai.init(project=project_id, location="us-central1")
                print(f"✓ Project {project_id} is accessible via Vertex AI")
                return True
            except Exception as vertex_e:
                print(f"❌ Cannot access Vertex AI for project {project_id}: {vertex_e}")
                return False
        else:
            # If Vertex AI not available, just check that auth worked
            print(f"✓ Project {project_id} authenticated (Vertex AI not available for full check)")
            return True
            
    except Exception as e:
        print(f"❌ Cannot access project {project_id}: {e}")
        return False


def setup_full_environment(
    project_id: str = None, 
    location: str = None,
    log_level: str = None,
    log_file: Optional[str] = None,
    env_file_path: str = None
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
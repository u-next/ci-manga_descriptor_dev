#!/usr/bin/env python3
"""
Simple test to verify centralized logging with GCP interactions.
"""

import sys
import os

# Add refactor modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from refactor.utils.logging import setup_logger, get_logger, log_pipeline_stage
from refactor.infrastructure.gcp_setup import load_environment_config, setup_environment, initialize_vertex_ai

def test_logging_with_gcp():
    """Test the centralized logging system with GCP operations."""
    
    print("=== Testing Centralized Logging with GCP ===\n")
    
    # Setup logger with timestamped file
    logger = setup_logger(
        name="manga_agent_test",
        level="INFO",
        include_console=True
    )
    
    # Test basic logging
    logger.info("🧪 Starting logging test")
    
    # Test environment loading
    with log_pipeline_stage("Environment Configuration"):
        config = load_environment_config()
        logger.info(f"📋 Loaded config: project={config['gcp_project_id']}, location={config['gcp_location']}")
    
    # Test GCP authentication
    with log_pipeline_stage("GCP Authentication", {"project": config['gcp_project_id']}):
        auth_success = setup_environment()
        if auth_success:
            logger.info("✅ GCP authentication successful")
        else:
            logger.error("❌ GCP authentication failed")
            return False
    
    # Test Vertex AI initialization
    with log_pipeline_stage("Vertex AI Setup", {"location": config['gcp_location']}):
        vertex_success = initialize_vertex_ai(config['gcp_project_id'])
        if vertex_success:
            logger.info("✅ Vertex AI initialization successful")
        else:
            logger.warning("⚠️ Vertex AI initialization failed (may be expected)")
    
    logger.info("🏁 Logging test completed")
    
    return True

if __name__ == "__main__":
    try:
        success = test_logging_with_gcp()
        if success:
            print("\n✅ Logging test completed successfully!")
            print("📁 Check the logs/ directory for the log file output")
        else:
            print("\n❌ Logging test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1)
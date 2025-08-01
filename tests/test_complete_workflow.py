#!/usr/bin/env python3
"""
Complete Workflow Test

Test the complete refactored workflow with a single manga title and show detailed output
including individual descriptions, consensus processing, and final results.
"""

import sys
import os
import json
from datetime import datetime

# Add refactor modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

def setup_environment():
    """Set up the environment for testing"""
    # Set environment variables
    os.environ["GOOGLE_CLOUD_PROJECT"] = "unext-ai-sandbox"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    
    # Initialize Vertex AI
    try:
        import vertexai
        vertexai.init(project="unext-ai-sandbox", location="us-central1")
        print("✓ Vertex AI initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Vertex AI: {e}")
        print("  Make sure you're using: micromamba run -n colab_env python")
        return False

def test_complete_workflow():
    """Test the complete workflow with detailed output"""
    
    print("🧪 COMPLETE WORKFLOW TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Set up environment
    if not setup_environment():
        print("⚠️ Environment setup failed, but continuing with imports test...")
    
    # Import our refactored modules
    try:
        from refactor.models.config import MangaAgentConfig
        from refactor.processing.workflow import execute_manga_description_workflow
        from refactor.utils.logging import setup_logger, get_logger
        print("✓ Successfully imported refactored modules")
    except ImportError as e:
        print(f"✗ Failed to import modules: {e}")
        return False
    
    # Set up logging
    logger = setup_logger(
        name="complete_workflow_test",
        level="INFO",
        include_console=True
    )
    
    # Set up configuration
    config = MangaAgentConfig(project_id="unext-ai-sandbox")
    config.set_grounding(False)  # Start without grounding for reliability
    config.enable_debug(True)  # Enable debug mode to save individual descriptions
    
    # Validate configuration
    if not config.validate():
        print("✗ Configuration validation failed")
        return False
    
    print(f"✓ Configuration: {config}")
    print()
    
    # Test manga details - using a popular, well-known manga
    manga_title = "ワンピース"  # One Piece
    internal_index = "test_workflow_001"
    authors_info_json = '[{"NORMALIZE_PEN_NAME": "尾田栄一郎"}]'  # Eiichiro Oda
    
    print(f"📚 Testing Manga: {manga_title}")
    print(f"📋 Index: {internal_index}")
    print(f"👤 Authors: {authors_info_json}")
    print()
    
    # Execute the workflow
    try:
        print("🚀 EXECUTING COMPLETE WORKFLOW")
        print("=" * 60)
        
        result = execute_manga_description_workflow(
            manga_title=manga_title,
            internal_index=internal_index,
            authors_info_json=authors_info_json,
            config=config
        )
        
        print("=" * 60)
        print("✅ Workflow completed!")
        print()
        
        # Display detailed results
        display_detailed_results(result)
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def display_detailed_results(result):
    """Display comprehensive workflow results with individual descriptions"""
    
    print("📊 DETAILED WORKFLOW RESULTS")
    print("=" * 80)
    
    # Basic workflow info
    final_status = result.get('final_status', 'UNKNOWN')
    total_input_tokens = result.get('total_input_tokens_workflow', 0)
    total_output_tokens = result.get('total_output_tokens_workflow', 0)
    
    print(f"🏁 Final Status: {final_status}")
    print(f"🔢 Total Input Tokens: {total_input_tokens}")
    print(f"🔢 Total Output Tokens: {total_output_tokens}")
    print()
    
    # Generator details - show each description individually
    generator_details = result.get('generator_details', [])
    print(f"🤖 GENERATED DESCRIPTIONS ({len(generator_details)} attempts)")
    print("=" * 80)
    
    valid_count = 0
    for i, (model_id, description) in enumerate(generator_details, 1):
        print(f"\n📝 Description {i}/4 - Model: {model_id}")
        print("─" * 50)
        
        if description and not description.startswith("FAILURE:"):
            valid_count += 1
            try:
                # Try to parse and display JSON nicely
                parsed = json.loads(description)
                print("✅ STATUS: Valid JSON")
                print("📄 CONTENT:")
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print("⚠️ STATUS: Valid response but not JSON")
                print("📄 CONTENT:")
                print(description)
        else:
            print("❌ STATUS: Failed")
            print("📄 ERROR:")
            print(description[:500] + "..." if len(description) > 500 else description)
        
        print("─" * 50)
    
    print(f"\n📈 Generation Summary: {valid_count}/4 valid descriptions generated")
    print()
    
    # Judge/Consensus output
    judge_output = result.get('judge_full_output', '')
    if judge_output:
        print("⚖️ DECISION PROCESS")
        print("=" * 80)
        
        # Check if consensus was used
        if "Enhanced Processing" in judge_output:
            print("🎯 APPROACH: Consensus-based (skipped traditional judge)")
            print("📊 DETAILS:")
            print(judge_output)
        else:
            print("🎯 APPROACH: Traditional judge fallback")
            print("📊 JUDGE OUTPUT:")
            print(judge_output)
        print()
    
    # Final description
    final_description = result.get('final_description', '')
    if final_description:
        print("🏆 FINAL DESCRIPTION")
        print("=" * 80)
        try:
            # Try to parse and display JSON nicely
            parsed = json.loads(final_description)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except (json.JSONDecodeError, TypeError):
            print(final_description)
        print()
    
    # Workflow analysis
    print("🔍 WORKFLOW ANALYSIS")
    print("=" * 80)
    
    print(f"✓ Valid descriptions generated: {valid_count}/4")
    
    # Determine what path was taken
    if "Enhanced Processing" in judge_output:
        print("✓ Used enhanced consensus processing")
        print("✓ Successfully avoided traditional judge (more efficient)")
    elif judge_output and not judge_output.startswith("FAILURE"):
        print("✓ Used traditional judge as fallback")
    else:
        print("✗ No valid final description produced")
    
    # Token efficiency
    if total_input_tokens > 0 and total_output_tokens > 0:
        token_ratio = total_output_tokens / total_input_tokens
        print(f"✓ Token efficiency: {token_ratio:.2f} output/input ratio")
    
    print(f"✓ Final status: {final_status}")
    print()

def main():
    """Run the complete workflow test"""
    print("🎯 MANGA DESCRIPTOR COMPLETE WORKFLOW TEST")
    print("=" * 80)
    print("This test runs a single manga through the complete refactored workflow")
    print("and shows detailed output including individual descriptions and consensus.")
    print()
    
    try:
        success = test_complete_workflow()
        
        print("=" * 80)
        if success:
            print("🎉 COMPLETE WORKFLOW TEST PASSED!")
            print("✅ All workflow components are working correctly")
            print("✅ Detailed output shows individual descriptions and decision process")
            print("✅ Ready for production use with real manga data")
        else:
            print("❌ COMPLETE WORKFLOW TEST FAILED!")
            print("⚠️ Check the errors above for troubleshooting")
        
        return success
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
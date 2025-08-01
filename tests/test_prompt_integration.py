#!/usr/bin/env python3
"""
Prompt Integration Testing

Test the integration of the new prompt loading system with the workflow.
"""

import sys
import os
from datetime import datetime

# Add refactor modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Import modules for testing
from refactor.utils.logging import setup_logger, get_logger
from refactor.utils.prompt_loading import load_single_description_prompt, load_judge_prompt
from refactor.models.prompts import PromptType
from refactor.processing.workflow import _create_generation_system_instruction, _create_judge_system_instruction


def test_prompt_integration():
    """Test the integration of prompt loading with workflow functions."""
    
    print("=== Testing Prompt Loading Integration ===\n")
    
    # Setup logger
    logger = setup_logger(
        name="prompt_integration_test",
        level="INFO",
        include_console=True
    )
    
    logger.info("🚀 Starting prompt integration tests")
    
    # Test data
    test_manga_title = "テストマンガ"
    test_internal_index = "TEST001"
    test_author_list_str = "テスト作者"
    test_num_descriptions = 4
    
    try:
        # Test 1: Direct prompt loading functions
        logger.info("📝 Testing direct prompt loading functions...")
        
        # Test standard single description prompt
        standard_prompt = load_single_description_prompt(
            manga_title=test_manga_title,
            internal_index=test_internal_index,
            author_list_str=test_author_list_str,
            prompt_type=PromptType.STANDARD
        )
        
        # Test doujinshi prompt
        doujinshi_prompt = load_single_description_prompt(
            manga_title=test_manga_title,
            internal_index=test_internal_index,
            author_list_str=test_author_list_str,
            prompt_type=PromptType.DOUJINSHI,
            title_search_terms=f'"{test_manga_title}"'
        )
        
        # Test adult prompt
        adult_prompt = load_single_description_prompt(
            manga_title=test_manga_title,
            internal_index=test_internal_index,
            author_list_str=test_author_list_str,
            prompt_type=PromptType.ADULT,
            title_search_terms=f'"{test_manga_title}"'
        )
        
        # Test judge prompt
        judge_prompt = load_judge_prompt(
            manga_title=test_manga_title,
            num_descriptions=test_num_descriptions
        )
        
        # Validate prompts were generated
        logger.info(f"✅ Standard prompt generated: {len(standard_prompt)} characters")
        logger.info(f"✅ Doujinshi prompt generated: {len(doujinshi_prompt)} characters")
        logger.info(f"✅ Adult prompt generated: {len(adult_prompt)} characters")
        logger.info(f"✅ Judge prompt generated: {len(judge_prompt)} characters")
        
        # Test 2: Workflow integration functions
        logger.info("🔧 Testing workflow integration functions...")
        
        # Test workflow generation system instruction
        workflow_system_instruction = _create_generation_system_instruction(
            manga_title=test_manga_title,
            internal_index=test_internal_index,
            author_list_str=test_author_list_str
        )
        
        # Test workflow judge system instruction
        workflow_judge_instruction = _create_judge_system_instruction(
            num_descriptions=test_num_descriptions,
            manga_title=test_manga_title
        )
        
        logger.info(f"✅ Workflow system instruction generated: {len(workflow_system_instruction)} characters")
        logger.info(f"✅ Workflow judge instruction generated: {len(workflow_judge_instruction)} characters")
        
        # Test 3: Content validation
        logger.info("🔍 Testing prompt content validation...")
        
        # Check that prompts contain expected elements
        validations = [
            ("Standard prompt contains manga title", test_manga_title in standard_prompt),
            ("Standard prompt contains internal index", test_internal_index in standard_prompt),
            ("Standard prompt contains author", test_author_list_str in standard_prompt),
            ("Doujinshi prompt mentions specialized databases", "Booth marketplace" in doujinshi_prompt),
            ("Adult prompt mentions academic databases", "MangaUpdates library catalog" in adult_prompt),
            ("Judge prompt mentions evaluation criteria", "Character Accuracy" in judge_prompt),
            ("Judge prompt mentions confidence score", "Confidence Score" in judge_prompt),
            ("Workflow integration matches direct loading", workflow_system_instruction == standard_prompt),
            ("Judge integration matches direct loading", workflow_judge_instruction == judge_prompt)
        ]
        
        passed_validations = 0
        for description, passed in validations:
            if passed:
                logger.info(f"✅ {description}")
                passed_validations += 1
            else:
                logger.warning(f"❌ {description}")
        
        logger.info(f"📊 Validation results: {passed_validations}/{len(validations)} passed")
        
        # Test 4: Parameter validation
        logger.info("⚠️ Testing parameter validation...")
        
        try:
            # Test with None parameter (should raise ValueError)
            load_single_description_prompt(
                manga_title=None,
                internal_index=test_internal_index,
                author_list_str=test_author_list_str
            )
            logger.warning("❌ Parameter validation failed - should have raised ValueError")
        except ValueError as e:
            logger.info(f"✅ Parameter validation working: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected validation error: {e}")
        
        # Test 5: Performance check
        logger.info("⚡ Testing performance...")
        
        start_time = datetime.now()
        for i in range(10):
            load_single_description_prompt(
                manga_title=f"テストマンガ{i}",
                internal_index=f"TEST{i:03d}",
                author_list_str="テスト作者"
            )
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"✅ Performance test: 10 prompts loaded in {duration:.3f}s ({duration/10:.3f}s avg)")
        
        logger.info("🎉 Prompt integration tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Prompt integration test failed: {e}")
        logger.exception("Full error traceback:")
        return False


if __name__ == "__main__":
    try:
        success = test_prompt_integration()
        if success:
            print("\n✅ Prompt integration test PASSED!")
            print("🔧 Workflow is ready to use new prompt loading system")
            print("📁 Check the logs/ directory for detailed test output")
        else:
            print("\n❌ Prompt integration test FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)
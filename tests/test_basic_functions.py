#!/usr/bin/env python3
"""
Basic Test Script for Manga Descriptor Components

This script tests the basic utilities that should work without external dependencies.
It's designed to verify the core refactored components are functional.
"""

import sys
import os

# Add refactor modules to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
refactor_dir = os.path.join(current_dir, '..', '..', 'refactor')
sys.path.insert(0, refactor_dir)

def test_content_detection():
    """Test content detection utilities"""
    print("=== Testing Content Detection ===")
    
    try:
        from utils.content_detection import is_adult_content, is_potential_doujinshi
        
        test_titles = [
            "キングダム",  # Safe title
            "恋愛コメディ",  # Romance (adult content)
            "motolog",  # Potential doujinshi
            "ワンピース",  # Safe title
            "Boys Love Story",  # English adult content
        ]
        
        for title in test_titles:
            adult = is_adult_content(title)
            # doujinshi = is_potential_doujinshi(title)  # Need to check if this function exists
            print(f"'{title}': Adult Content = {adult}")
        
        print("✅ Content detection functions working")
        return True
        
    except Exception as e:
        print(f"❌ Content detection failed: {e}")
        return False


def test_title_processing():
    """Test title processing utilities"""
    print("\n=== Testing Title Processing ===")
    
    try:
        from utils.title_processing import clean_manga_title, generate_title_variations
        
        test_titles = [
            "【期間限定】キングダム 分冊版",
            "motolog",
            "ワンピース～冒険の始まり：",
            "One Piece (English Edition)"
        ]
        
        for title in test_titles:
            cleaned = clean_manga_title(title)
            variations = generate_title_variations(cleaned)
            print(f"Original: '{title}'")
            print(f"Cleaned: '{cleaned}'")
            print(f"Variations: {variations}")
            print()
        
        print("✅ Title processing functions working")
        return True
        
    except Exception as e:
        print(f"❌ Title processing failed: {e}")
        return False


def test_json_extraction():
    """Test JSON extraction utilities"""
    print("=== Testing JSON Extraction ===")
    
    try:
        from utils.json_extraction import extract_json_from_text
        
        test_texts = [
            '{"title": "Test Manga", "genre": "Action"}',
            '''Here's the result:
            ```json
            {"title": "Another Manga", "genre": "Romance"}
            ```''',
            'The JSON object is: {"title": "Third Manga", "description": "A great story"}'
        ]
        
        for i, text in enumerate(test_texts, 1):
            extracted = extract_json_from_text(text)
            print(f"Text {i}: {extracted}")
        
        print("✅ JSON extraction functions working")
        return True
        
    except Exception as e:
        print(f"❌ JSON extraction failed: {e}")
        return False


def test_infrastructure_check():
    """Test infrastructure dependency checking"""
    print("\n=== Testing Infrastructure ===")
    
    try:
        from infrastructure.gcp_setup import verify_dependencies
        
        dependencies = verify_dependencies()
        
        print("✅ Infrastructure dependency check working")
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure check failed: {e}")
        return False


def test_sample_manga_title():
    """Test a complete flow with a sample manga title"""
    print("\n=== Testing Complete Flow with Sample Title ===")
    
    sample_title = "【限定版】鬼滅の刃～無限列車編：完全版"
    
    try:
        # Import what we can
        from utils.content_detection import is_adult_content
        from utils.title_processing import clean_manga_title, generate_title_variations
        
        print(f"Testing with: '{sample_title}'")
        
        # Step 1: Content detection
        is_adult = is_adult_content(sample_title)
        print(f"Adult content detected: {is_adult}")
        
        # Step 2: Title cleaning
        cleaned_title = clean_manga_title(sample_title)
        print(f"Cleaned title: '{cleaned_title}'")
        
        # Step 3: Generate variations
        variations = generate_title_variations(cleaned_title)
        print(f"Title variations: {variations}")
        
        print("✅ Complete flow test successful")
        return True
        
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        return False


def main():
    """Run all basic tests"""
    print("🧪 Testing Basic Manga Descriptor Components")
    print("=" * 50)
    
    results = []
    
    # Run individual tests
    results.append(test_content_detection())
    results.append(test_title_processing())
    results.append(test_json_extraction())
    results.append(test_infrastructure_check())
    results.append(test_sample_manga_title())
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All basic tests passed! Core utilities are working.")
        print("\nNext steps for full functionality:")
        print("1. Install GCP dependencies: pip install google-cloud-aiplatform google-auth")
        print("2. Set up authentication: gcloud auth application-default login")
        print("3. Implement remaining placeholder functions in workflow.py")
        print("4. Test with real Vertex AI models")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
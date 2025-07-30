#!/usr/bin/env python3
"""
Example Usage of Refactored Manga Description Components

This script demonstrates how to use the extracted utility functions,
I/O operations, infrastructure setup, and modular workflow components
from the refactored manga description system.
"""

# Example imports (these would work once the modules are fully integrated)
from utils import (
    is_adult_content, 
    is_potential_doujinshi,
    clean_manga_title,
    generate_title_variations,
    extract_json_from_text
)

from processing import execute_manga_description_workflow

from io import (
    load_input_data,
    prepare_workflow_dataframe,
    save_workflow_results,
    validate_input_format
)

from infrastructure import (
    setup_environment,
    initialize_vertex_ai,
    verify_dependencies,
    setup_full_environment
)


def demonstrate_content_detection():
    """Demonstrate content detection utilities"""
    print("=== Content Detection Examples ===")
    
    test_titles = [
        "キングダム",  # Safe title
        "恋愛コメディ",  # Romance (adult content)
        "motolog",  # Potential doujinshi
        "ワンピース"  # Safe title
    ]
    
    for title in test_titles:
        adult = is_adult_content(title)
        doujinshi = is_potential_doujinshi(title)
        print(f"'{title}': Adult={adult}, Doujinshi={doujinshi}")


def demonstrate_title_processing():
    """Demonstrate title processing utilities"""
    print("\\n=== Title Processing Examples ===")
    
    test_titles = [
        "【期間限定】キングダム 分冊版",
        "motolog",
        "ワンピース～冒険の始まり："
    ]
    
    for title in test_titles:
        cleaned = clean_manga_title(title)
        variations = generate_title_variations(cleaned)
        print(f"Original: '{title}'")
        print(f"Cleaned: '{cleaned}'")
        print(f"Variations: {variations}")
        print()


def demonstrate_json_extraction():
    """Demonstrate JSON extraction utilities"""
    print("=== JSON Extraction Examples ===")
    
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


def demonstrate_infrastructure_setup():
    """Demonstrate infrastructure and I/O functions"""
    print("\\n=== Infrastructure & I/O Examples ===")
    
    print("Infrastructure setup:")
    print("- setup_environment() - GCP authentication")
    print("- initialize_vertex_ai() - Vertex AI initialization")
    print("- verify_dependencies() - Check required packages")
    
    print("\\nI/O operations:")
    print("- load_input_data() - Load CSV from local/GCS")
    print("- prepare_workflow_dataframe() - Clean and validate data")
    print("- save_workflow_results() - Save results to GCS/local")
    print("- validate_input_format() - Check required columns")


def demonstrate_workflow_structure():
    """Show the structure of the refactored workflow"""
    print("\\n=== Refactored Workflow Structure ===")
    
    print("""
    Original monolithic function (273 lines) has been broken down into:
    
    1. execute_manga_description_workflow() - Main orchestrator
       ├── preprocess_authors_step() - Author preprocessing (10 lines)
       ├── generate_descriptions_step() - Description generation (35 lines)  
       ├── enhanced_processing_step() - Normalization & consensus (55 lines)
       ├── decide_final_output_step() - Consensus vs judge logic (135 lines)
       └── format_workflow_results() - Result formatting (13 lines)
    
    Benefits:
    - Each function is testable in isolation
    - Clear separation of concerns
    - Easier to debug and maintain
    - Better error handling opportunities
    """)


if __name__ == "__main__":
    demonstrate_content_detection()
    demonstrate_title_processing()
    demonstrate_json_extraction()
    demonstrate_infrastructure_setup()
    demonstrate_workflow_structure()
    
    print("\\n=== Complete Refactoring Summary ===")
    print("✅ Content detection utilities extracted (utils/content_detection.py)")
    print("✅ Title processing utilities extracted (utils/title_processing.py)") 
    print("✅ JSON extraction utilities extracted (utils/json_extraction.py)")
    print("✅ Input/output functions extracted (io/data_loader.py, io/output_manager.py)")
    print("✅ Infrastructure setup extracted (infrastructure/gcp_setup.py)")
    print("✅ Workflow function broken down into manageable components (processing/workflow.py)")
    print("✅ Module structure with proper __init__.py files created")
    print("\\nReady for live coding session! 🚀")
    print("\\nNext steps: Integrate with original system and add comprehensive testing")
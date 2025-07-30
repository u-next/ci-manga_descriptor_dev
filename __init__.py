"""
Utility Functions for Manga Description Generation

This package contains reusable utility functions extracted from the monolithic
manga_agent_runner.py for better maintainability and testability.

Modules:
    content_detection: Adult content and doujinshi detection
    title_processing: Title cleaning and variation generation
    json_extraction: JSON parsing from mixed-format text
"""

from .content_detection import is_adult_content, is_potential_doujinshi
from .title_processing import clean_manga_title, generate_title_variations
from .json_extraction import extract_json_from_text

__all__ = [
    'is_adult_content',
    'is_potential_doujinshi', 
    'clean_manga_title',
    'generate_title_variations',
    'extract_json_from_text'
]
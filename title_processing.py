"""
Title Processing Utilities

This module provides functions for cleaning and processing manga titles
to improve search quality and grounding effectiveness.

Functions:
    clean_manga_title: Remove metadata and normalize titles
    generate_title_variations: Create multiple case variations for searching
"""

import re
from typing import List


def clean_manga_title(title: str) -> str:
    """
    Cleans a manga title by removing extraneous metadata and normalizing case for better searching.
    Handles unconventional titles like 'motolog' by generating multiple search variations.
    
    Args:
        title: Raw manga title to clean
        
    Returns:
        Cleaned title with metadata removed and normalized spacing
    """
    # Remove content in any type of bracket: 【...】, [...], (...)
    cleaned_title = re.sub(r'[【\[(].*?[)\]】]', '', title)

    # Remove separator characters like tilde and colon by replacing them with a space
    cleaned_title = cleaned_title.replace('～', ' ')
    cleaned_title = cleaned_title.replace('：', ' ')

    # Remove common edition-related phrases
    phrases_to_remove = [
        '分冊版', '電子限定おまけ付き', 'モノクロ版', 'フルカラー版', '話売り'
    ]
    for phrase in phrases_to_remove:
        cleaned_title = cleaned_title.replace(phrase, '')

    # Remove any trailing question marks or exclamation marks
    cleaned_title = cleaned_title.rstrip('?! ').strip()

    # Replace multiple spaces with a single space for cleanliness
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title)

    return cleaned_title


def generate_title_variations(title: str) -> List[str]:
    """
    Generate multiple case variations of a title for better search coverage.
    Handles unconventional titles like 'motolog' -> ['motolog', 'Motolog', 'MOTOLOG', 'MotoLog']
    
    Args:
        title: Title to generate variations for
        
    Returns:
        List of title variations with different case patterns
    """
    variations = [title]  # Original title
    
    # Add basic case variations
    if title.lower() not in [v.lower() for v in variations]:
        variations.append(title.lower())
    if title.upper() not in [v.upper() for v in variations]:
        variations.append(title.upper())
    if title.capitalize() not in variations:
        variations.append(title.capitalize())
    if title.title() not in variations:
        variations.append(title.title())
    
    # For unconventional lowercase titles, try mixed case patterns
    if title.islower() and len(title) > 4:
        # Try capitalizing at word boundaries and mid-word for compound words
        for i in range(1, len(title)):
            if i == len(title) // 2:  # Middle capitalization (motolog -> motoLog)
                variation = title[:i] + title[i:].capitalize()
                if variation not in variations:
                    variations.append(variation)
    
    return variations
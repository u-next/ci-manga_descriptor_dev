"""
Author Processing Utilities

This module contains utilities for processing manga author information,
including JSON parsing, validation, and LLM-based author research fallback.

Functions:
    preprocess_manga_authors: Main author preprocessing function
    research_authors_with_llm: LLM-based author research
    validate_author_name: Author name validation
"""

import json
from typing import Dict, List, Any, Optional

# Import centralized logging
from .logging import get_logger, log_performance, log_model_operation


@log_performance("Preprocess Authors")
def preprocess_manga_authors(
    manga_title: str, 
    internal_index: str, 
    authors_info_json: str, 
    config
) -> List[str]:
    """
    Extract and preprocess author information for manga processing.
    
    Improved modular version that handles JSON parsing, validation,
    and fallback author research with proper error handling.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors_info_json: JSON string with author information
        config: MangaAgentConfig instance
        
    Returns:
        List of preprocessed author names
    """
    logger = get_logger()
    
    logger.info(f"Preprocessing authors for '{manga_title}'")
    
    known_author_names = []
    
    try:
        # Handle missing or invalid author info with robust type checking
        if _is_empty_author_info(authors_info_json):
            authors_data = []
            logger.debug(f"Empty author info for '{manga_title}', will attempt research")
        else:
            authors_data = _parse_authors_json(authors_info_json, manga_title, logger)
            
        # Extract normalized pen names from valid author data
        if isinstance(authors_data, list):
            known_author_names = _extract_author_names(authors_data, logger)
            
    except Exception as e:
        logger.error(f"Unexpected error parsing authors_info for '{manga_title}': {e}")
        authors_data = []
    
    # Fallback: Research authors using LLM if no valid data found
    if not known_author_names:
        logger.info(f"No author info available for '{manga_title}', researching authors...")
        known_author_names = research_authors_with_llm(
            manga_title, internal_index, config, logger
        )
        
        if known_author_names:
            logger.info(f"Found authors via research: {', '.join(known_author_names)}")
        else:
            logger.warning(f"Could not determine authors for '{manga_title}'")
    else:
        logger.info(f"Authors processed: {', '.join(known_author_names)}")
    
    return known_author_names


def research_authors_with_llm(
    manga_title: str, 
    internal_index: str, 
    config, 
    logger
) -> List[str]:
    """
    Research manga authors using LLM when author information is missing.
    
    Improved version with better error handling, model selection,
    and response validation.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        config: MangaAgentConfig instance
        logger: Logger instance
        
    Returns:
        List of author names found, or empty list if research fails
    """
    try:
        # Import here to avoid circular dependencies
        from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
        
        # Select the first available generator model, fallback to flash
        model_id = (config.generator_model_ids[0] if config.generator_model_ids 
                   else "gemini-2.0-flash-exp")
        
        logger.debug(f"Researching authors for '{manga_title}' using model: {model_id}")
        
        # Create focused research prompt
        research_prompt = _create_author_research_prompt(manga_title)
        
        # Configure model with conservative settings for factual accuracy
        model = GenerativeModel(
            model_name=model_id,
            generation_config=GenerationConfig(
                temperature=0.1,  # Low temperature for factual accuracy
                max_output_tokens=2048,  # Reduced tokens for focused response
                top_p=0.8,
                top_k=10
            ),
            safety_settings=config.custom_safety_settings or _get_default_safety_settings()
        )
        
        # Generate and process response
        with log_model_operation(f"Author Research - {model_id}", {"manga_title": manga_title}):
            response = model.generate_content(research_prompt)
            
        return _process_author_research_response(response, manga_title, logger)
        
    except Exception as e:
        logger.error(f"Error researching authors for '{manga_title}': {e}")
        return []


def validate_author_name(name: str) -> bool:
    """
    Validate that an author name seems reasonable.
    
    Args:
        name: Author name to validate
        
    Returns:
        True if the name appears to be a valid author name
    """
    if not name or len(name.strip()) < 2:
        return False
    
    # Basic validation - reject obvious garbage
    name = name.strip()
    if any(char in name for char in ['<', '>', '{', '}', '[', ']']):
        return False
    
    # Reject overly long names (likely not real author names)
    if len(name) > 100:
        return False
        
    return True


# Private helper functions

def _is_empty_author_info(authors_info_json: Any) -> bool:
    """Check if author info is None, NaN, empty string, or invalid."""
    import pandas as pd
    return (authors_info_json is None or 
            pd.isna(authors_info_json) or 
            authors_info_json == '' or
            (isinstance(authors_info_json, str) and authors_info_json.strip() == ''))


def _parse_authors_json(authors_info_json: str, manga_title: str, logger) -> List[Dict]:
    """Parse and validate authors JSON data with proper error handling."""
    import pandas as pd
    
    try:
        if isinstance(authors_info_json, str):
            return json.loads(authors_info_json)
        else:
            # Handle non-string types (like float/NaN) 
            logger.warning(f"Invalid authors_info type {type(authors_info_json)} for '{manga_title}', using empty list")
            return []
            
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse authors_info JSON for '{manga_title}': {e}")
        return []


def _extract_author_names(authors_data: List[Dict], logger) -> List[str]:
    """Extract and validate normalized pen names from author data."""
    author_names = []
    
    for author in authors_data:
        if isinstance(author, dict):
            pen_name = author.get("NORMALIZE_PEN_NAME")
            if pen_name and isinstance(pen_name, str) and pen_name.strip():
                author_names.append(pen_name.strip())
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(author_names))


def _create_author_research_prompt(manga_title: str) -> str:
    """Create a focused prompt for author research."""
    return f"""Identify the author(s) of this manga: "{manga_title}"

Respond with ONLY the author name(s). If multiple authors, separate with commas. If unknown, respond "UNKNOWN".

Author(s):"""


def _get_default_safety_settings():
    """Get default safety settings for author research."""
    from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
    
    return [
        SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
        SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
        SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
        SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
    ]


def _process_author_research_response(response, manga_title: str, logger) -> List[str]:
    """Process and validate author research response."""
    if not response or not response.text:
        # Check for token limit issues
        if response and response.candidates:
            for candidate in response.candidates:
                if (hasattr(candidate, 'finish_reason') and 
                    candidate.finish_reason.name == 'MAX_TOKENS'):
                    logger.warning(f"Author research hit MAX_TOKENS for '{manga_title}', skipping research")
                    return []
        
        logger.warning(f"No response text for author research of '{manga_title}'")
        return []
    
    authors_text = response.text.strip()
    
    # Handle "unknown" response
    if authors_text.upper() == "UNKNOWN":
        return []
    
    # Parse and clean author names
    authors = [author.strip().strip('"\'') for author in authors_text.split(',')]
    authors = [author for author in authors if author and author.lower() != 'unknown']
    
    # Limit to max 3 authors to avoid noise and validate names
    validated_authors = []
    for author in authors[:3]:
        if validate_author_name(author):
            validated_authors.append(author)
    
    return validated_authors
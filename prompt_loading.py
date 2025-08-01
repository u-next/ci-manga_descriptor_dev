#!/usr/bin/env python3
"""
Prompt Loading Utilities

This module provides centralized prompt loading functions for the manga description generation system.
Imports prompt templates from models.prompts and provides convenient loading functions.
"""

from typing import Dict, Any, Optional

# Import from models
from ..models.prompts import PromptTemplates, PromptType


class PromptLoader:
    """Utility class for loading and formatting prompt templates."""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def load_single_description_prompt(
        self, 
        manga_title: str, 
        internal_index: str, 
        author_list_str: str,
        prompt_type: PromptType = PromptType.STANDARD,
        title_search_terms: Optional[str] = None
    ) -> str:
        """
        Load formatted single description prompt based on content type.
        
        Args:
            manga_title: The title of the manga
            internal_index: Internal index for the manga
            author_list_str: Comma-separated string of author names
            prompt_type: Type of prompt to use (standard, doujinshi, adult)
            title_search_terms: Search terms for title (used in doujinshi/adult prompts)
            
        Returns:
            Formatted prompt string ready for LLM
        """
        # Validate parameters
        self._validate_parameters(
            manga_title=manga_title,
            internal_index=internal_index,
            author_list_str=author_list_str
        )
        
        if prompt_type == PromptType.STANDARD:
            return self.templates.SINGLE_DESCRIPTION_STANDARD.format(
                manga_title=manga_title,
                internal_index=internal_index,
                author_list_str=author_list_str
            )
        elif prompt_type == PromptType.DOUJINSHI:
            if title_search_terms is None:
                title_search_terms = manga_title
            return self.templates.SINGLE_DESCRIPTION_DOUJINSHI.format(
                title_search_terms=title_search_terms,
                internal_index=internal_index,
                author_list_str=author_list_str
            )
        elif prompt_type == PromptType.ADULT:
            if title_search_terms is None:
                title_search_terms = manga_title
            return self.templates.SINGLE_DESCRIPTION_ADULT.format(
                title_search_terms=title_search_terms,
                internal_index=internal_index,
                author_list_str=author_list_str
            )
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def load_judge_prompt(
        self, 
        manga_title: str, 
        num_descriptions: int
    ) -> str:
        """
        Load formatted judge evaluation prompt.
        
        Args:
            manga_title: The title of the manga
            num_descriptions: Number of descriptions to evaluate
            
        Returns:
            Formatted prompt string ready for LLM
        """
        self._validate_parameters(
            manga_title=manga_title,
            num_descriptions=num_descriptions
        )
        
        return self.templates.JUDGE_EVALUATION.format(
            manga_title=manga_title,
            num_descriptions=num_descriptions
        )
    
    def _validate_parameters(self, **kwargs) -> None:
        """
        Validate prompt parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        for key, value in kwargs.items():
            if value is None:
                raise ValueError(f"Required parameter '{key}' cannot be None")
            
            # Validate specific parameter types
            if key == 'num_descriptions' and (not isinstance(value, int) or value < 1):
                raise ValueError(f"Parameter '{key}' must be a positive integer")
            
            # Convert to string and validate non-empty for string parameters
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"Parameter '{key}' cannot be empty")
    
    def get_available_prompt_types(self) -> Dict[str, Any]:
        """
        Get information about available prompt types.
        
        Returns:
            Dictionary with prompt type information
        """
        return {
            "prompt_types": [pt.value for pt in PromptType],
            "single_description_types": [
                PromptType.STANDARD.value,
                PromptType.DOUJINSHI.value,
                PromptType.ADULT.value
            ],
            "judge_type": PromptType.JUDGE.value,
            "standard_params": ["manga_title", "internal_index", "author_list_str"],
            "doujinshi_params": ["manga_title", "internal_index", "author_list_str", "title_search_terms"],
            "adult_params": ["manga_title", "internal_index", "author_list_str", "title_search_terms"],
            "judge_params": ["manga_title", "num_descriptions"]
        }


# Create a global instance for easy access
prompt_loader = PromptLoader()


def load_single_description_prompt(
    manga_title: str, 
    internal_index: str, 
    author_list_str: str,
    prompt_type: PromptType = PromptType.STANDARD,
    title_search_terms: Optional[str] = None
) -> str:
    """
    Convenience function to load single description prompt.
    
    Args:
        manga_title: The title of the manga
        internal_index: Internal index for the manga  
        author_list_str: Comma-separated string of author names
        prompt_type: Type of prompt to use (standard, doujinshi, adult)
        title_search_terms: Search terms for title (used in doujinshi/adult prompts)
        
    Returns:
        Formatted prompt string ready for LLM
    """
    return prompt_loader.load_single_description_prompt(
        manga_title=manga_title,
        internal_index=internal_index,
        author_list_str=author_list_str,
        prompt_type=prompt_type,
        title_search_terms=title_search_terms
    )


def load_judge_prompt(manga_title: str, num_descriptions: int) -> str:
    """
    Convenience function to load judge evaluation prompt.
    
    Args:
        manga_title: The title of the manga
        num_descriptions: Number of descriptions to evaluate
        
    Returns:
        Formatted prompt string ready for LLM
    """
    return prompt_loader.load_judge_prompt(
        manga_title=manga_title,
        num_descriptions=num_descriptions
    )


# Export the main functions and classes for easy import
__all__ = [
    'PromptLoader',
    'PromptTemplates', 
    'PromptType',
    'prompt_loader',
    'load_single_description_prompt',
    'load_judge_prompt'
]
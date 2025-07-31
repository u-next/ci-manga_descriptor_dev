"""
Configuration Module for Manga Agent

This module contains configuration classes and settings for the manga description
generation system, including model configurations and safety settings.
"""

from typing import List, Optional

# Import centralized logging
from ..utils.logging import get_logger, log_model_operation

# Try to import Vertex AI types, fall back to None if not available
try:
    from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    # Create dummy classes for when Vertex AI is not available
    class SafetySetting:
        def __init__(self, category, threshold):
            self.category = category
            self.threshold = threshold
    
    class HarmCategory:
        HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
        HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
        HARM_CATEGORY_UNSPECIFIED = "HARM_CATEGORY_UNSPECIFIED"
    
    class HarmBlockThreshold:
        BLOCK_NONE = "BLOCK_NONE"


class MangaAgentConfig:
    """Configuration class for manga agent settings"""
    
    def __init__(self, project_id: str = "un-ds-dwh"):
        self.project_id = project_id
        self.location = "us-central1"
        
        # Updated to current best practice models
        self.generator_model_ids = [
            'gemini-2.5-flash',
            'gemini-2.5-flash', 
            'gemini-2.5-flash',
            'gemini-2.5-flash'
        ]
        self.judge_model_id = "gemini-2.5-pro"
        
        # Safety settings to allow manga content analysis
        if VERTEX_AI_AVAILABLE:
            self.custom_safety_settings = [
                SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_UNSPECIFIED, threshold=HarmBlockThreshold.BLOCK_NONE)
            ]
        else:
            self.custom_safety_settings = []
        
        # Additional settings
        self.enable_grounding = False
        self.max_workers = 4
        self.enable_debug_output = False
        
        # Enhanced processing settings
        self.factual_confidence_threshold = 56.0
        self.min_descriptions_for_consensus = 2
        
    def update_project(self, project_id: str):
        """Update the project ID for the configuration"""
        self.project_id = project_id
        
    def enable_debug(self, enabled: bool = True):
        """Enable or disable debug output"""
        self.enable_debug_output = enabled
        
    def set_grounding(self, enabled: bool = True):
        """Enable or disable Google Search grounding"""
        self.enable_grounding = enabled
        
    def validate(self) -> bool:
        """Validate the configuration settings"""
        if not self.project_id:
            return False
        if not self.generator_model_ids:
            return False
        if not self.judge_model_id:
            return False
        return True
    
    def __repr__(self):
        return f"MangaAgentConfig(project={self.project_id}, generators={len(self.generator_model_ids)}, judge={self.judge_model_id})"
"""
Models Module

This module contains AI model configurations, settings, and data structures
for the manga description generation system.

Classes:
    MangaAgentConfig: Configuration settings for the manga agent
    WorkflowResult: Container for workflow execution results
"""

from .config import MangaAgentConfig
from .workflow_results import WorkflowResult, GenerationResult, AuthorInfo, EnhancedProcessingResult, FactualVerification

__all__ = ['MangaAgentConfig', 'WorkflowResult', 'GenerationResult', 'AuthorInfo', 'EnhancedProcessingResult', 'FactualVerification']
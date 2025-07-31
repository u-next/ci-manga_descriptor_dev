"""
Workflow Results for Manga Description System

This module contains result containers and data classes specifically for the manga
description generation workflow execution and processing steps.
"""

from dataclasses import dataclass
from typing import List, Tuple, Any, Optional, Dict


@dataclass
class WorkflowResult:
    """Container for complete workflow execution results"""
    generator_details: List[Tuple[str, str]]
    judge_model_id_used: str
    judge_full_output: Optional[str]
    judge_finish_reason: str
    final_status: str
    final_description: Optional[str]
    total_input_tokens_workflow: int
    total_output_tokens_workflow: int


@dataclass
class GenerationResult:
    """Container for single description generation result"""
    description_json: Optional[str]
    model_id: str
    input_tokens: int
    output_tokens: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class AuthorInfo:
    """Container for processed author information"""
    names: List[str]
    research_results: List[str]
    total_found: int
    
    def has_authors(self) -> bool:
        return len(self.names) > 0
    
    def get_display_string(self) -> str:
        if not self.names:
            return "No author information available"
        return ", ".join(self.names)


@dataclass
class EnhancedProcessingResult:
    """Container for enhanced processing step results"""
    normalized_descriptions: List[Dict[str, Any]]
    factual_verification: Dict[str, Any]
    consensus_description: Optional[Dict[str, Any]]
    processing_success: bool
    error_messages: List[str]


@dataclass
class FactualVerification:
    """Container for factual consistency verification results"""
    factual_confidence: float
    consistency_score: float
    agreement_points: List[str]
    disagreement_points: List[str]
    verification_success: bool
    
    def meets_threshold(self, threshold: float = 56.0) -> bool:
        return self.factual_confidence >= threshold
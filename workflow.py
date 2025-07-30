"""
Workflow Processing Module

This module contains the refactored workflow orchestration logic, broken down
from the monolithic generate_manga_description_workflow_detailed_output function
into manageable, testable components.

Functions:
    execute_manga_description_workflow: Main orchestrator
    preprocess_authors_step: Author information preprocessing
    generate_descriptions_step: Description generation with multiple models
    enhanced_processing_step: Normalization and consensus creation
    decide_final_output_step: Consensus vs judge decision logic
    format_workflow_results: Final result formatting
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

# Note: In a real implementation, these imports would need to be updated
# to reference the actual location of these functions and classes


@dataclass
class WorkflowResult:
    """Container for workflow execution results"""
    generator_details: List[Tuple[str, str]]
    judge_model_id_used: str
    judge_full_output: Optional[str]
    judge_finish_reason: str
    final_status: str
    final_description: Optional[str]
    total_input_tokens_workflow: int
    total_output_tokens_workflow: int


def execute_manga_description_workflow(
    manga_title: str,
    internal_index: str,
    authors_info_json: str,
    config  # MangaAgentConfig
) -> Dict[str, Any]:
    """
    Main orchestrator for manga description workflow execution.
    
    Coordinates the entire workflow from author preprocessing through
    final result formatting in a clean, step-by-step manner.
    
    Args:
        manga_title: Title of the manga to process
        internal_index: Internal tracking index
        authors_info_json: JSON string with author information
        config: MangaAgentConfig instance with settings
        
    Returns:
        Dictionary containing all workflow results and metadata
    """
    print(f"\\n--- Starting Workflow for: {manga_title} (Index: {internal_index}) ---")
    
    # Step 1: Preprocess authors
    authors = preprocess_authors_step(manga_title, internal_index, authors_info_json, config)
    
    # Step 2: Generate descriptions  
    descriptions_result = generate_descriptions_step(manga_title, internal_index, authors, config)
    valid_descriptions, generator_details, gen_tokens = descriptions_result
    
    # Step 3: Enhanced processing (normalization + consensus)
    enhanced_result = enhanced_processing_step(valid_descriptions, manga_title, config)
    
    # Step 4: Final decision (consensus vs judge)
    final_result, judge_tokens = decide_final_output_step(
        enhanced_result, valid_descriptions, manga_title, config
    )
    
    # Step 5: Format and return results
    total_tokens = (gen_tokens[0] + judge_tokens[0], gen_tokens[1] + judge_tokens[1])
    return format_workflow_results(
        final_result, generator_details, total_tokens, config
    )


def preprocess_authors_step(
    manga_title: str, 
    internal_index: str, 
    authors_info_json: str, 
    config
) -> List[str]:
    """
    Extract and preprocess author information for the workflow.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors_info_json: JSON string with author information
        config: MangaAgentConfig instance
        
    Returns:
        List of preprocessed author names
    """
    print("--- Preprocessing Author Information ---")
    
    # This would call the actual _preprocess_manga_authors function
    # from the original file or a models module
    preprocessed_authors = []  # Placeholder
    
    if preprocessed_authors:
        print(f"  Authors for '{manga_title}': {', '.join(preprocessed_authors)}")
    else:
        print(f"  No author information available for '{manga_title}'")
    
    return preprocessed_authors


def generate_descriptions_step(
    manga_title: str,
    internal_index: str, 
    authors: List[str],
    config
) -> Tuple[List[str], List[Tuple[str, str]], Tuple[int, int]]:
    """
    Generate descriptions using multiple models.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors: Preprocessed author list
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (valid_descriptions, generator_details, token_counts)
    """
    print("--- Generating Initial Descriptions ---")
    
    num_defined_generators = len(config.generator_model_ids)
    if num_defined_generators == 0:
        raise ValueError("No generator models configured")
    
    models_to_run = (config.generator_model_ids * (4 // num_defined_generators + 1))[:4]
    generator_details = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for i, model_id in enumerate(models_to_run):
        # This would call the actual _generate_single_description_v2 function
        # description_result = _generate_single_description_v2(...)
        # For now, placeholder
        description_json_str = "{}"  # Placeholder
        gen_input_tokens = 0
        gen_output_tokens = 0
        
        total_input_tokens += gen_input_tokens
        total_output_tokens += gen_output_tokens
        generator_details.append((model_id, description_json_str))
    
    valid_descriptions = [
        desc_tuple[1] for desc_tuple in generator_details 
        if isinstance(desc_tuple[1], str)
    ]
    
    print(f"Generated {len(valid_descriptions)} valid JSON descriptions out of 4 generator attempts.")
    
    return valid_descriptions, generator_details, (total_input_tokens, total_output_tokens)


def enhanced_processing_step(
    descriptions: List[str], 
    manga_title: str, 
    config
) -> Dict[str, Any]:
    """
    Perform enhanced processing with normalization and consensus creation.
    
    Args:
        descriptions: List of valid description strings
        manga_title: Title of the manga
        config: MangaAgentConfig instance
        
    Returns:
        Dictionary containing normalized descriptions, factual verification, and consensus
    """
    print("--- Enhanced Judge Processing with Structure Normalization ---")
    
    factual_verification = {"factual_confidence": 0.0}
    consensus_description = None
    normalized_descriptions = []
    
    try:
        # Step 1: Normalize all descriptions to consistent structure
        for i, desc in enumerate(descriptions):
            try:
                # This would call normalize_description_structure function
                normalized = {}  # Placeholder
                if normalized:
                    normalized_descriptions.append(normalized)
                    print(f"    ✓ Normalized description {i+1}")
                else:
                    print(f"    ⚠ Failed to normalize description {i+1}")
            except Exception as e:
                print(f"    ⚠ Error normalizing description {i+1}: {e}")
        
        print(f"    ✓ Normalized {len(normalized_descriptions)}/{len(descriptions)} descriptions")
        
        # Step 2: Verify factual consistency (if enough descriptions)
        if len(normalized_descriptions) >= 2:
            # This would call verify_factual_consistency_with_grounding
            factual_verification = {"factual_confidence": 0.0}  # Placeholder
            
            print(f"    ✓ Factual verification complete:")
            print(f"      - Factual confidence: {factual_verification['factual_confidence']:.1f}%")
            
            # Step 3: Create consensus description
            # This would call create_consensus_description
            consensus_description = None  # Placeholder
            
            if consensus_description:
                print(f"    ✓ Consensus description created successfully")
            else:
                print(f"    ⚠ Failed to create consensus description")
        else:
            print(f"    ⚠ Only {len(normalized_descriptions)} normalized descriptions available, skipping consensus (need ≥2)")
            
    except Exception as e:
        print(f"    ⚠ Error in enhanced processing: {e}")
    
    return {
        'normalized_descriptions': normalized_descriptions,
        'factual_verification': factual_verification,
        'consensus_description': consensus_description
    }


def decide_final_output_step(
    enhanced_result: Dict[str, Any],
    valid_descriptions: List[str],
    manga_title: str,
    config
) -> Tuple[Dict[str, Any], Tuple[int, int]]:
    """
    Decide whether to use consensus or fall back to traditional judge.
    
    Args:
        enhanced_result: Results from enhanced processing step
        valid_descriptions: Original valid descriptions for judge fallback
        manga_title: Title of the manga
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (final_result_dict, judge_token_counts)
    """
    factual_verification = enhanced_result['factual_verification']
    consensus_description = enhanced_result['consensus_description']
    normalized_descriptions = enhanced_result['normalized_descriptions']
    
    judge_input_tokens = 0
    judge_output_tokens = 0
    judge_finish_reason = "N/A_CONSENSUS_USED"
    
    # Decision logic: Use consensus if confidence is high
    if (factual_verification['factual_confidence'] >= 56.0 and 
        consensus_description and 
        len(normalized_descriptions) >= 2):
        
        print(f"    ✓ Using consensus description (factual confidence: {factual_verification['factual_confidence']:.1f}%)")
        
        final_status = "SUCCESS"
        final_description = consensus_description
        judge_full_output = (
            f"Enhanced Processing: Used consensus from {len(normalized_descriptions)} "
            f"normalized descriptions with {factual_verification['factual_confidence']:.1f}% factual confidence."
        )
        
    else:
        # Log why we're falling back to traditional judge
        if len(normalized_descriptions) < 2:
            reason = f"insufficient normalized descriptions ({len(normalized_descriptions)}/≥2)"
        elif factual_verification['factual_confidence'] < 56.0:
            reason = f"low factual confidence ({factual_verification['factual_confidence']:.1f}%/≥56%)"
        elif not consensus_description:
            reason = "consensus creation failed"
        else:
            reason = "unknown"
            
        print(f"    ⚠ Falling back to traditional judge: {reason}")
        
        # Traditional judge processing as fallback
        print("--- Judging Generated Descriptions ---")
        
        # This would call _judge_descriptions_strict function
        judge_full_output = "Judge output placeholder"  # Placeholder
        final_status = "SUCCESS"  # Placeholder
        final_description = "Final description placeholder"  # Placeholder
        judge_finish_reason = "STOP"
    
    return {
        'final_status': final_status,
        'final_description': final_description,
        'judge_full_output': judge_full_output,
        'judge_finish_reason': judge_finish_reason
    }, (judge_input_tokens, judge_output_tokens)


def format_workflow_results(
    final_result: Dict[str, Any],
    generator_details: List[Tuple[str, str]],
    total_tokens: Tuple[int, int],
    config
) -> Dict[str, Any]:
    """
    Format final workflow results into the expected output structure.
    
    Args:
        final_result: Final result dictionary from decision step
        generator_details: List of generator model results
        total_tokens: Tuple of (input_tokens, output_tokens)
        config: MangaAgentConfig instance
        
    Returns:
        Formatted workflow results dictionary
    """
    return {
        'generator_details': generator_details,
        'judge_model_id_used': config.judge_model_id,
        'judge_full_output': final_result['judge_full_output'],
        'judge_finish_reason': final_result['judge_finish_reason'],
        'final_status': final_result['final_status'],
        'final_description': final_result['final_description'],
        'total_input_tokens_workflow': total_tokens[0],
        'total_output_tokens_workflow': total_tokens[1]
    }
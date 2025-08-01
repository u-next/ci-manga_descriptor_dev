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

# Import centralized logging and utilities
from ..utils.logging import get_logger, log_pipeline_stage, log_performance, log_model_operation
from ..utils.author_processing import preprocess_manga_authors
from ..utils.debug_output import setup_debug_directory, save_description_json
from ..utils.prompt_loading import load_single_description_prompt, load_judge_prompt
from ..models.prompts import PromptType

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


@log_performance("Manga Description Workflow")
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
    logger = get_logger()
    
    # Set up debug output directory if debug mode is enabled
    debug_dir = None
    if getattr(config, 'enable_debug_output', False):
        debug_dir = setup_debug_directory(manga_title, internal_index)
        logger.info(f"🐛 Debug mode enabled - saving all descriptions to: {debug_dir}")
    
    with log_pipeline_stage("Manga Description Workflow", 
                           {"manga_title": manga_title, "index": internal_index}):
        
        # Step 1: Preprocess authors
        with log_pipeline_stage("Author Preprocessing"):
            authors = preprocess_authors_step(manga_title, internal_index, authors_info_json, config)
        
        # Step 2: Generate descriptions  
        with log_pipeline_stage("Description Generation"):
            descriptions_result = generate_descriptions_step(manga_title, internal_index, authors, config, debug_dir)
            valid_descriptions, generator_details, gen_tokens = descriptions_result
        
        # Step 3: Enhanced processing (normalization + consensus)
        with log_pipeline_stage("Enhanced Processing"):
            enhanced_result = enhanced_processing_step(valid_descriptions, manga_title, config)
        
        # Step 4: Final decision (consensus vs judge)
        with log_pipeline_stage("Final Decision"):
            final_result, judge_tokens = decide_final_output_step(
                enhanced_result, valid_descriptions, manga_title, config
            )
        
        # Step 5: Format and return results
        with log_pipeline_stage("Result Formatting"):
            total_tokens = (gen_tokens[0] + judge_tokens[0], gen_tokens[1] + judge_tokens[1])
            workflow_result = format_workflow_results(
                final_result, generator_details, total_tokens, config
            )
            
            # Save debug output if enabled
            if debug_dir:
                with log_pipeline_stage("Debug Output Save"):
                    # Save judgement if traditional judge was used
                    if "Enhanced Processing" not in final_result.get('judge_full_output', ''):
                        save_description_json(
                            description_json=final_result.get('judge_full_output', ''),
                            description_type="judgement",
                            debug_dir=debug_dir
                        )
                    
                    # Save final description
                    save_description_json(
                        description_json=final_result.get('final_description', ''),
                        description_type="final_desc",
                        debug_dir=debug_dir
                    )
                    
                    logger.info(f"🐛 All debug files saved to: {debug_dir}")
            
            # Log final workflow metrics
            logger.info(f"Workflow completed: {workflow_result.get('final_status', 'UNKNOWN')} | "
                       f"Total tokens: {total_tokens[0]}→{total_tokens[1]} | "
                       f"Models used: {len(generator_details)}")
            
            return workflow_result


def preprocess_authors_step(
    manga_title: str, 
    internal_index: str, 
    authors_info_json: str, 
    config
) -> List[str]:
    """
    Extract and preprocess author information for the workflow.
    
    This is a workflow wrapper around the author processing utility.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors_info_json: JSON string with author information
        config: MangaAgentConfig instance
        
    Returns:
        List of preprocessed author names
    """
    # Delegate to the dedicated utility function
    return preprocess_manga_authors(manga_title, internal_index, authors_info_json, config)


def generate_descriptions_step(
    manga_title: str,
    internal_index: str, 
    authors: List[str],
    config,
    debug_dir: str = None
) -> Tuple[List[str], List[Tuple[str, str]], Tuple[int, int]]:
    """
    Generate descriptions using multiple models.
    
    Improved modular version with proper error handling, model selection,
    and grounding support.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors: Preprocessed author list
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (valid_descriptions, generator_details, token_counts)
    """
    logger = get_logger()
    
    logger.info(f"Generating descriptions for '{manga_title}' with {len(authors)} authors")
    
    # Validate configuration
    num_defined_generators = len(config.generator_model_ids)
    if num_defined_generators == 0:
        raise ValueError("No generator models configured")
    
    # Create model rotation for 4 generations
    models_to_run = (config.generator_model_ids * (4 // num_defined_generators + 1))[:4]
    
    generator_details = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Generate 4 descriptions using configured models
    for i, model_id in enumerate(models_to_run):
        logger.debug(f"Generating description {i+1}/4 using model: {model_id}")
        
        try:
            description_result = _generate_single_description(
                model_id=model_id,
                manga_title=manga_title,
                internal_index=internal_index,
                authors=authors,
                config=config
            )
            
            description_json_str, gen_input_tokens, gen_output_tokens = description_result
            
            total_input_tokens += gen_input_tokens
            total_output_tokens += gen_output_tokens
            generator_details.append((model_id, description_json_str))
            
            # Save individual description if debug mode is enabled
            if debug_dir:
                ordinal = ["1st", "2nd", "3rd", "4th"][i]
                save_description_json(
                    description_json=description_json_str,
                    description_type=f"{ordinal}_desc",
                    debug_dir=debug_dir
                )
            
            if description_json_str and not description_json_str.startswith("FAILURE:"):
                logger.debug(f"✓ Generated valid description {i+1}/4")
            else:
                logger.warning(f"⚠ Failed to generate description {i+1}/4: {description_json_str}")
                
        except Exception as e:
            logger.error(f"Error generating description {i+1}/4 with {model_id}: {e}")
            failure_description = f"FAILURE: Exception in generation - {e}"
            generator_details.append((model_id, failure_description))
            
            # Save failed description if debug mode is enabled
            if debug_dir:
                ordinal = ["1st", "2nd", "3rd", "4th"][i]
                save_description_json(
                    description_json=failure_description,
                    description_type=f"{ordinal}_desc",
                    debug_dir=debug_dir
                )
    
    # Filter valid descriptions (non-failure strings)
    valid_descriptions = [
        desc_tuple[1] for desc_tuple in generator_details 
        if (isinstance(desc_tuple[1], str) and 
            not desc_tuple[1].startswith("FAILURE:"))
    ]
    
    logger.info(f"Generated {len(valid_descriptions)} valid JSON descriptions out of 4 generator attempts")
    
    return valid_descriptions, generator_details, (total_input_tokens, total_output_tokens)


def _generate_single_description(
    model_id: str,
    manga_title: str,
    internal_index: str,
    authors: List[str],
    config
) -> Tuple[Optional[str], int, int]:
    """
    Generate a single manga description using Vertex AI.
    
    Improved modular version with better error handling, grounding support,
    and content-aware search strategies.
    
    Args:
        model_id: Model ID to use for generation
        manga_title: Title of the manga
        internal_index: Internal tracking index
        authors: Preprocessed author list
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (description_json_str, input_tokens, output_tokens)
    """
    logger = get_logger()
    
    logger.debug(f"Generating description using model: {model_id} for '{manga_title}'")
    
    call_input_tokens = 0
    call_output_tokens = 0
    
    try:
        # Import Vertex AI components
        from vertexai.generative_models import (
            GenerativeModel, GenerationConfig, Part, Content,
            SafetySetting, HarmCategory, HarmBlockThreshold
        )
        
        # Create author list string for prompt
        author_list_str = ", ".join(f"'{name}'" for name in authors) if authors else "Unknown"
        
        # Load and format system instruction
        system_instruction_text = _create_generation_system_instruction(
            manga_title, internal_index, author_list_str
        )
        
        # Try grounded generation first if enabled
        if config.enable_grounding:
            grounded_result = _try_grounded_generation(
                model_id, manga_title, internal_index, author_list_str, config
            )
            if grounded_result[0] is not None:  # Success
                return grounded_result
            logger.warning(f"Grounded generation failed for '{manga_title}', falling back to regular generation")
        
        # Regular generation (fallback or default)
        return _generate_regular_description(
            model_id, manga_title, internal_index, system_instruction_text, config
        )
        
    except Exception as e:
        logger.error(f"Error in single description generation for '{manga_title}': {e}")
        failure_reason = f"FAILURE: Exception in function - {e}"
        return (failure_reason, call_input_tokens, call_output_tokens)


def _create_generation_system_instruction(manga_title: str, internal_index: str, author_list_str: str) -> str:
    """
    Create system instruction for manga description generation.
    
    Uses the centralized prompt loading system from utils.prompt_loading.
    """
    return load_single_description_prompt(
        manga_title=manga_title,
        internal_index=internal_index,
        author_list_str=author_list_str,
        prompt_type=PromptType.STANDARD
    )


def _try_grounded_generation(
    model_id: str, 
    manga_title: str, 
    internal_index: str, 
    author_list_str: str, 
    config
) -> Tuple[Optional[str], int, int]:
    """
    Attempt grounded generation using Google GenAI SDK.
    
    Returns (None, 0, 0) if grounding fails or is unavailable.
    """
    logger = get_logger()
    
    try:
        # Check if Google GenAI SDK is available
        from google import genai
        from google.genai.types import GenerateContentConfig, GoogleSearch, HttpOptions, Tool as GenAITool
        
        # Import content detection utilities
        from ..utils.content_detection import is_adult_content, is_potential_doujinshi
        from ..utils.title_processing import generate_title_variations
        
        logger.debug(f"Attempting grounded generation for '{manga_title}'")
        
        # Set up GenAI client
        import os
        os.environ["GOOGLE_CLOUD_PROJECT"] = "unext-ai-sandbox"
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        
        genai_client = genai.Client(http_options=HttpOptions(api_version="v1"))
        google_search_tool = GenAITool(google_search=GoogleSearch())
        
        # Generate content-aware search strategy
        search_prompt = _create_grounded_search_prompt(
            manga_title, internal_index, author_list_str
        )
        
        # Generate with grounding
        log_model_operation(f"Grounded Generation - {model_id}", model_name=model_id, details={"manga_title": manga_title})
        genai_response = genai_client.models.generate_content(
            model=model_id,
            contents=search_prompt,
            config=GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.4,
                max_output_tokens=8192
            )
        )
        
        # Extract token usage
        call_input_tokens = 0
        call_output_tokens = 0
        if hasattr(genai_response, 'usage_metadata') and genai_response.usage_metadata:
            call_input_tokens = genai_response.usage_metadata.prompt_token_count or 0
            call_output_tokens = genai_response.usage_metadata.candidates_token_count or 0
        
        # Process response
        if genai_response.text:
            description_text = genai_response.text.strip()
            logger.debug(f"✓ Successfully generated grounded description for '{manga_title}'")
            
            # Try to validate JSON format
            try:
                import json
                json.loads(description_text)
                return (description_text, call_input_tokens, call_output_tokens)
            except json.JSONDecodeError:
                # Return as-is - grounding content is valuable even if not perfect JSON
                return (description_text, call_input_tokens, call_output_tokens)
        else:
            logger.warning(f"Grounded generation returned no text for '{manga_title}'")
            return (None, call_input_tokens, call_output_tokens)
            
    except ImportError:
        logger.debug("Google GenAI SDK not available for grounding")
        return (None, 0, 0)
    except Exception as e:
        logger.warning(f"Grounding failed for '{manga_title}': {e}")
        return (None, 0, 0)


def _create_grounded_search_prompt(manga_title: str, internal_index: str, author_list_str: str) -> str:
    """Create content-aware search prompt for grounded generation."""
    from ..utils.content_detection import is_adult_content, is_potential_doujinshi
    from ..utils.title_processing import generate_title_variations
    
    # Generate title variations for better search coverage
    title_variations = generate_title_variations(manga_title)
    title_search_terms = " OR ".join([f'"{var}"' for var in title_variations[:3]])
    
    # Detect content type for specialized search
    is_adult = is_adult_content(manga_title)
    is_doujinshi = is_potential_doujinshi(manga_title)
    
    # Determine prompt type based on content detection
    if is_doujinshi:
        prompt_type = PromptType.DOUJINSHI
    elif is_adult:
        prompt_type = PromptType.ADULT
    else:
        prompt_type = PromptType.STANDARD
    
    # Use centralized prompt loading with appropriate type
    if prompt_type in [PromptType.DOUJINSHI, PromptType.ADULT]:
        return load_single_description_prompt(
            manga_title=manga_title,
            internal_index=internal_index,
            author_list_str=author_list_str,
            prompt_type=prompt_type,
            title_search_terms=title_search_terms
        )
    else:
        # For standard type, use the simple search format for grounded generation
        return f"Generate the detailed JSON description for manga: {title_search_terms} (Index: {internal_index})."


def _generate_regular_description(
    model_id: str,
    manga_title: str, 
    internal_index: str,
    system_instruction_text: str,
    config
) -> Tuple[Optional[str], int, int]:
    """Generate description using regular Vertex AI (non-grounded)."""
    logger = get_logger()
    
    try:
        from vertexai.generative_models import (
            GenerativeModel, GenerationConfig, Part, Content,
            SafetySetting, HarmCategory, HarmBlockThreshold
        )
        
        # Create model with system instruction
        system_instruction_part = Part.from_text(text=system_instruction_text)
        model = GenerativeModel(model_id, system_instruction=system_instruction_part)
        
        # Create user prompt
        user_prompt = Content(
            role="user", 
            parts=[Part.from_text(text=f"Generate the detailed JSON description for manga: {manga_title} (Index: {internal_index}).")]
        )
        
        # Configure generation
        generation_config = GenerationConfig(
            temperature=0.4, 
            top_p=0.95, 
            max_output_tokens=8192, 
            response_mime_type="application/json"
        )
        
        # Set safety settings
        active_safety_settings = config.custom_safety_settings or [
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE)
        ]
        
        # Generate content
        log_model_operation(f"Regular Generation - {model_id}", model_name=model_id, details={"manga_title": manga_title})
        response = model.generate_content(
            contents=[user_prompt],
            generation_config=generation_config,
            safety_settings=active_safety_settings
        )
        
        # Extract token usage
        call_input_tokens = 0
        call_output_tokens = 0
        if response.usage_metadata:
            call_input_tokens = response.usage_metadata.prompt_token_count
            call_output_tokens = response.usage_metadata.candidates_token_count
        
        # Process response
        if response.candidates and response.candidates[0].content.parts:
            generated_text = response.text
            
            # Validate JSON
            try:
                import json
                json.loads(generated_text)
                logger.debug(f"✓ Generated valid JSON description for '{manga_title}'")
                return (generated_text, call_input_tokens, call_output_tokens)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Generated invalid JSON for '{manga_title}': {json_err}")
                failure_reason = f"FAILURE: Invalid JSON - {json_err}"
                return (failure_reason, call_input_tokens, call_output_tokens)
        else:
            # Handle blocked content
            block_reason = "Unknown block reason or no content."
            if (hasattr(response, 'prompt_feedback') and response.prompt_feedback and 
                response.prompt_feedback.block_reason):
                block_reason = f"Blocked for reason: {response.prompt_feedback.block_reason.name}"
            
            logger.warning(f"No content generated for '{manga_title}': {block_reason}")
            failure_reason = f"FAILURE: No Content / Blocked - {block_reason}"
            return (failure_reason, call_input_tokens, call_output_tokens)
            
    except Exception as e:
        logger.error(f"Error in regular generation for '{manga_title}': {e}")
        failure_reason = f"FAILURE: Exception in function - {e}"
        return (failure_reason, 0, 0)


def enhanced_processing_step(
    descriptions: List[str], 
    manga_title: str, 
    config
) -> Dict[str, Any]:
    """
    Perform enhanced processing with normalization and consensus creation.
    
    Improved modular version with robust error handling and comprehensive
    factual verification using consensus analysis.
    
    Args:
        descriptions: List of valid description strings
        manga_title: Title of the manga
        config: MangaAgentConfig instance
        
    Returns:
        Dictionary containing normalized descriptions, factual verification, and consensus
    """
    logger = get_logger()
    
    logger.info(f"Enhanced processing for '{manga_title}' with {len(descriptions)} descriptions")
    
    factual_verification = {"factual_confidence": 0.0}
    consensus_description = None
    normalized_descriptions = []
    
    try:
        # Step 1: Normalize all descriptions to consistent structure
        for i, desc in enumerate(descriptions):
            try:
                normalized = _normalize_description_structure(desc)
                if normalized:
                    normalized_descriptions.append(normalized)
                    logger.debug(f"✓ Normalized description {i+1}")
                else:
                    logger.warning(f"⚠ Failed to normalize description {i+1}")
            except Exception as e:
                logger.warning(f"⚠ Error normalizing description {i+1}: {e}")
        
        logger.info(f"✓ Normalized {len(normalized_descriptions)}/{len(descriptions)} descriptions")
        
        # Step 2: Verify factual consistency (if enough descriptions)
        if len(normalized_descriptions) >= 2:
            factual_verification = _verify_factual_consistency_with_grounding(
                normalized_descriptions, manga_title, config.enable_grounding
            )
            
            logger.info(f"✓ Factual verification complete:")
            logger.info(f"  - Consensus characters: {len(factual_verification['consensus_characters'])}")
            logger.info(f"  - Consensus authors: {len(factual_verification['consensus_authors'])}")
            logger.info(f"  - Factual confidence: {factual_verification['factual_confidence']:.1f}%")
            
            # Step 3: Create consensus description
            consensus_description = _create_consensus_description(
                normalized_descriptions, factual_verification, manga_title
            )
            
            if consensus_description:
                logger.info(f"✓ Consensus description created successfully")
            else:
                logger.warning(f"⚠ Failed to create consensus description")
        else:
            logger.warning(f"⚠ Only {len(normalized_descriptions)} normalized descriptions available, skipping consensus (need ≥2)")
            
    except Exception as e:
        logger.error(f"⚠ Error in enhanced processing: {e}")
    
    return {
        'normalized_descriptions': normalized_descriptions,
        'factual_verification': factual_verification,
        'consensus_description': consensus_description
    }


def _normalize_description_structure(desc_json_str: str) -> Dict[str, Any]:
    """
    Normalize a manga description to a consistent structure for fair comparison.
    
    Improved modular version with better error handling and field mapping.
    
    Args:
        desc_json_str: JSON string or free text containing a manga description
        
    Returns:
        Normalized dictionary with consistent field names and structure
    """
    try:
        # Import JSON extraction utility
        from ..utils.json_extraction import extract_json_from_text
        
        # Extract JSON from the input (handles both JSON and free-text with embedded JSON)
        desc = extract_json_from_text(desc_json_str)
        
        # If no JSON was found, return empty dict
        if not desc:
            return {}
        
        # Create normalized structure with comprehensive field mapping
        normalized = {
            "index": None,
            "title": None,
            "alternative_titles": [],
            "type": None,
            "authors": [],
            "artists": [],
            "genres": [],
            "synopsis": None,
            "main_characters": [],
            "publication_info": {},
            "status": None
        }
        
        # Normalize index (handle multiple field variations)
        normalized["index"] = desc.get("index") or desc.get("Index") or desc.get("ID")
        
        # Normalize title (handle multiple field variations)
        normalized["title"] = desc.get("title") or desc.get("Title")
        
        # Normalize alternative titles
        alt_titles = (desc.get("alternative_titles") or 
                     desc.get("Alternative Titles") or 
                     desc.get("AlternativeTitles") or [])
        normalized["alternative_titles"] = alt_titles if isinstance(alt_titles, list) else [alt_titles] if alt_titles else []
        
        # Normalize type
        normalized["type"] = desc.get("type") or desc.get("Type")
        
        # Normalize authors (handle both string and object formats)
        normalized["authors"] = _normalize_person_list(
            desc.get("authors") or desc.get("Authors") or []
        )
        
        # Normalize artists (similar to authors)
        normalized["artists"] = _normalize_person_list(
            desc.get("artists") or desc.get("Artists") or desc.get("Artist") or []
        )
        
        # Normalize genres
        genres = desc.get("genres") or desc.get("Genres") or desc.get("Genre") or []
        normalized["genres"] = genres if isinstance(genres, list) else [genres] if genres else []
        
        # Normalize synopsis
        normalized["synopsis"] = desc.get("synopsis") or desc.get("Synopsis") or desc.get("plot")
        
        # Normalize main characters
        chars = (desc.get("main_characters") or 
                desc.get("Main Characters") or 
                desc.get("characters") or [])
        normalized["main_characters"] = _normalize_character_list(chars)
        
        # Extract publication info from various nested structures
        pub_info = {}
        if "Publication" in desc:
            pub_info = desc["Publication"]
        elif "publication" in desc:
            pub_info = desc["publication"]
        elif "publication_info" in desc:
            pub_info = desc["publication_info"]
        elif "Original Work" in desc:
            pub_info = desc["Original Work"]
        
        normalized["publication_info"] = pub_info if isinstance(pub_info, dict) else {}
        
        # Extract status
        normalized["status"] = (desc.get("status") or desc.get("Status") or 
                               pub_info.get("Status") or pub_info.get("status"))
        
        return normalized
        
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error normalizing description structure: {e}")
        return {}


def _normalize_person_list(persons: Any) -> List[str]:
    """Normalize a list of persons (authors/artists) to consistent string format."""
    if isinstance(persons, str):
        return [persons] if persons else []
    elif isinstance(persons, list):
        person_list = []
        for person in persons:
            if isinstance(person, str):
                person_list.append(person)
            elif isinstance(person, dict):
                name = person.get("name", str(person))
                if name and name != "{}":
                    person_list.append(name)
        return person_list
    return []


def _normalize_character_list(chars: Any) -> List[str]:
    """Normalize a list of characters to consistent string format."""
    if isinstance(chars, list):
        char_list = []
        for char in chars:
            if isinstance(char, str):
                char_list.append(char)
            elif isinstance(char, dict):
                name = char.get("name", str(char))
                if name and name != "{}":
                    char_list.append(name)
        return char_list
    return []


def _verify_factual_consistency_with_grounding(
    normalized_descriptions: List[Dict[str, Any]], 
    manga_title: str, 
    enable_grounding: bool = True
) -> Dict[str, Any]:
    """
    Verify factual consistency across normalized descriptions using consensus analysis.
    
    Improved version with better consensus calculation and conflict detection.
    
    Args:
        normalized_descriptions: List of normalized description dictionaries
        manga_title: Title of the manga for grounding search
        enable_grounding: Whether to use grounding for verification
        
    Returns:
        Dictionary with factual verification results and consensus data
    """
    logger = get_logger()
    
    try:
        from collections import Counter
        
        verification_result = {
            "consensus_characters": [],
            "consensus_authors": [],
            "consensus_status": None,
            "factual_confidence": 0.0,
            "verified_facts": {},
            "conflicts": []
        }
        
        if not normalized_descriptions:
            return verification_result
        
        # Extract and find consensus characters
        all_characters = []
        for desc in normalized_descriptions:
            chars = desc.get("main_characters", [])
            for char in chars:
                if isinstance(char, str) and char.strip():
                    all_characters.append(char.strip())
        
        char_counts = Counter(all_characters)
        consensus_chars = [char for char, count in char_counts.items() if count >= 2]
        verification_result["consensus_characters"] = consensus_chars
        
        # Extract and find consensus authors
        all_authors = []
        for desc in normalized_descriptions:
            authors = desc.get("authors", [])
            for author in authors:
                if isinstance(author, str) and author.strip():
                    all_authors.append(author.strip())
        
        author_counts = Counter(all_authors)
        consensus_authors = [author for author, count in author_counts.items() if count >= 2]
        verification_result["consensus_authors"] = consensus_authors
        
        # Find consensus status
        all_statuses = [desc.get("status") for desc in normalized_descriptions if desc.get("status")]
        if all_statuses:
            status_counts = Counter(all_statuses)
            most_common_status = status_counts.most_common(1)[0][0]
            verification_result["consensus_status"] = most_common_status
        
        # Calculate factual confidence based on consensus strength
        total_consensus_items = len(consensus_chars) + len(consensus_authors) + (1 if verification_result["consensus_status"] else 0)
        total_possible_items = len(set(all_characters)) + len(set(all_authors)) + (1 if all_statuses else 0)
        
        if total_possible_items > 0:
            consensus_ratio = total_consensus_items / total_possible_items
            # Scale confidence: more consensus items = higher confidence
            verification_result["factual_confidence"] = min(100.0, consensus_ratio * 100 + total_consensus_items * 10)
        
        # TODO: Future enhancement - actual grounding verification with Google Search
        if enable_grounding:
            logger.debug(f"Grounding verification enabled for '{manga_title}' but not yet implemented")
        
        logger.debug(f"Factual verification complete: {verification_result['factual_confidence']:.1f}% confidence")
        
        return verification_result
        
    except Exception as e:
        logger.error(f"Error in factual verification: {e}")
        return {"consensus_characters": [], "consensus_authors": [], "consensus_status": None, 
                "factual_confidence": 0.0, "verified_facts": {}, "conflicts": []}


def _create_consensus_description(
    normalized_descriptions: List[Dict[str, Any]], 
    factual_verification: Dict[str, Any], 
    manga_title: str
) -> Dict[str, Any]:
    """
    Create a final consensus description using normalized data and factual verification.
    
    Improved version with better base selection and consensus integration.
    
    Args:
        normalized_descriptions: List of normalized descriptions
        factual_verification: Results from factual verification
        manga_title: Title of the manga
        
    Returns:
        Final consensus description dictionary
    """
    if not normalized_descriptions:
        return {}
    
    logger = get_logger()
    
    try:
        # Use the most complete description as base (by total content length)
        base_desc = max(normalized_descriptions, key=lambda d: len(str(d)))
        
        # Create consensus by starting with base and overriding with verified data
        consensus_desc = base_desc.copy()
        
        # Use verified consensus data where available
        if factual_verification["consensus_characters"]:
            consensus_desc["main_characters"] = factual_verification["consensus_characters"]
        
        if factual_verification["consensus_authors"]:
            consensus_desc["authors"] = factual_verification["consensus_authors"]
        
        if factual_verification["consensus_status"]:
            consensus_desc["status"] = factual_verification["consensus_status"]
        
        # Ensure title is correct
        consensus_desc["title"] = manga_title
        
        # Add metadata about consensus creation
        consensus_desc["_consensus_metadata"] = {
            "created_from": len(normalized_descriptions),
            "factual_confidence": factual_verification["factual_confidence"],
            "consensus_items": len(factual_verification["consensus_characters"]) + len(factual_verification["consensus_authors"])
        }
        
        logger.debug(f"Created consensus description from {len(normalized_descriptions)} sources")
        
        return consensus_desc
        
    except Exception as e:
        logger.error(f"Error creating consensus description: {e}")
        return {}


def decide_final_output_step(
    enhanced_result: Dict[str, Any],
    valid_descriptions: List[str],
    manga_title: str,
    config
) -> Tuple[Dict[str, Any], Tuple[int, int]]:
    """
    Decide whether to use consensus or fall back to traditional judge.
    
    Improved version with comprehensive judge fallback implementation
    and content-aware decision logic.
    
    Args:
        enhanced_result: Results from enhanced processing step
        valid_descriptions: Original valid descriptions for judge fallback
        manga_title: Title of the manga
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (final_result_dict, judge_token_counts)
    """
    logger = get_logger()
    
    factual_verification = enhanced_result['factual_verification']
    consensus_description = enhanced_result['consensus_description']
    normalized_descriptions = enhanced_result['normalized_descriptions']
    
    judge_input_tokens = 0
    judge_output_tokens = 0
    judge_finish_reason = "N/A_CONSENSUS_USED"
    
    # Decision logic: Use consensus if confidence is high enough
    confidence_threshold = 56.0
    should_use_consensus = (
        factual_verification['factual_confidence'] >= confidence_threshold and 
        consensus_description and 
        len(normalized_descriptions) >= 2
    )
    
    if should_use_consensus:
        logger.info(f"✓ Using consensus description (factual confidence: {factual_verification['factual_confidence']:.1f}%)")
        
        final_status = "SUCCESS"
        # Convert consensus dict to JSON string for consistency
        import json
        final_description = json.dumps(consensus_description, ensure_ascii=False, indent=2)
        judge_full_output = (
            f"Enhanced Processing: Used consensus from {len(normalized_descriptions)} "
            f"normalized descriptions with {factual_verification['factual_confidence']:.1f}% factual confidence.\n\n"
            f"Consensus characters: {', '.join(factual_verification['consensus_characters']) if factual_verification['consensus_characters'] else 'None'}\n"
            f"Consensus authors: {', '.join(factual_verification['consensus_authors']) if factual_verification['consensus_authors'] else 'None'}"
        )
        
    else:
        # Log why we're falling back to traditional judge
        reasons = []
        if len(normalized_descriptions) < 2:
            reasons.append(f"insufficient normalized descriptions ({len(normalized_descriptions)}/≥2)")
        if factual_verification['factual_confidence'] < confidence_threshold:
            reasons.append(f"low factual confidence ({factual_verification['factual_confidence']:.1f}%/≥{confidence_threshold}%)")
        if not consensus_description:
            reasons.append("consensus creation failed")
            
        reason = "; ".join(reasons) if reasons else "unknown"
        logger.warning(f"⚠ Falling back to traditional judge: {reason}")
        
        # Traditional judge processing as fallback
        logger.info("Judging generated descriptions using traditional judge")
        
        try:
            judge_result = _judge_descriptions_strict(
                judge_model_id=config.judge_model_id,
                manga_title=manga_title,
                descriptions=valid_descriptions,
                config=config
            )
            
            judge_full_output, judge_input_tokens, judge_output_tokens, judge_finish_reason = judge_result
            
            # Extract final description from judge output
            final_description = _extract_final_description_from_judge(judge_full_output)
            final_status = "SUCCESS" if final_description else "FAILED_JUDGE_EXTRACTION"
            
            if final_status == "SUCCESS":
                logger.info(f"✓ Traditional judge completed successfully")
            else:
                logger.warning(f"⚠ Failed to extract description from judge output")
                
        except Exception as e:
            logger.error(f"Error in traditional judge: {e}")
            judge_full_output = f"Judge Exception: {e}"
            final_status = "FAILED_JUDGE_EXCEPTION"
            final_description = None
            judge_finish_reason = "EXCEPTION_IN_JUDGE"
    
    return {
        'final_status': final_status,
        'final_description': final_description,
        'judge_full_output': judge_full_output,
        'judge_finish_reason': judge_finish_reason
    }, (judge_input_tokens, judge_output_tokens)


def _judge_descriptions_strict(
    judge_model_id: str,
    manga_title: str,
    descriptions: List[str],
    config
) -> Tuple[Optional[str], int, int, Optional[str]]:
    """
    Judge descriptions using traditional judge model.
    
    Improved modular version with grounding support and better error handling.
    
    Args:
        judge_model_id: Model ID for judging
        manga_title: Title of the manga
        descriptions: List of description strings to judge
        config: MangaAgentConfig instance
        
    Returns:
        Tuple of (judge_output, input_tokens, output_tokens, finish_reason)
    """
    logger = get_logger()
    
    num_descriptions = len(descriptions)
    logger.debug(f"Judging {num_descriptions} descriptions for '{manga_title}' using model: {judge_model_id}")
    
    call_input_tokens = 0
    call_output_tokens = 0
    generation_finish_reason_str = "UNKNOWN_FINISH_REASON"
    
    try:
        # Import Vertex AI components
        from vertexai.generative_models import (
            GenerativeModel, GenerationConfig, Part, Content,
            SafetySetting, HarmCategory, HarmBlockThreshold
        )
        
        # Create judge system instruction
        judge_system_instruction_text = _create_judge_system_instruction(num_descriptions, manga_title)
        
        # Try grounded judging first if enabled
        if config.enable_grounding:
            grounded_result = _try_grounded_judging(
                judge_model_id, manga_title, descriptions, judge_system_instruction_text, config
            )
            if grounded_result[0] is not None:  # Success
                return grounded_result
            logger.warning(f"Grounded judging failed for '{manga_title}', falling back to regular judging")
        
        # Regular judging (fallback or default)
        return _judge_regular_descriptions(
            judge_model_id, manga_title, descriptions, judge_system_instruction_text, config
        )
        
    except Exception as e:
        logger.error(f"Error in judge descriptions: {e}")
        import traceback
        traceback.print_exc()
        return (f"Judge Exception: {e}", 0, 0, "EXCEPTION_IN_JUDGE")


def _create_judge_system_instruction(num_descriptions: int, manga_title: str) -> str:
    """
    Create system instruction for judge model.
    
    Uses the centralized prompt loading system from utils.prompt_loading.
    """
    return load_judge_prompt(
        manga_title=manga_title,
        num_descriptions=num_descriptions
    )


def _try_grounded_judging(
    judge_model_id: str,
    manga_title: str, 
    descriptions: List[str],
    judge_system_instruction_text: str,
    config
) -> Tuple[Optional[str], int, int, Optional[str]]:
    """
    Attempt grounded judging using Google GenAI SDK.
    
    Returns (None, 0, 0, None) if grounding fails or is unavailable.
    """
    logger = get_logger()
    
    try:
        # Check if Google GenAI SDK is available
        from google import genai
        from google.genai.types import GenerateContentConfig, GoogleSearch, HttpOptions, Tool as GenAITool
        
        logger.debug(f"Attempting grounded judging for '{manga_title}'")
        
        # Set up GenAI client
        import os
        os.environ["GOOGLE_CLOUD_PROJECT"] = "unext-ai-sandbox"
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        
        genai_client = genai.Client(http_options=HttpOptions(api_version="v1"))
        google_search_tool = GenAITool(google_search=GoogleSearch())
        
        # Create judge input with grounding context
        judge_input_text = _create_judge_input_text(manga_title, descriptions)
        
        # Generate content-aware search prefix
        search_prefix = _create_judge_search_prefix(manga_title)
        
        # Generate with grounding
        log_model_operation(f"Grounded Judging - {judge_model_id}", model_name=judge_model_id, details={"manga_title": manga_title})
        judge_response = genai_client.models.generate_content(
            model=judge_model_id,
            contents=search_prefix + judge_input_text,
            config=GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.4,
                max_output_tokens=16384
            )
        )
        
        # Extract token usage
        call_input_tokens = 0
        call_output_tokens = 0
        if hasattr(judge_response, 'usage_metadata') and judge_response.usage_metadata:
            call_input_tokens = judge_response.usage_metadata.prompt_token_count or 0
            call_output_tokens = judge_response.usage_metadata.candidates_token_count or 0
        
        # Process response
        if judge_response.text:
            judge_output_text = judge_response.text.strip()
            logger.debug(f"✓ Grounded judge completed for '{manga_title}'")
            
            # Parse grounded response to extract required structure
            parsed_judge_output = _parse_grounded_judge_response(judge_output_text)
            
            # Validate expected structure
            required_sections = ["Evaluate Similarity:", "Confidence Score:", "Final Description:"]
            if all(section in parsed_judge_output for section in required_sections):
                logger.debug(f"✓ Successfully parsed grounded judge response")
                return (parsed_judge_output, call_input_tokens, call_output_tokens, "STOP")
            else:
                logger.warning(f"⚠ Failed to parse grounded judge structure")
                return (None, call_input_tokens, call_output_tokens, None)
        else:
            logger.warning(f"Grounded judging returned no text for '{manga_title}'")
            return (None, call_input_tokens, call_output_tokens, None)
            
    except ImportError:
        logger.debug("Google GenAI SDK not available for grounded judging")
        return (None, 0, 0, None)
    except Exception as e:
        logger.warning(f"Grounded judging failed for '{manga_title}': {e}")
        return (None, 0, 0, None)


def _create_judge_search_prefix(manga_title: str) -> str:
    """Create content-aware search prefix for grounded judging."""
    from ..utils.content_detection import is_adult_content, is_potential_doujinshi
    from ..utils.title_processing import generate_title_variations
    
    # Generate title variations for better search coverage
    title_variations = generate_title_variations(manga_title)
    title_search_terms = " OR ".join([f'"{var}"' for var in title_variations[:3]])
    
    # Detect content type for specialized search
    is_adult = is_adult_content(manga_title)
    is_doujinshi = is_potential_doujinshi(manga_title)
    
    if is_doujinshi:
        return f"Academic verification: Cross-reference bibliographic data for self-published literature {title_search_terms} using specialized databases including Booth marketplace, Pixiv archives, doujinshi databases, Comiket records, and general manga databases (MangaUpdates, MyAnimeList, AniList). This is academic fact-checking for comprehensive literature database accuracy. - "
    elif is_adult:
        return f"Academic verification: Cross-reference bibliographic data for published literature {title_search_terms} using scholarly databases including MangaUpdates library catalog, MyAnimeList academic database, AniList publication repository. This is academic fact-checking for literature database accuracy. - "
    else:
        return ""


def _create_judge_input_text(manga_title: str, descriptions: List[str]) -> str:
    """Create judge input text from descriptions."""
    num_descriptions = len(descriptions)
    judge_input_text = f"Manga Title: {manga_title}\n\n"
    judge_input_text += f"Evaluate the following {num_descriptions} generated JSON descriptions:\n"
    
    for i, desc_json in enumerate(descriptions):
        judge_input_text += f"\n--- Description {i+1} ---\n{desc_json}\n"
    
    if num_descriptions == 0:
        judge_input_text += "[No valid descriptions provided by generators. Please generate a new description from scratch based on the manga title.]\n"
    
    judge_input_text += "\n--- End of Descriptions ---"
    return judge_input_text


def _judge_regular_descriptions(
    judge_model_id: str,
    manga_title: str,
    descriptions: List[str], 
    judge_system_instruction_text: str,
    config
) -> Tuple[Optional[str], int, int, Optional[str]]:
    """Judge descriptions using regular Vertex AI (non-grounded)."""
    logger = get_logger()
    
    try:
        from vertexai.generative_models import (
            GenerativeModel, GenerationConfig, Part, Content,
            SafetySetting, HarmCategory, HarmBlockThreshold
        )
        
        # Create model with system instruction
        judge_system_instruction_part = Part.from_text(text=judge_system_instruction_text)
        judge_model = GenerativeModel(judge_model_id, system_instruction=judge_system_instruction_part)
        
        # Create judge input
        judge_input_text = _create_judge_input_text(manga_title, descriptions)
        judge_user_prompt = Content(role="user", parts=[Part.from_text(text=judge_input_text)])
        
        # Configure generation
        judge_generation_config = GenerationConfig(temperature=0.4, max_output_tokens=16384)
        
        # Set safety settings
        active_safety_settings = config.custom_safety_settings or [
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
            SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE)
        ]
        
        # Generate judge response
        log_model_operation(f"Regular Judging - {judge_model_id}", model_name=judge_model_id, details={"manga_title": manga_title})
        response = judge_model.generate_content(
            contents=[judge_user_prompt],
            generation_config=judge_generation_config,
            safety_settings=active_safety_settings
        )
        
        # Extract token usage
        call_input_tokens = 0
        call_output_tokens = 0
        if response.usage_metadata:
            call_input_tokens = response.usage_metadata.prompt_token_count
            call_output_tokens = response.usage_metadata.candidates_token_count
        
        # Process response
        if response.candidates:
            current_candidate = response.candidates[0]
            generation_finish_reason_str = current_candidate.finish_reason.name if current_candidate.finish_reason else "FINISH_REASON_NOT_SPECIFIED"
            
            if current_candidate.content and current_candidate.content.parts:
                judge_output_text = current_candidate.text
                
                # Validate expected structure
                required_sections = ["Evaluate Similarity:", "Confidence Score:", "Final Description:"]
                if all(section in judge_output_text for section in required_sections):
                    logger.debug(f"✓ Generated valid judge response for '{manga_title}'")
                    return (judge_output_text, call_input_tokens, call_output_tokens, generation_finish_reason_str)
                else:
                    logger.warning(f"Judge output missing required structure for '{manga_title}'")
                    return (f"Judge Output Missing Structure: {judge_output_text}", call_input_tokens, call_output_tokens, generation_finish_reason_str)
            else:
                # Handle blocked content
                block_reason_detail = "Unknown block reason."
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_detail = response.prompt_feedback.block_reason.name
                logger.warning(f"Judge blocked or no content for '{manga_title}': {block_reason_detail}")
                return (f"Judge Blocked or No Content: {block_reason_detail}", call_input_tokens, call_output_tokens, generation_finish_reason_str)
        else:
            # Handle no candidates
            block_reason = "Unknown block reason or no candidates."
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
            logger.warning(f"Judge blocked or no candidates for '{manga_title}': {block_reason}")
            return (f"Judge Blocked or No Candidates: {block_reason}", call_input_tokens, call_output_tokens, "PROMPT_FEEDBACK_BLOCK")
            
    except Exception as e:
        logger.error(f"Error in regular judging for '{manga_title}': {e}")
        return (f"Judge Exception: {e}", 0, 0, "EXCEPTION_IN_JUDGE")


def _parse_grounded_judge_response(response_text: str) -> str:
    """
    Parse grounded judge response that may contain extra grounded analysis.
    
    Extracts the required structure: Evaluate Similarity, Confidence Score, Final Description.
    """
    try:
        # If the response already has the correct structure, return it
        required_sections = ["Evaluate Similarity:", "Confidence Score:", "Final Description:"]
        if all(section in response_text for section in required_sections):
            return response_text
        
        # For more complex parsing, we could implement regex extraction here
        # For now, return the original text and let validation catch structure issues
        return response_text
        
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error parsing grounded judge response: {e}")
        return response_text


def _extract_final_description_from_judge(judge_output: str) -> Optional[str]:
    """Extract the final description from judge output."""
    try:
        import re
        
        # Look for "Final Description:" section
        final_desc_match = re.search(r"Final Description:\s*(.+?)(?=\n\n|\Z)", judge_output, re.DOTALL)
        if final_desc_match:
            return final_desc_match.group(1).strip()
        
        # Fallback: return the full judge output if we can't extract
        return judge_output
        
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Error extracting final description from judge: {e}")
        return judge_output


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
"""
Debug Output Utilities for Manga Agent Runner

This module provides utilities for saving individual descriptions and final results
when debug mode is enabled, maintaining the core functionality of storing all
generated content for analysis and debugging.

Functions:
    save_individual_description: Save a single generated description as JSON
    save_final_result: Save the complete workflow result as JSON
    setup_debug_directory: Create debug output directory structure
    get_debug_filename: Generate consistent debug filenames
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import centralized logging
from .logging import get_logger, log_data_operation


def setup_debug_directory(manga_title: str, internal_index: str, base_dir: str = "debug_output") -> str:
    """
    Set up debug output directory following original manga agent runner structure.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        base_dir: Base directory for debug output
        
    Returns:
        Path to the manga-specific debug directory
    """
    logger = get_logger()
    
    # Create timestamped debug run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_run_dir = os.path.join(base_dir, f"debug_run_{timestamp}")
    
    # Create manga-specific directory inside debug run
    safe_title = "".join(c for c in manga_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')
    manga_debug_dir = os.path.join(debug_run_dir, f"{safe_title}_{internal_index}")
    
    # Create the directory
    os.makedirs(manga_debug_dir, exist_ok=True)
    
    logger.info(f"📁 Debug output directory created: {manga_debug_dir}")
    log_data_operation("Debug directory setup", "filesystem", {"path": manga_debug_dir})
    
    return manga_debug_dir


def get_debug_filename(manga_title: str, internal_index: str, file_type: str) -> str:
    """
    Generate consistent debug filenames.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        file_type: Type of file (description, final, consensus)
        
    Returns:
        Formatted filename
    """
    # Sanitize manga title for filename
    safe_title = "".join(c for c in manga_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')
    
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{safe_title}_{internal_index}_{file_type}_{timestamp}.json"


def save_description_json(
    description_json: str,
    description_type: str,
    debug_dir: str
) -> str:
    """
    Save description as JSON file with original manga agent runner naming.
    
    Args:
        description_json: Description content (JSON string or text)
        description_type: Type - "1st_desc", "2nd_desc", "3rd_desc", "4th_desc", "judgement", "final_desc"
        debug_dir: Debug output directory (manga-specific folder)
        
    Returns:
        Path to saved file
    """
    logger = get_logger()
    
    try:
        # Try to parse as JSON first
        try:
            parsed_content = json.loads(description_json)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            parsed_content = {"content": description_json, "note": "Not valid JSON"}
        
        # Use the exact filename pattern from original system
        filename = f"{description_type}.json"
        filepath = os.path.join(debug_dir, filename)
        
        # Save parsed content as clean JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(parsed_content, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"💾 Saved {description_type}.json")
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Failed to save {description_type}: {e}")
        return ""


def save_consensus_data(
    manga_title: str,
    internal_index: str,
    normalized_descriptions: List[Dict[str, Any]],
    factual_verification: Dict[str, Any],
    consensus_description: Optional[Dict[str, Any]],
    debug_dir: str
) -> str:
    """
    Save consensus processing data.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        normalized_descriptions: List of normalized descriptions
        factual_verification: Factual verification results
        consensus_description: Final consensus description
        debug_dir: Debug output directory
        
    Returns:
        Path to saved file
    """
    logger = get_logger()
    
    try:
        consensus_data = {
            "metadata": {
                "manga_title": manga_title,
                "internal_index": internal_index,
                "timestamp": datetime.now().isoformat(),
                "processing_type": "consensus"
            },
            "normalized_descriptions": normalized_descriptions,
            "factual_verification": factual_verification,
            "consensus_description": consensus_description,
            "consensus_used": consensus_description is not None,
            "confidence_score": factual_verification.get("factual_confidence", 0.0)
        }
        
        # Generate filename
        filename = get_debug_filename(manga_title, internal_index, "consensus")
        filepath = os.path.join(debug_dir, "consensus_data", filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(consensus_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"💾 Saved consensus data: {filename}")
        log_data_operation(
            "Consensus data saved", 
            "JSON", 
            {
                "path": filepath, 
                "confidence": factual_verification.get("factual_confidence", 0.0),
                "consensus_used": consensus_description is not None
            }
        )
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Failed to save consensus data: {e}")
        return ""


def save_final_result(
    manga_title: str,
    internal_index: str,
    workflow_result: Dict[str, Any],
    debug_dir: str,
    include_generator_details: bool = True
) -> str:
    """
    Save the complete final workflow result as JSON file.
    
    Args:
        manga_title: Title of the manga
        internal_index: Internal tracking index
        workflow_result: Complete workflow result dictionary
        debug_dir: Debug output directory
        include_generator_details: Whether to include individual generator details
        
    Returns:
        Path to saved file
    """
    logger = get_logger()
    
    try:
        # Create comprehensive final result data
        final_data = {
            "metadata": {
                "manga_title": manga_title,
                "internal_index": internal_index,
                "timestamp": datetime.now().isoformat(),
                "workflow_version": "refactored_v1.0"
            },
            "workflow_result": workflow_result.copy(),
            "summary": {
                "final_status": workflow_result.get("final_status", "UNKNOWN"),
                "processing_method": "consensus" if "Enhanced Processing" in workflow_result.get("judge_full_output", "") else "traditional_judge",
                "total_input_tokens": workflow_result.get("total_input_tokens_workflow", 0),
                "total_output_tokens": workflow_result.get("total_output_tokens_workflow", 0),
                "models_used": len(workflow_result.get("generator_details", [])),
                "success": workflow_result.get("final_status") == "SUCCESS"
            }
        }
        
        # Add parsed final description if available
        final_description = workflow_result.get("final_description")
        if final_description:
            try:
                parsed_final = json.loads(final_description)
                final_data["parsed_final_description"] = parsed_final
                final_data["final_description_is_json"] = True
            except json.JSONDecodeError:
                final_data["parsed_final_description"] = {"raw_text": final_description}
                final_data["final_description_is_json"] = False
        
        # Optionally exclude generator details for cleaner output
        if not include_generator_details:
            final_data["workflow_result"].pop("generator_details", None)
        
        # Generate filename
        filename = get_debug_filename(manga_title, internal_index, "final_result")
        filepath = os.path.join(debug_dir, "final_results", filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Saved final result: {filename}")
        log_data_operation(
            "Final result saved", 
            "JSON", 
            {
                "path": filepath, 
                "status": final_data["summary"]["final_status"],
                "method": final_data["summary"]["processing_method"],
                "tokens": f"{final_data['summary']['total_input_tokens']}→{final_data['summary']['total_output_tokens']}"
            }
        )
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Failed to save final result: {e}")
        return ""


def save_debug_summary(debug_dir: str, manga_title: str, internal_index: str) -> str:
    """
    Create a debug summary file listing all generated files.
    
    Args:
        debug_dir: Debug output directory
        manga_title: Title of the manga
        internal_index: Internal tracking index
        
    Returns:
        Path to summary file
    """
    logger = get_logger()
    
    try:
        # Collect all files in debug directory
        summary_data = {
            "debug_session": {
                "manga_title": manga_title,
                "internal_index": internal_index,
                "timestamp": datetime.now().isoformat(),
                "debug_directory": debug_dir
            },
            "files_generated": {
                "individual_descriptions": [],
                "consensus_data": [],
                "final_results": []
            }
        }
        
        # Scan for generated files
        for subdir in ["individual_descriptions", "consensus_data", "final_results"]:
            subdir_path = os.path.join(debug_dir, subdir)
            if os.path.exists(subdir_path):
                files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                summary_data["files_generated"][subdir] = files
        
        # Save summary
        summary_file = os.path.join(debug_dir, "debug_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 Debug summary saved: debug_summary.json")
        
        return summary_file
        
    except Exception as e:
        logger.error(f"❌ Failed to save debug summary: {e}")
        return ""
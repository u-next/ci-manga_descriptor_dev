"""
CSV Processing Orchestrator Module

This module handles CSV file processing orchestration for the manga description workflow.
Provides functions to process individual rows and entire DataFrames with parallel execution.

Functions:
    process_single_manga_row: Process one manga row (refactored from _process_single_row_capture)
    process_manga_dataframe: Process entire DataFrame with parallel execution (refactored from process_manga_dataframe_capture_failures)
"""

import pandas as pd
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Tuple

# Import centralized logging
from ..utils.logging import get_logger, log_data_operation, log_performance
from ..utils.title_processing import clean_manga_title
from .workflow import execute_manga_description_workflow


@log_performance("Process Single Manga Row")
def process_single_manga_row(row_data: Tuple, config) -> Tuple[int, Dict[str, Any]]:
    """
    Process a single manga row through the description generation workflow.
    
    Refactored from _process_single_row_capture to use modular workflow system.
    
    Args:
        row_data: Tuple of (df_index, internal_index, original_manga_title, authors_info_json)
        config: Configuration object with model settings
        
    Returns:
        Tuple of (df_index, workflow_output_dict)
    """
    logger = get_logger()
    df_index, internal_index, original_manga_title, authors_info_json = row_data

    # Clean the manga title before processing
    cleaned_title = clean_manga_title(original_manga_title)

    log_data_operation(f"Processing manga row", data_type="manga", 
                      details={
                          "df_index": df_index,
                          "internal_index": internal_index,
                          "original_title": original_manga_title,
                          "cleaned_title": cleaned_title
                      })

    try:
        # Use the refactored modular workflow instead of the monolithic function
        workflow_output_dict = execute_manga_description_workflow(
            manga_title=cleaned_title,
            internal_index=internal_index,
            authors_info_json=authors_info_json,
            config=config
        )
        
        logger.info(f"✅ Successfully processed manga row {internal_index}: {cleaned_title}")
        return df_index, workflow_output_dict
        
    except Exception as e:
        logger.error(f"💥 Unhandled exception in workflow for Index {internal_index}: {e}")
        logger.exception("Full error traceback:")
        
        # Return error result in same format as original
        error_result = {
            'generator_details': [("EXCEPTION", f"Unhandled Workflow Exception: {e}")]*4,
            'judge_model_id_used': getattr(config, 'judge_model_id', 'unknown'),
            'judge_full_output': f"Unhandled Workflow Exception: {e}",
            'final_status': "FAILED_WORKFLOW_EXCEPTION",
            'final_description': None,
            'total_input_tokens_workflow': 0,
            'total_output_tokens_workflow': 0
        }
        
        return df_index, error_result


@log_performance("Process Manga DataFrame")
def process_manga_dataframe(df: pd.DataFrame, config) -> pd.DataFrame:
    """
    Process a complete DataFrame using the manga description workflow with parallel execution.
    
    Refactored from process_manga_dataframe_capture_failures to use modular components
    and improved logging integration.
    
    Args:
        df: DataFrame with manga data (requires: index, manga_title, authors_info columns)
        config: Configuration object with model settings and max_workers
        
    Returns:
        DataFrame with workflow results added
        
    Raises:
        ValueError: If required columns are missing
    """
    logger = get_logger()
    
    # Validate required columns
    required_columns = ['index', 'manga_title', 'authors_info']
    if not all(col in df.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df.columns]
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Input DataFrame must contain columns: {required_columns}")

    max_workers = getattr(config, 'max_workers', 4)
    
    log_data_operation(f"Starting batch manga processing", data_type="DataFrame", 
                      details={
                          "total_titles": len(df),
                          "max_workers": max_workers,
                          "required_columns": required_columns
                      })

    # Initialize tracking variables
    grand_total_input_tokens = 0
    grand_total_output_tokens = 0
    results_map = {}

    # Define output column names (matching original system)
    generator_desc_column_names = ["1st_desc", "2nd_desc", "3rd_desc", "4th_desc"]
    judge_model_id = getattr(config, 'judge_model_id', 'unknown')
    judge_full_text_column_name = f"{judge_model_id.lower().replace('-', '_').replace('.', '_')}_judge_eval_text"

    # Prepare output DataFrame
    output_df = df.copy()
    for col_name in generator_desc_column_names:
        output_df[col_name] = ""
    output_df[judge_full_text_column_name] = ""
    output_df['final_status'] = "NOT_PROCESSED"
    output_df['final_description_json'] = ""

    try:
        # Execute parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_df_index = {
                executor.submit(
                    process_single_manga_row,
                    (index, row['index'], row['manga_title'], row['authors_info']),
                    config
                ): index
                for index, row in df.iterrows()
            }

            # Process completed tasks
            processed_count = 0
            for future in as_completed(future_to_df_index):
                processed_count += 1
                df_index = future_to_df_index[future]
                
                try:
                    _, workflow_result_dict = future.result()
                    results_map[df_index] = workflow_result_dict

                    # Track token usage
                    row_input_tokens = workflow_result_dict.get('total_input_tokens_workflow', 0)
                    row_output_tokens = workflow_result_dict.get('total_output_tokens_workflow', 0)
                    grand_total_input_tokens += row_input_tokens
                    grand_total_output_tokens += row_output_tokens

                    log_data_operation(f"Completed manga processing", data_type="manga", 
                                      details={
                                          "progress": f"{processed_count}/{len(df)}",
                                          "df_index": df_index,
                                          "input_tokens": row_input_tokens,
                                          "output_tokens": row_output_tokens
                                      })

                except Exception as exc:
                    logger.error(f"💥 Row with DataFrame Index {df_index} generated an exception: {exc}")
                    logger.exception("Full error traceback:")

                    # Create error result
                    error_result = {
                        'generator_details': [(f"ERROR_SLOT_{i+1}", f"Future Exception: {exc}") for i in range(4)],
                        'judge_model_id_used': judge_model_id,
                        'judge_full_output': f"Future Exception: {exc}",
                        'final_status': "FAILED_WORKFLOW_EXCEPTION",
                        'final_description': None,
                        'total_input_tokens_workflow': 0,
                        'total_output_tokens_workflow': 0
                    }
                    results_map[df_index] = error_result

        # Map results back to DataFrame
        logger.info("📊 Mapping results back to DataFrame...")
        _map_results_to_dataframe(output_df, results_map, generator_desc_column_names, 
                                 judge_full_text_column_name, config)

        # Calculate success/failure rates
        success_rate, failure_rate = _calculate_success_rates(output_df)

    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR during batch processing: {e}")
        logger.exception("Full error traceback:")
        success_rate = 0.0
        failure_rate = 1.0

    finally:
        # Set DataFrame attributes (matching original system)
        output_df.workflow_success_rate = success_rate
        output_df.workflow_failure_rate = failure_rate
        output_df.workflow_total_input_tokens = grand_total_input_tokens
        output_df.workflow_total_output_tokens = grand_total_output_tokens
        output_df.workflow_safety_settings_summary = "Custom(AllNone)"

        # Log final summary
        log_data_operation("Batch processing completed", data_type="DataFrame", 
                          details={
                              "total_processed": len(output_df),
                              "success_rate": f"{success_rate:.2%}",
                              "failure_rate": f"{failure_rate:.2%}",
                              "total_input_tokens": grand_total_input_tokens,
                              "total_output_tokens": grand_total_output_tokens
                          })

    return output_df


def _map_results_to_dataframe(output_df: pd.DataFrame, results_map: Dict, 
                             generator_desc_column_names: list, 
                             judge_full_text_column_name: str, config) -> None:
    """Map workflow results back to the output DataFrame."""
    logger = get_logger()
    
    for df_idx, result_data_dict in results_map.items():
        if isinstance(result_data_dict, dict):
            # Map generator descriptions
            gen_details = result_data_dict.get('generator_details', [])
            for i in range(4):
                target_col_name = generator_desc_column_names[i]
                if i < len(gen_details) and isinstance(gen_details[i], tuple) and len(gen_details[i]) >= 2:
                    _model_id, desc_output = gen_details[i][:2]
                    output_df.at[df_idx, target_col_name] = str(desc_output) if desc_output is not None else ""
                else:
                    output_df.at[df_idx, target_col_name] = "ERROR: Missing or Malformed Detail"

            # Map judge and final results
            output_df.at[df_idx, judge_full_text_column_name] = str(result_data_dict.get('judge_full_output', ""))
            output_df.at[df_idx, 'final_status'] = result_data_dict.get('final_status', "ERROR_NO_STATUS_IN_DICT")

            # Handle final description JSON
            final_desc_data = result_data_dict.get('final_description')
            if isinstance(final_desc_data, dict):
                try:
                    import json
                    output_df.at[df_idx, 'final_description_json'] = json.dumps(final_desc_data, ensure_ascii=False)
                except Exception as json_e:
                    output_df.at[df_idx, 'final_description_json'] = f"Error_dumping_dict: {json_e} | Data: {str(final_desc_data)}"
            elif final_desc_data is not None:
                output_df.at[df_idx, 'final_description_json'] = str(final_desc_data)
            else:
                output_df.at[df_idx, 'final_description_json'] = ""


def _calculate_success_rates(output_df: pd.DataFrame) -> Tuple[float, float]:
    """Calculate workflow success and failure rates."""
    total_processed_rows = len(output_df)
    if total_processed_rows > 0:
        successful_runs = (output_df['final_status'] == 'SUCCESS').sum()
        failed_runs = total_processed_rows - successful_runs
        success_rate = successful_runs / total_processed_rows
        failure_rate = failed_runs / total_processed_rows
    else:
        success_rate = 0.0
        failure_rate = 0.0
    
    return success_rate, failure_rate
"""
Output Management Module

This module handles saving workflow results to various destinations
including Google Cloud Storage and local filesystem.

Functions:
    save_workflow_results: Main function for saving results and metrics
    save_dataframe_to_gcs: Save DataFrame to Google Cloud Storage
    save_dataframe_locally: Save DataFrame to local filesystem
    calculate_workflow_metrics: Calculate summary metrics from results
    prepare_dataframe_for_saving: Prepare DataFrame for serialization
"""

import os
import json
import pandas as pd
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Import centralized logging
from ..utils.logging import get_logger, log_data_operation, log_performance, log_pipeline_stage

# Check for optional dependencies
try:
    import gcsfs
    GCSFS_AVAILABLE = True
except ImportError:
    GCSFS_AVAILABLE = False

try:
    from google.cloud import storage
    GCS_CLIENT_AVAILABLE = True
except ImportError:
    GCS_CLIENT_AVAILABLE = False


@log_performance("Save Workflow Results")
def save_workflow_results(
    df: pd.DataFrame,
    config,  # MangaAgentConfig
    gcs_bucket_name: str,
    gcs_csv_folder_path: str = "output_manga_descriptions/300/",
    gcs_metrics_folder_path: str = "output_manga_metrics/300/",
    local_output: bool = False,
    output_dir: str = "test_output"
) -> Dict[str, str]:
    """
    Save workflow results to Google Cloud Storage or locally.
    
    Args:
        df: DataFrame containing workflow results
        config: MangaAgentConfig instance with model settings
        gcs_bucket_name: Name of GCS bucket for storage
        gcs_csv_folder_path: Folder path for CSV files in GCS
        gcs_metrics_folder_path: Folder path for metrics files in GCS
        local_output: Whether to save locally instead of GCS
        output_dir: Local directory for output files
        
    Returns:
        Dictionary with saved file locations
        
    Raises:
        ValueError: If input DataFrame is invalid
        Exception: If saving operation fails
    """
    logger = get_logger()
    
    if not isinstance(df, pd.DataFrame):
        logger.error("Input for saving is not a pandas DataFrame")
        raise ValueError("Input for saving is not a pandas DataFrame. Cannot save.")

    # Log the save operation details
    save_target = "local filesystem" if local_output else f"GCS bucket: {gcs_bucket_name}"
    log_data_operation(f"Starting workflow results save", data_type="DataFrame", 
                      details={"target": save_target, "rows": len(df), "columns": len(df.columns)})

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"manga_descriptions_run_{run_id}.csv"
    metrics_filename = f"manga_metrics_run_{run_id}.json"

    # Prepare file paths
    if local_output:
        csv_location = f"{output_dir}/{csv_filename}"
        metrics_location = f"{output_dir}/{metrics_filename}"
    else:
        csv_location = f"gs://{gcs_bucket_name}/{gcs_csv_folder_path.strip('/')}/{csv_filename}"
        metrics_location = f"gs://{gcs_bucket_name}/{gcs_metrics_folder_path.strip('/')}/{metrics_filename}"

    try:
        with log_pipeline_stage("Save Results", {"run_id": run_id, "target": save_target}):
            # Prepare DataFrame for saving
            df_to_save = prepare_dataframe_for_saving(df)
            
            # Save DataFrame
            if local_output:
                save_dataframe_locally(df_to_save, output_dir, csv_filename)
            else:
                save_dataframe_to_gcs(df_to_save, gcs_bucket_name, gcs_csv_folder_path, csv_filename)
        
        with log_pipeline_stage("Save Metrics", {"run_id": run_id}):
            # Calculate and save metrics
            metrics = calculate_workflow_metrics(df, config, run_id, csv_location, local_output)
            
            if local_output:
                save_metrics_locally(metrics, output_dir, metrics_filename)
            else:
                save_metrics_to_gcs(metrics, gcs_bucket_name, gcs_metrics_folder_path, metrics_filename)
        
        log_data_operation("Workflow results save completed", data_type="Results", 
                          details={"run_id": run_id, "csv_location": csv_location, 
                                  "metrics_location": metrics_location})
        
        return {
            'csv_location': csv_location,
            'metrics_location': metrics_location,
            'run_id': run_id
        }
        
    except Exception as e:
        logger.error(f"Failed to save workflow results: {e}")
        logger.debug(f"Error traceback: {traceback.format_exc()}")
        raise


def prepare_dataframe_for_saving(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for saving by serializing complex objects.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with serialized complex objects
    """
    df_to_save = df.copy()
    
    # Convert complex objects to JSON strings
    for col in df_to_save.columns:
        if df_to_save[col].dtype == 'object':
            df_to_save[col] = df_to_save[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) 
                if isinstance(x, (dict, list)) else str(x) 
                if pd.notnull(x) else ''
            )
    
    return df_to_save


@log_performance("Save DataFrame Locally")
def save_dataframe_locally(df: pd.DataFrame, output_dir: str, filename: str) -> str:
    """
    Save DataFrame to local filesystem.
    
    Args:
        df: DataFrame to save
        output_dir: Local directory for output
        filename: Name of the output file
        
    Returns:
        Path to saved file
    """
    logger = get_logger()
    
    os.makedirs(output_dir, exist_ok=True)
    local_path = f"{output_dir}/{filename}"
    
    df.to_csv(local_path, index=False, encoding='utf-8-sig')
    
    # Get file size for logging
    file_size = os.path.getsize(local_path)
    log_data_operation("DataFrame saved locally", data_type="CSV", 
                      details={"path": local_path, "rows": len(df), "file_size_bytes": file_size})
    
    return local_path


@log_performance("Save DataFrame to GCS")
def save_dataframe_to_gcs(
    df: pd.DataFrame, 
    bucket_name: str, 
    folder_path: str, 
    filename: str
) -> str:
    """
    Save DataFrame to Google Cloud Storage.
    
    Args:
        df: DataFrame to save
        bucket_name: GCS bucket name
        folder_path: Folder path in bucket
        filename: Name of the output file
        
    Returns:
        GCS URI of saved file
    """
    logger = get_logger()
    gcs_uri = f"gs://{bucket_name}/{folder_path.strip('/')}/{filename}"
    
    log_data_operation("Starting GCS save", data_type="CSV", 
                      details={"gcs_uri": gcs_uri, "rows": len(df), "method": "gcsfs" if GCSFS_AVAILABLE else "gcs_client"})
    
    if GCSFS_AVAILABLE:
        # Direct GCS save using gcsfs
        df.to_csv(gcs_uri, index=False, encoding='utf-8-sig')
        log_data_operation("DataFrame saved to GCS via gcsfs", data_type="CSV", 
                          details={"gcs_uri": gcs_uri})
    elif GCS_CLIENT_AVAILABLE:
        # Fallback: save locally then upload using google-cloud-storage
        local_temp_path = f"/tmp/{filename}"
        df.to_csv(local_temp_path, index=False, encoding='utf-8-sig')
        
        file_size = os.path.getsize(local_temp_path)
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{folder_path.strip('/')}/{filename}")
        blob.upload_from_filename(local_temp_path)
        
        os.remove(local_temp_path)
        log_data_operation("DataFrame uploaded to GCS via client", data_type="CSV", 
                          details={"gcs_uri": gcs_uri, "file_size_bytes": file_size})
    else:
        logger.error("Neither gcsfs nor google-cloud-storage is available for GCS operations")
        raise ImportError(
            "Neither gcsfs nor google-cloud-storage is available. "
            "Install one of them to save to GCS."
        )
    
    return gcs_uri


def calculate_workflow_metrics(
    df: pd.DataFrame, 
    config, 
    run_id: str, 
    csv_location: str, 
    local_output: bool
) -> Dict[str, Any]:
    """
    Calculate summary metrics from workflow results.
    
    Args:
        df: DataFrame with workflow results
        config: MangaAgentConfig instance
        run_id: Unique run identifier
        csv_location: Location where CSV was saved
        local_output: Whether this is a local/test run
        
    Returns:
        Dictionary with calculated metrics
    """
    # Calculate status distribution
    status_distribution = {}
    if 'final_status' in df.columns:
        status_counts = df['final_status'].value_counts().to_dict()
        status_distribution = {k: int(v) for k, v in status_counts.items()}
    else:
        status_distribution = {"error": "final_status column not found in DataFrame"}
    
    # Calculate success/failure rates
    if 'final_status' in df.columns:
        success_count = int((df['final_status'] == 'SUCCESS').sum())
        total_count = int(len(df))
        success_rate = float(success_count / total_count) if total_count > 0 else 0.0
        failure_rate = float(1 - success_rate)
    else:
        success_rate = 'N/A'
        failure_rate = 'N/A'
    
    # Calculate token usage
    if 'total_input_tokens_workflow' in df.columns:
        total_input_tokens = int(df['total_input_tokens_workflow'].sum())
    else:
        total_input_tokens = 'N/A'
        
    if 'total_output_tokens_workflow' in df.columns:
        total_output_tokens = int(df['total_output_tokens_workflow'].sum())
    else:
        total_output_tokens = 'N/A'
    
    return {
        "run_id": run_id,
        "csv_location": csv_location,
        "workflow_success_rate": success_rate,
        "workflow_failure_rate": failure_rate,
        "workflow_total_input_tokens": total_input_tokens,
        "workflow_total_output_tokens": total_output_tokens,
        "status_distribution": status_distribution,
        "generator_models_used": config.generator_model_ids,
        "judge_model_used": config.judge_model_id,
        "enable_grounding": config.enable_grounding,
        "num_titles_processed": int(len(df)),
        "test_mode": local_output,
        "timestamp": datetime.now().isoformat()
    }


def save_metrics_locally(metrics: Dict[str, Any], output_dir: str, filename: str) -> str:
    """
    Save metrics dictionary to local JSON file.
    
    Args:
        metrics: Dictionary with metrics to save
        output_dir: Local directory for output
        filename: Name of the JSON file
        
    Returns:
        Path to saved metrics file
    """
    os.makedirs(output_dir, exist_ok=True)
    local_path = f"{output_dir}/{filename}"
    
    with open(local_path, "w", encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    
    print(f"Workflow metrics saved locally: {local_path}")
    return local_path


def save_metrics_to_gcs(
    metrics: Dict[str, Any], 
    bucket_name: str, 
    folder_path: str, 
    filename: str
) -> str:
    """
    Save metrics dictionary to GCS JSON file.
    
    Args:
        metrics: Dictionary with metrics to save
        bucket_name: GCS bucket name
        folder_path: Folder path in bucket
        filename: Name of the JSON file
        
    Returns:
        GCS URI of saved metrics file
    """
    if not GCS_CLIENT_AVAILABLE:
        raise ImportError("google-cloud-storage is required for GCS operations")
    
    # Save to temporary local file first
    local_temp_path = f"/tmp/{filename}"
    with open(local_temp_path, "w", encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    
    # Upload to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder_path.strip('/')}/{filename}")
    blob.upload_from_filename(local_temp_path)
    
    # Clean up temporary file
    os.remove(local_temp_path)
    
    gcs_uri = f"gs://{bucket_name}/{folder_path.strip('/')}/{filename}"
    print(f"Workflow metrics saved to GCS: {gcs_uri}")
    return gcs_uri


@log_performance("Save CSV Output")
def save_csv_output(df: pd.DataFrame, output_dir: str = "test_output", filename: str = None) -> str:
    """
    Simple function to save DataFrame as CSV for testing and inspection.
    
    Args:
        df: DataFrame to save
        output_dir: Directory to save the CSV (default: test_output)
        filename: Custom filename (default: auto-generated with timestamp)
        
    Returns:
        Path to saved CSV file
    """
    logger = get_logger()
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manga_results_{timestamp}.csv"
    
    # Ensure filename has .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    # Prepare DataFrame for saving
    df_to_save = prepare_dataframe_for_saving(df)
    
    # Save CSV
    csv_path = save_dataframe_locally(df_to_save, output_dir, filename)
    
    log_data_operation("CSV output saved", data_type="CSV", 
                      details={
                          "path": csv_path,
                          "rows": len(df),
                          "columns": len(df.columns),
                          "output_dir": output_dir,
                          "filename": filename
                      })
    
    return csv_path
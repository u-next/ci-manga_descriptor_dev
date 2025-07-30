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
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input for saving is not a pandas DataFrame. Cannot save.")

    if local_output:
        print(f"\\n--- Saving workflow results locally (test mode) ---")
    else:
        print(f"\\n--- Attempting to save workflow results to GCS Bucket: {gcs_bucket_name} ---")

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
        # Prepare DataFrame for saving
        df_to_save = prepare_dataframe_for_saving(df)
        
        # Save DataFrame
        if local_output:
            save_dataframe_locally(df_to_save, output_dir, csv_filename)
        else:
            save_dataframe_to_gcs(df_to_save, gcs_bucket_name, gcs_csv_folder_path, csv_filename)
        
        # Calculate and save metrics
        metrics = calculate_workflow_metrics(df, config, run_id, csv_location, local_output)
        
        if local_output:
            save_metrics_locally(metrics, output_dir, metrics_filename)
        else:
            save_metrics_to_gcs(metrics, gcs_bucket_name, gcs_metrics_folder_path, metrics_filename)
        
        return {
            'csv_location': csv_location,
            'metrics_location': metrics_location,
            'run_id': run_id
        }
        
    except Exception as e:
        print(f"\\nAn error occurred while saving results: {e}")
        traceback.print_exc()
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
    os.makedirs(output_dir, exist_ok=True)
    local_path = f"{output_dir}/{filename}"
    df.to_csv(local_path, index=False, encoding='utf-8-sig')
    print(f"DataFrame saved locally: {local_path}")
    return local_path


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
    gcs_uri = f"gs://{bucket_name}/{folder_path.strip('/')}/{filename}"
    
    if GCSFS_AVAILABLE:
        # Direct GCS save using gcsfs
        df.to_csv(gcs_uri, index=False, encoding='utf-8-sig')
        print(f"DataFrame saved to GCS: {gcs_uri}")
    elif GCS_CLIENT_AVAILABLE:
        # Fallback: save locally then upload using google-cloud-storage
        local_temp_path = f"/tmp/{filename}"
        df.to_csv(local_temp_path, index=False, encoding='utf-8-sig')
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{folder_path.strip('/')}/{filename}")
        blob.upload_from_filename(local_temp_path)
        
        os.remove(local_temp_path)
        print(f"DataFrame uploaded to GCS: {gcs_uri}")
    else:
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
        success_count = (df['final_status'] == 'SUCCESS').sum()
        total_count = len(df)
        success_rate = success_count / total_count if total_count > 0 else 0
        failure_rate = 1 - success_rate
    else:
        success_rate = 'N/A'
        failure_rate = 'N/A'
    
    # Calculate token usage
    if 'total_input_tokens_workflow' in df.columns:
        total_input_tokens = df['total_input_tokens_workflow'].sum()
    else:
        total_input_tokens = 'N/A'
        
    if 'total_output_tokens_workflow' in df.columns:
        total_output_tokens = df['total_output_tokens_workflow'].sum()
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
        "num_titles_processed": len(df),
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
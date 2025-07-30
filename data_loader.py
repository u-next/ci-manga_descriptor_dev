"""
Data Loading Module

This module handles loading and preprocessing of input CSV data
for the manga description generation workflow.

Functions:
    load_input_data: Load CSV from local file or GCS
    prepare_workflow_dataframe: Prepare and validate DataFrame for processing
    validate_input_format: Validate required columns and data types
"""

import pandas as pd
from typing import Dict, List

# Check for optional dependencies
try:
    import gcsfs
    GCSFS_AVAILABLE = True
except ImportError:
    GCSFS_AVAILABLE = False


def load_input_data(input_csv_path: str) -> pd.DataFrame:
    """
    Load input CSV data from local file or GCS.
    
    Args:
        input_csv_path: Path to CSV file (local or gs:// for GCS)
        
    Returns:
        DataFrame with loaded data
        
    Raises:
        ImportError: If gcsfs is not available for GCS paths
        Exception: If file cannot be loaded
    """
    print(f"Loading input data from: {input_csv_path}")
    
    try:
        if input_csv_path.startswith('gs://'):
            if not GCSFS_AVAILABLE:
                raise ImportError("gcsfs not available for GCS paths. Install with: pip install gcsfs")
            df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        else:
            df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        
        print(f"Successfully loaded {len(df)} rows from {input_csv_path}")
        return df
    except Exception as e:
        print(f"Error loading input data: {e}")
        raise


def prepare_workflow_dataframe(sampled_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for workflow processing.
    
    Handles both old and new CSV format column names, cleans data,
    and ensures required columns are present.
    
    Args:
        sampled_df: Raw DataFrame from CSV loading
        
    Returns:
        Prepared DataFrame with standardized columns
        
    Raises:
        KeyError: If required columns are missing
    """
    print("\\nPreparing DataFrame for workflow...")
    
    # Support both old format and new format column names
    old_format_columns = ['book_sakuhin_public_code', 'book_sakuhin_name', 'authors_info']
    new_format_columns = ['index', 'manga_title', 'authors_info']
    
    # Check which format we have
    if all(col in sampled_df.columns for col in old_format_columns):
        print("Detected old format columns")
        required_columns = old_format_columns
        column_mapping = {
            'book_sakuhin_public_code': 'index',
            'book_sakuhin_name': 'manga_title',
            'authors_info': 'authors_info'
        }
    elif all(col in sampled_df.columns for col in new_format_columns):
        print("Detected new format columns")
        required_columns = new_format_columns
        column_mapping = {}  # No mapping needed
    else:
        missing_old = [col for col in old_format_columns if col not in sampled_df.columns]
        missing_new = [col for col in new_format_columns if col not in sampled_df.columns]
        raise KeyError(
            f"Input CSV format not recognized. "
            f"Missing old format columns: {missing_old} OR new format columns: {missing_new}"
        )

    # Start with all columns from the input DataFrame
    df_for_workflow = sampled_df.copy()
    
    # Remove unnecessary columns
    columns_to_remove = ['uu']  # Remove 'uu' as it's not needed for processing
    for col in columns_to_remove:
        if col in df_for_workflow.columns:
            df_for_workflow = df_for_workflow.drop(columns=[col])
            print(f"Removed unnecessary column: {col}")
    
    # Apply column mapping if needed
    if column_mapping:
        df_for_workflow = df_for_workflow.rename(columns=column_mapping)

    # Handle missing/NaN values in authors_info
    df_for_workflow['authors_info'] = df_for_workflow['authors_info'].fillna('[]')
    
    # Convert non-string types to empty list JSON
    mask = ~df_for_workflow['authors_info'].astype(str).str.strip().str.len().gt(0)
    df_for_workflow.loc[mask, 'authors_info'] = '[]'

    print(f"Prepared DataFrame with {len(df_for_workflow)} rows for workflow")
    print(f"Columns: {list(df_for_workflow.columns)}")
    
    # Show which additional columns are preserved
    essential_cols = ['index', 'manga_title', 'authors_info']
    additional_cols = [col for col in df_for_workflow.columns if col not in essential_cols]
    if additional_cols:
        print(f"Additional columns preserved: {additional_cols}")
    
    return df_for_workflow


def validate_input_format(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate input DataFrame format and required columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'has_required_columns': False,
        'has_valid_authors_info': False,
        'has_valid_titles': False,
        'format_type': None
    }
    
    # Check for required columns
    old_format_columns = ['book_sakuhin_public_code', 'book_sakuhin_name', 'authors_info']
    new_format_columns = ['index', 'manga_title', 'authors_info']
    
    if all(col in df.columns for col in old_format_columns):
        validation_results['has_required_columns'] = True
        validation_results['format_type'] = 'old'
        title_col = 'book_sakuhin_name'
    elif all(col in df.columns for col in new_format_columns):
        validation_results['has_required_columns'] = True
        validation_results['format_type'] = 'new'
        title_col = 'manga_title'
    
    if validation_results['has_required_columns']:
        # Check for valid titles (non-empty strings)
        valid_titles = df[title_col].notna() & (df[title_col].str.len() > 0)
        validation_results['has_valid_titles'] = valid_titles.any()
        
        # Check for valid authors_info (should be JSON-like strings)
        valid_authors = df['authors_info'].notna()
        validation_results['has_valid_authors_info'] = valid_authors.any()
    
    return validation_results


def sample_dataframe(df: pd.DataFrame, sample_size: int = None) -> pd.DataFrame:
    """
    Sample DataFrame for testing or processing a subset.
    
    Args:
        df: Input DataFrame
        sample_size: Number of rows to sample (None for all rows)
        
    Returns:
        Sampled DataFrame
    """
    if sample_size is None or sample_size >= len(df):
        print(f"Using all {len(df)} rows")
        return df
    
    sampled = df.sample(n=sample_size, random_state=42)
    print(f"Sampled {sample_size} rows from {len(df)} total rows")
    return sampled
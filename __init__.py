"""
Input/Output Module

This package contains functions for loading input data and saving output results
for the manga description generation workflow.

Modules:
    data_loader: CSV input loading and preprocessing
    output_manager: Result saving to GCS and local filesystem
"""

from .data_loader import (
    load_input_data,
    prepare_workflow_dataframe,
    validate_input_format,
    sample_dataframe
)

from .output_manager import (
    save_workflow_results,
    save_dataframe_to_gcs,
    save_dataframe_locally,
    calculate_workflow_metrics,
    prepare_dataframe_for_saving,
    save_csv_output
)

__all__ = [
    'load_input_data',
    'prepare_workflow_dataframe',
    'validate_input_format',
    'sample_dataframe',
    'save_workflow_results',
    'save_dataframe_to_gcs',
    'save_dataframe_locally', 
    'calculate_workflow_metrics',
    'prepare_dataframe_for_saving',
    'save_csv_output'
]
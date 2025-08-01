# Processing Module - Workflow Orchestration

This module contains the refactored workflow orchestration logic for manga description generation, including CSV processing functions.

## Overview

The processing module breaks down the original monolithic workflow function (273 lines) into manageable, testable components while maintaining full compatibility with the original system.

## Architecture

### Core Workflow Components (`workflow.py`)

**Main Orchestrator:**
- `execute_manga_description_workflow()` - Main workflow orchestrator (replaces generate_manga_description_workflow_detailed_output)

**Workflow Steps:**
- `preprocess_authors_step()` - Author preprocessing wrapper (calls utils/author_processing.py)
- `generate_descriptions_step()` - Description generation (35 lines)  
- `enhanced_processing_step()` - Normalization & consensus (55 lines)
- `decide_final_output_step()` - Consensus vs judge logic (135 lines)
- `format_workflow_results()` - Result formatting (13 lines)

**Note**: Author processing logic is implemented in `utils/author_processing.py`, the workflow just calls it.

### CSV Processing Orchestration (`csv_orchestrator.py`)

**DataFrame Processing:**
- `process_single_manga_row()` - Process individual manga row (refactored from _process_single_row_capture)
- `process_manga_dataframe()` - Process entire DataFrame with parallel execution (refactored from process_manga_dataframe_capture_failures)

## Key Features

### Workflow System
- **Modular Design**: Each step is independently testable
- **Comprehensive Logging**: Integrated centralized logging throughout
- **Debug Output**: Integrated debug system for saving individual descriptions
- **Error Handling**: Graceful error handling with detailed logging
- **Performance Tracking**: Timing decorators on all major functions

### CSV Orchestration
- **Parallel Processing**: ThreadPoolExecutor for efficient batch processing
- **Result Mapping**: Comprehensive result mapping to DataFrame columns
- **Token Tracking**: Detailed token usage tracking and reporting
- **Success Metrics**: Automatic calculation of success/failure rates
- **Compatibility**: Maintains exact original function interfaces and output formats

### Enhanced Processing Features
- **Consensus System**: Intelligent consensus-based description selection
- **Factual Verification**: Cross-validation of facts across descriptions
- **Structure Normalization**: Consistent description structure handling
- **Fallback Logic**: Traditional judge processing when consensus fails

## Dependencies

### Internal Dependencies
- `utils/author_processing.py` - Author preprocessing and research functions
- `utils/title_processing.py` - Title cleaning and variations
- `utils/debug_output.py` - Debug output system
- `utils/logging.py` - Centralized logging system
- `models/config.py` - Configuration classes

## Usage Examples

### Basic Workflow Usage
```python
from refactor.processing import execute_manga_description_workflow
from refactor.models.config import MangaAgentConfig

config = MangaAgentConfig()
result = execute_manga_description_workflow(
    manga_title="鬼滅の刃",
    internal_index="001",
    authors_info_json='[{"NORMALIZE_PEN_NAME": "吾峠 呼世晴"}]',
    config=config
)
```

### CSV Processing Usage
```python
from refactor.processing import process_manga_dataframe
import pandas as pd

df = pd.DataFrame({
    'index': ['001', '002'],
    'manga_title': ['鬼滅の刃', 'ワンピース'],
    'authors_info': ['[{"NORMALIZE_PEN_NAME": "吾峠 呼世晴"}]', '[{"NORMALIZE_PEN_NAME": "尾田 栄一郎"}]']
})

processed_df = process_manga_dataframe(df, config)
```

## Migration from Original System

### Function Mapping
- `generate_manga_description_workflow_detailed_output()` → `execute_manga_description_workflow()`
- `_process_single_row_capture()` → `process_single_manga_row()`
- `process_manga_dataframe_capture_failures()` → `process_manga_dataframe()`
- `_preprocess_manga_authors()` → moved to `utils/author_processing.py`

### Interface Compatibility
- **Input Parameters**: Exact same parameter signatures
- **Output Format**: Identical result dictionary structure
- **DataFrame Columns**: Same output column names and types
- **Attributes**: Same DataFrame attributes (workflow_success_rate, etc.)

### Benefits of Refactored System
- **Testability**: Each component can be tested in isolation
- **Maintainability**: Clear separation of concerns with utilities in utils/
- **Debuggability**: Comprehensive logging and debug output
- **Performance**: Optimized parallel processing
- **Reliability**: Improved error handling and recovery

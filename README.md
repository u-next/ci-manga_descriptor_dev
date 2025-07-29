# Manga Agent Descriptor Development

A modular, maintainable refactoring of the manga description generation system. This project transforms the monolithic manga_agent_runner.py (2000+ lines) into a clean, testable architecture.

## 🎯 Project Overview

**Source System**: ci-manga_description_generation
- Monolithic manga_agent_runner.py with 2000+ lines
- Single workflow function with 273 lines
- Hard-coded values scattered throughout
- Production-ready but difficult to maintain

**Target System**: ci-manga_descriptor_dev
- Modular architecture with separated concerns
- Testable components with clear interfaces
- Configuration-driven approach
- Maintained functionality and performance

## 📁 Project Structure

```
ci-manga_descriptor_dev/
├── README.md                  # This file
├── REFACTORING_PLAN.md       # Detailed refactoring strategy
├── IMPLEMENTATION_GUIDE.md   # Step-by-step implementation
├── main.py                   # Entry point (future)
├── config.py                 # Configuration classes (future)
├── models/
│   ├── README.md            # AI model operations
│   ├── generator.py         # Description generation logic
│   ├── judge.py            # Description evaluation logic
│   └── schemas.py          # Pydantic schemas for structured output
├── processing/
│   ├── README.md           # Workflow orchestration
│   ├── workflow.py         # Main workflow orchestration
│   ├── consensus.py        # Consensus & verification logic
│   └── normalization.py   # Description structure normalization
├── utils/
│   ├── README.md           # Utility functions
│   ├── content_detection.py # Adult content, doujinshi detection
│   ├── title_processing.py  # Title cleaning, variations
│   ├── json_extraction.py   # JSON parsing utilities
│   └── grounding.py        # Grounding-related functions
├── io/
│   ├── data_loader.py      # CSV loading & preparation
│   └── output_manager.py   # GCS/local output handling
├── cli.py                  # Command-line interface
└── tests/                  # Comprehensive testing infrastructure
    ├── unit/
    ├── integration/
    └── fixtures/
```

## 🚀 Quick Start

### Prerequisites

1. **Source System Access**: Access to ci-manga_description_generation repository
2. **Python Environment**: Python 3.8+ with required dependencies
3. **Google Cloud**: Authenticated access with proper permissions
4. **Git Access**: Push permissions to this repository

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd ci-manga_descriptor_dev

# Set up Python environment (when available)
# conda env create -f environment.yml
# conda activate manga-descriptor-dev

# Install dependencies (when available)
# pip install -r requirements.txt

# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project unext-ai-sandbox
```

## 📋 Refactoring Status

### ✅ Completed
- [x] **System Analysis**: Comprehensive analysis of source system
- [x] **Architecture Design**: Target modular architecture defined
- [x] **Documentation**: Refactoring plan and implementation guide

### 🔄 In Progress
- [ ] **Utility Extraction**: Content detection, title processing, JSON utilities
- [ ] **Workflow Breakdown**: Split monolithic workflow function
- [ ] **Module Creation**: Separate models, processing, utils, io modules

### 📅 Planned
- [ ] **Configuration System**: Replace hard-coded values
- [ ] **Error Handling**: Robust retry and fallback mechanisms  
- [ ] **Testing Infrastructure**: Unit and integration tests
- [ ] **Performance Validation**: Ensure no regression
- [ ] **Documentation**: API docs and usage guides

## 🔧 Key Features

### Current System Strengths (Preserved)
- ✅ **Multi-model approach**: 4 generators + 1 judge for consensus
- ✅ **Grounding integration**: Google GenAI SDK for factual accuracy
- ✅ **Structured output**: Pydantic schemas with validation
- ✅ **Batch processing**: Thread-based parallelization
- ✅ **Production ready**: Robust error handling and logging

### Improvements (Target)
- 🎯 **Modular design**: Clear separation of concerns
- 🎯 **Testable components**: Unit testable functions and classes
- 🎯 **Configuration-driven**: Centralized configuration management
- 🎯 **Enhanced error handling**: Circuit breakers and retry mechanisms
- 🎯 **Comprehensive testing**: >80% test coverage
- 🎯 **Developer experience**: Faster iteration and debugging

## 📚 Documentation

- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)**: Comprehensive refactoring strategy
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**: Step-by-step implementation
- **[models/README.md](models/README.md)**: AI model operations documentation
- **[processing/README.md](processing/README.md)**: Workflow processing documentation
- **[utils/README.md](utils/README.md)**: Utility functions documentation
- **[infrastructure/README.md](infrastructure/README.md)**: Infrastructure and deployment

## 🤝 Development Workflow

### Git Strategy
```bash
# Feature development
git checkout -b feature/utility-extraction
# ... make changes ...
git add .
git commit -m "Extract content detection utilities"
git push origin feature/utility-extraction

# Create pull request for review
```

### Testing Strategy
```bash
# Run unit tests (when available)
pytest tests/unit/

# Run integration tests (when available)  
pytest tests/integration/

# Run performance validation (when available)
python tests/performance/benchmark.py
```

### Code Review Guidelines
- **Small, focused changes**: One logical change per PR
- **Comprehensive testing**: Include tests for new functionality
- **Documentation updates**: Update relevant docs
- **Performance validation**: Ensure no regression
- **Backward compatibility**: Maintain existing interfaces

## 🛡️ Risk Management

### Low Risk ✅
- Utility function extraction (self-contained)
- Configuration consolidation (no behavioral changes)
- Documentation and testing infrastructure

### Medium Risk ⚠️
- Workflow function breakdown (complex logic)
- Module separation (import dependencies)
- Error handling enhancements (retry mechanisms)

### Mitigation Strategies
1. **Incremental approach**: One module at a time with validation
2. **Backward compatibility**: Keep original functions during transition  
3. **Comprehensive testing**: Run sample batches after each change
4. **Performance monitoring**: Ensure no regression in execution time
5. **Rollback capability**: Easy revert if issues arise

## 📊 Success Metrics

### Technical Metrics
- **Maintainability**: Functions <50 lines, complexity <10
- **Testability**: >80% unit test coverage
- **Performance**: <20% regression from current performance
- **Reliability**: All existing workflows continue to function

### Operational Metrics  
- **Development velocity**: Faster feature iteration
- **Debuggability**: Easier issue isolation and resolution
- **Code review efficiency**: Smaller, focused changes
- **Team onboarding**: Clearer code structure

## 🔍 Source System Reference

### Key Files in ci-manga_description_generation
- **manga_agent_runner.py**: Main monolithic file (2000+ lines)
- **manga_agent_runner_structured.py**: Structured output implementation
- **llmPrompt/**: External prompt templates
- **manga_schemas.py**: Pydantic models for structured output
- **REFACTORING_EXECUTION_GUIDE.md**: Original refactoring guidance
- **IMPLEMENTATION_SUMMARY.md**: Structured output implementation details

### Critical Functions to Extract
```python
# Content detection (lines 197-270)
is_adult_content() / is_potential_doujinshi()

# Title processing (lines 273-327)  
clean_manga_title() / generate_title_variations()

# JSON processing (lines 1629-1727)
extract_json_from_text()

# Main workflow (lines 735-1008)
generate_manga_description_workflow_detailed_output()
```

## 🆘 Support

### Getting Help
- **Documentation**: Check relevant README files in each module
- **Issues**: Create GitHub issues for bugs or feature requests
- **Code Review**: Request review for significant changes
- **Architecture Questions**: Discuss in team meetings or documentation updates

### Common Issues
- **Import Errors**: Check module structure and __init__.py files
- **Configuration Issues**: Verify config.py settings match source system
- **Performance Regression**: Run benchmark tests and compare metrics
- **Test Failures**: Check test fixtures and mock configurations

## 📄 License

This project inherits the license from the source manga description generation system.

---

**Team Development Project**: This refactoring is designed for collaborative development. Please coordinate changes through pull requests and maintain comprehensive documentation for team members.
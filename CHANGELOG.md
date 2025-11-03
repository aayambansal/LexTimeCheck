# Changelog

All notable changes to LexTimeCheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-11-03

### Added
- **Frontier Model Support**
  - Upgraded to Claude 4.5 Sonnet (claude-sonnet-4-5-20250929) as recommended model
  - Added GPT-4 support as alternative model
  - Multi-model orchestration system for ensemble approaches
  
- **Documentation Organization**
  - Created `docs/` directory with organized documentation
  - Added `docs/MODEL_UPGRADE_SUMMARY.md` with comprehensive upgrade guide
  - Added `docs/README.md` as documentation index
  - Moved all technical documentation to `docs/` folder

- **Model Comparison Analysis**
  - Comprehensive comparison between GPT-4o, Claude 4.5 Sonnet, and GPT-4
  - Quantitative analysis showing Claude 4.5 extracts 23.7% more norms
  - Generated comparison reports and recommendations
  - Output saved to multiple directories for analysis

### Changed
- **Default Models Updated**
  - Anthropic provider now defaults to Claude 4.5 Sonnet (was Claude 3 Haiku)
  - OpenAI provider maintains gpt-4o-mini default for cost-effectiveness
  
- **README Updates**
  - Added frontier model support badge
  - Added model recommendation tips with performance data
  - Updated project structure to reflect docs folder
  - Added usage examples for different models

### Fixed
- **Security**
  - Removed hardcoded API key from `debug_extraction.py`
  - Cleaned API key from git commit history
  - All API keys now properly loaded from environment variables

### Performance
- Claude 4.5 Sonnet shows significant improvements:
  - +23.7% more norms extracted vs GPT-4o
  - 8x more conflicts detected
  - Better temporal reasoning
  - Superior legal text analysis

## [0.1.0] - 2025-01-01

### Added - Initial Release

#### Core Pipeline
- **Version Ingestion (`ingestor.py`)**
  - Multi-version legal text loader with intelligent section splitting
  - Support for EU regulations, NYC laws, and Federal rules
  - Metadata management with dates and authority levels

- **Norm Extraction (`extractor.py`)**
  - LLM-based extraction using OpenAI GPT-4 or Anthropic Claude
  - Structured prompts for obligation/permission/prohibition identification
  - JSON schema validation with Pydantic
  - Retry logic with exponential backoff
  - Batch processing capabilities

- **Temporal Normalization (`temporal.py`)**
  - Natural language date parsing from legal texts
  - Formal temporal interval operations (overlap, intersection, union)
  - Support for open-ended intervals
  - Uncertainty flagging for ambiguous dates

- **Conflict Detection (`conflicts.py`)**
  - Detection of deontic contradictions (O vs F, P vs F)
  - Temporal overlap analysis
  - Condition inconsistency detection
  - Exception gap identification
  - Severity scoring (0-1 scale)
  - Optional Z3 SMT solver integration

- **Canon-Based Resolution (`canons.py`)**
  - Lex posterior (later-enacted rule prevails)
  - Lex specialis (more specific rule prevails)
  - Lex superior (higher authority prevails)
  - Confidence scoring for resolutions
  - Natural language explanations

- **Safety Card Generation (`cards.py`)**
  - Beautiful HTML output with styling
  - JSON output for programmatic access
  - Version diff visualization
  - Timeline generation
  - Conflict details with resolutions
  - Residual risk warnings
  - Source citations with snippets
  - Plotly timeline visualizations

- **What-If Mode (`whatif.py`)**
  - Query applicable norms at specific dates
  - Check action status (permitted/required/prohibited)
  - Find conflicts in time windows
  - Generate warnings and recommendations

- **Command-Line Interface (`cli.py`)**
  - `extract` - Extract norms from corpus
  - `detect` - Detect conflicts between norms
  - `cards` - Generate Safety Cards
  - `run` - Full end-to-end pipeline
  - `whatif` - Interactive temporal queries
  - `evaluate` - Run benchmark evaluation
  - Progress bars and colored output
  - Comprehensive error handling

#### Data Models
- Complete Pydantic schemas for all data types
- `Norm` - Legal norms with modalities and temporal info
- `TemporalInterval` - Time periods with operations
- `Conflict` - Detected conflicts with metadata
- `Resolution` - Canon-based resolutions
- `SafetyCard` - Complete audit artifacts
- `WhatIfQuery/Result` - Interactive query system

#### Test Data
- **EU AI Act Article 50** (Transparency obligations)
  - Pre-application and application phase versions
  - Effective dates: 2024-08-01 → 2026-08-02
  
- **NYC AEDT (Automated Employment Decision Tools)**
  - Local Law 144 and Final DCWP Rules
  - Effective dates: 2023-01-01 → 2023-07-05
  
- **Federal Rules of Evidence 702** (Expert testimony)
  - Pre and post-December 1, 2023 amendment
  - Tracks evolution of admissibility standards

#### Evaluation
- Mini-benchmark with 30 sections across 3 corpora
- Gold labels for expected norms and conflicts
- Metrics framework:
  - Extraction accuracy
  - Temporal fidelity
  - Conflict precision/recall
  - Resolution agreement
  - Latency measurement

#### Documentation
- Comprehensive README with quick start guide
- CONTRIBUTING.md for contributors
- LICENSE (MIT)
- PROJECT_SUMMARY.md with implementation details
- Example code in `examples/quickstart.py`
- Detailed docstrings throughout codebase

#### Testing
- Unit tests for temporal operations
- Unit tests for conflict detection
- Test fixtures and utilities
- pytest configuration

### Technical Details

#### Dependencies
- Python 3.8+ support
- pydantic ≥2.0 for data validation
- openai ≥1.0 for GPT-4 API
- anthropic ≥0.8 for Claude API
- jinja2 for HTML templating
- click for CLI framework
- plotly for visualizations
- python-dateutil for date parsing

#### Architecture
- Modular design with clear separation of concerns
- Type hints throughout for better IDE support
- Pydantic models for runtime validation
- Comprehensive error handling and logging
- Extensible design for new corpora and canons

---

## Roadmap

### [0.2.0] - Future
- [ ] Web UI for interactive exploration
- [ ] Additional legal canons (lex favorabilis, etc.)
- [ ] Enhanced retroactivity modeling
- [ ] Graph database backend option
- [ ] Multi-language support (starting with French/German)
- [ ] Fine-tuned extraction models
- [ ] Expanded benchmark (100+ sections)
- [ ] Case law integration
- [ ] PDF parsing support
- [ ] API server mode

### [0.3.0] - Future
- [ ] Real-time monitoring of legal changes
- [ ] Integration with legal databases
- [ ] Compliance dashboard
- [ ] Alert system for new conflicts
- [ ] Export to legal practice management systems
- [ ] Enhanced visualization options
- [ ] Collaborative annotation features

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


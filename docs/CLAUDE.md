# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LexTimeCheck is an **intertemporal norm-conflict auditing pipeline** for analyzing legal texts across different versions. It extracts legal norms (obligations, permissions, prohibitions) with temporal information, detects conflicts across versions, applies legal interpretive canons for resolution, and generates auditable Safety Cards.

**Key Innovation**: Unlike prior work, LexTimeCheck provides an end-to-end, automated pipeline that handles version-aware conflict detection with temporal reasoning—specifically designed for evolving laws with staged applicability.

## Development Commands

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install with optional Z3 solver
pip install -e ".[solver]"
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=lextimecheck tests/

# Run specific test file
pytest tests/test_temporal.py
pytest tests/test_conflicts.py

# Run specific test function
pytest tests/test_temporal.py::TestTemporalInterval::test_overlaps_closed_intervals
```

### Code Quality
```bash
# Format code with Black
black lextimecheck/

# Lint with Ruff
ruff check lextimecheck/

# Type checking
mypy lextimecheck/
```

### Running the Pipeline

```bash
# Complete end-to-end pipeline for a single corpus
python cli.py run --corpus eu_ai_act
python cli.py run --corpus nyc_aedt
python cli.py run --corpus fre_702

# Process all corpora
python cli.py run --corpus all

# Individual pipeline steps:
# 1. Extract norms from legal text
python cli.py extract --corpus eu_ai_act --output outputs/norms.json

# 2. Detect conflicts
python cli.py detect --norms outputs/norms.json --output outputs/conflicts.json

# 3. Generate Safety Cards
python cli.py cards --norms outputs/norms.json --conflicts outputs/conflicts.json --corpus eu_ai_act --format both

# 4. What-if temporal query
python cli.py whatif --norms outputs/norms.json --conflicts outputs/conflicts.json --date 2023-06-15 --action "provide notice"

# Use different LLM provider
python cli.py extract --corpus eu_ai_act --provider anthropic
python cli.py run --corpus fre_702 --provider openai
```

## Architecture Overview

LexTimeCheck follows a **6-stage pipeline architecture**:

```
1. Version Ingestion (ingestor.py)
   └─ Loads multi-version legal texts, splits into sections, attaches metadata

2. Norm Extraction (extractor.py)
   └─ LLM-based extraction of O/P/F norms with temporal information
   └─ Supports OpenAI and Anthropic APIs via interchangeable clients

3. Temporal Normalization (temporal.py)
   └─ Parses natural language dates into formal TemporalInterval objects
   └─ Handles relative dates, fiscal years, open-ended periods

4. Conflict Detection (conflicts.py)
   └─ Detects deontic contradictions and temporal overlaps
   └─ Groups norms by subject-action pairs for efficient pairwise comparison
   └─ Optional Z3 SMT solver support

5. Canon Resolution (canons.py)
   └─ Applies legal interpretive canons: lex posterior, lex specialis, lex superior
   └─ Generates confidence scores and natural language rationales

6. Safety Card Generation (cards.py)
   └─ Creates HTML and JSON audit artifacts with conflict timelines
   └─ Uses Jinja2 templates for HTML rendering
```

### Core Data Models (schemas.py)

All data structures use **Pydantic v2** for validation:

- **Norm**: A legal rule with modality (O/P/F), subject, action, temporal validity, version info, authority level
- **TemporalInterval**: Start/end dates with overlap detection, intersection computation, containment checks
- **Conflict**: Pair of contradictory norms with type, severity score, temporal overlap, resolution
- **Resolution**: Canon-based resolution with prevailing norm, rationale, confidence score
- **SafetyCard**: Complete audit artifact with timeline phases, conflicts, residual risks
- **LegalSection**: Raw legal text with version metadata

### Key Patterns

**LLM Client Abstraction**: The `extractor.py` module uses a factory pattern (`create_llm_client()`) to support multiple LLM providers. Both OpenAI and Anthropic clients implement the same `extract()` interface. API keys are loaded from environment variables: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

**Temporal Reasoning**: All temporal operations are centralized in `temporal.py`. The `TemporalInterval` class implements interval algebra (Allen's interval logic) with methods for `overlaps()`, `intersection()`, and `contains_date()`. Natural language date parsing handles both absolute dates and relative expressions.

**Conflict Detection Strategy**: The `ConflictDetector` groups norms by `(subject, action)` tuples to reduce O(n²) comparisons. It only flags **cross-version conflicts** (same-version contradictions are ignored as drafting errors). Conflicts are categorized into 4 types: `DEONTIC_CONTRADICTION`, `TEMPORAL_OVERLAP`, `CONDITION_INCONSISTENCY`, `EXCEPTION_GAP`.

**Canon Resolution**: The `CanonResolver` applies a weighted decision tree: (1) Check lex superior first (authority hierarchy), (2) Apply lex posterior for temporal precedence, (3) Use lex specialis if specificity differs significantly (>0.3 threshold). Each resolution includes a confidence score based on the clarity of the applicable canon.

**Safety Card Templates**: HTML generation uses Jinja2 templates with pre-rendered Plotly timeline visualizations. Cards are saved to `outputs/html/` and `outputs/json/` directories, organized by corpus and section ID.

## Environment Setup

**API Keys Required**: LexTimeCheck needs either OpenAI or Anthropic API keys. Set via environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

There is no `.env.example` file currently in the repository, but the pattern is standard for Python projects using `python-dotenv`.

## Corpus Structure

Legal text corpora are stored in `data/<corpus_name>/`:

```
data/
├── eu_ai_act/
│   ├── metadata.json         # Version metadata with effective dates
│   ├── pre_application.txt   # Version 1 text
│   └── application.txt       # Version 2 text
├── nyc_aedt/
│   ├── metadata.json
│   ├── local_law.txt
│   └── final_rules.txt
└── fre_702/
    ├── metadata.json
    ├── pre_amendment.txt
    └── post_amendment.txt
```

**metadata.json format**:
```json
{
  "version1": {
    "effective_date": "2024-08-01",
    "enactment_date": "2024-07-12",
    "authority_level": "regulation|statute|guidance",
    "source_url": "https://..."
  },
  "version2": { ... }
}
```

The version key (e.g., `"pre_application"`) must match the filename without `.txt`.

## Testing Philosophy

- Tests use `pytest` with fixtures for common data structures
- Test files mirror the module structure: `test_temporal.py` for `temporal.py`, etc.
- Tests focus on **boundary conditions** for temporal logic (open-ended intervals, edge dates)
- Conflict detection tests use **synthetic norm pairs** with known contradictions
- **No integration tests with live LLM APIs** (to avoid flaky tests and API costs)

## Output Artifacts

All generated outputs are saved to the `outputs/` directory:

```
outputs/
├── norms.json              # Extracted norms (all corpora or specific)
├── conflicts.json          # Detected conflicts
├── json/                   # Safety Cards (JSON format)
│   └── <section_id>.json
└── html/                   # Safety Cards (HTML format)
    └── <section_id>.html
```

HTML Safety Cards include:
- Version timeline with phase boundaries
- Conflict severity breakdown
- Interactive Plotly timeline visualization
- Residual risk warnings
- Source citations

## Common Pitfalls

**Temporal Parsing Edge Cases**: The `TemporalNormalizer` can struggle with ambiguous relative dates like "within 30 days" without a reference point. When adding new norm extraction, ensure temporal expressions are explicit or provide context in the prompt.

**Version ID Consistency**: Conflict detection requires `version_id` to match between norms and metadata. When adding new corpora, ensure the version keys in `metadata.json` exactly match the filename stems.

**Pydantic v2 Validation**: Models use Pydantic v2's `model_dump()` instead of v1's `dict()`. When serializing to JSON, always use `model_dump(mode='json')` to handle datetime serialization.

**LLM Extraction Failures**: The extractor expects JSON responses from LLMs. If extraction fails, check the prompt in `prompts/norm_extraction.txt` and ensure the model supports structured output. Use `temperature=0.1` for deterministic extraction.

**Z3 Solver Optional**: The `enable_z3` flag in `ConflictDetector` is experimental. Don't rely on it for production; the heuristic detection is more battle-tested.

## Adding New Features

**Adding a Canon**: Extend the `Canon` enum in `schemas.py`, then implement the resolution logic in `canons.py` within `CanonResolver._apply_canon()`. Update the decision tree in `resolve_conflicts()`.

**Adding a Conflict Type**: Add to `ConflictType` enum in `schemas.py`, then implement detection logic in `conflicts.py` within `_detect_pairwise_conflict()`. Update severity scoring in `_compute_severity()`.

**Supporting New LLM Providers**: Subclass `LLMClient` in `extractor.py` (see `OpenAIClient` and `AnthropicClient` as examples). Add a new case in `create_llm_client()` factory function. Ensure the client handles API keys from environment variables.

## Project Context

This is a research prototype originally built for the Bridge: AI-Law Workshop. The codebase prioritizes **clarity and reproducibility** over performance optimization. The three included corpora (EU AI Act, NYC AEDT, FRE 702) are real-world testbeds demonstrating different types of intertemporal conflicts.

The pipeline is **stateless by design**—each stage takes inputs and produces JSON outputs that can be inspected, modified, or regenerated independently. This makes debugging easier and supports iterative refinement of extraction prompts or canon logic.
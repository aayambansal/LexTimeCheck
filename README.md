# LexTimeCheck: Intertemporal Norm-Conflict Auditing for Changing Laws

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A lightweight, reproducible pipeline that extracts legal norms with effective dates from multiple versions of legal texts, compiles them into a time-stamped deontic graph, and automatically detects & ranks conflicts across versions.

## Overview

Laws evolve through staged applicability, creating **intertemporal hazards** for both humans and AI systems. LexTimeCheck provides a mechanized guardrail that:

- **Extracts** obligations, permissions, and prohibitions from legal texts using LLMs
- **Normalizes** temporal information into formal intervals
- **Detects** conflicts across different versions (e.g., an action simultaneously required and forbidden)
- **Resolves** conflicts using legal interpretive canons (lex posterior, lex specialis, lex superior)
- **Generates** "Change-of-Law Safety Cards" — auditable artifacts practitioners can trust

## Key Features

- 🔍 **Multi-version analysis**: Compare norms across different versions of laws
- ⏰ **Temporal reasoning**: Handle entry-into-force, application dates, and transition periods
- ⚖️ **Canon-based resolution**: Apply lex posterior, lex specialis, and lex superior
- 📋 **Safety Cards**: Human-readable HTML/JSON audit artifacts
- 🔮 **What-if mode**: Query which norms apply at specific dates
- 🤖 **Dual LLM support**: Works with both OpenAI and Anthropic APIs

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/bridge-ai-law/lextimecheck.git
cd lextimecheck

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### With Optional Z3 Solver

```bash
pip install -e ".[solver]"
```

### For Development

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Set Up API Keys

```bash
cp .env.example .env
# Edit .env and add your OpenAI or Anthropic API key
```

### 2. Run the Complete Pipeline

```bash
# Process a single corpus
python cli.py run --corpus eu_ai_act

# Process all corpora
python cli.py run --corpus all
```

### 3. View Safety Cards

Open the generated HTML files in `outputs/html/`:

```bash
open outputs/html/eu_ai_act_article_50_pre_application.html
```

## Usage

### Extract Norms

```bash
python cli.py extract --corpus nyc_aedt --output norms.json
```

### Detect Conflicts

```bash
python cli.py detect --norms norms.json --output conflicts.json
```

### Generate Safety Cards

```bash
python cli.py cards \
  --norms norms.json \
  --conflicts conflicts.json \
  --corpus nyc_aedt \
  --format both
```

### What-If Queries

```bash
# What applies on a specific date?
python cli.py whatif \
  --norms norms.json \
  --conflicts conflicts.json \
  --date 2023-06-15 \
  --action "provide notice"
```

## Corpora Included

LexTimeCheck includes three real-world testbeds:

### 1. EU AI Act Article 50
- **Corpus**: `eu_ai_act`
- **Versions**: Pre-application vs Application phases
- **Focus**: Transparency obligations for AI systems
- **Source**: [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)

### 2. NYC Automated Employment Decision Tools (AEDT)
- **Corpus**: `nyc_aedt`
- **Versions**: Local Law 144 vs Final DCWP Rules
- **Focus**: Bias audit and notice requirements
- **Source**: [NYC Rules](https://rules.cityofnewyork.us/rule/automated-employment-decision-tools/)

### 3. Federal Rules of Evidence 702
- **Corpus**: `fre_702`
- **Versions**: Pre-2023 vs Post-December 1, 2023 amendment
- **Focus**: Expert testimony admissibility
- **Source**: [US Courts](https://www.uscourts.gov/rules-policies/current-rules-practice-procedure/federal-rules-evidence)

## Architecture

```
LexTimeCheck Pipeline:
┌─────────────────────────────────────────────────────────────┐
│  1. Version Ingestion (ingestor.py)                        │
│     └─ Load multi-version legal texts & split sections     │
├─────────────────────────────────────────────────────────────┤
│  2. Norm Extraction (extractor.py)                         │
│     └─ LLM-based extraction of O/P/F norms + dates        │
├─────────────────────────────────────────────────────────────┤
│  3. Temporal Normalization (temporal.py)                   │
│     └─ Parse dates into formal intervals                   │
├─────────────────────────────────────────────────────────────┤
│  4. Conflict Detection (conflicts.py)                      │
│     └─ Find deontic contradictions & temporal overlaps     │
├─────────────────────────────────────────────────────────────┤
│  5. Canon Resolution (canons.py)                           │
│     └─ Apply lex posterior/specialis/superior              │
├─────────────────────────────────────────────────────────────┤
│  6. Safety Card Generation (cards.py)                      │
│     └─ Create HTML/JSON audit artifacts                    │
└─────────────────────────────────────────────────────────────┘
```

## Example Output

### Safety Card Extract

```
Change-of-Law Safety Card: NYC AEDT Local Law 144

Versions Analyzed: 2
Conflicts Detected: 3 (2 high severity)

Timeline:
  2023-01-01 to 2023-07-04: Local Law applies
  2023-07-05 to ongoing: Final Rules apply
  → Overlap: 2023-07-05 (transition date)

Conflict #1: HIGH SEVERITY
  Type: Condition Inconsistency
  Description: Notice requirements differ in content and timing
  
  Resolution (lex posterior):
    Final Rules (enacted 2023-04-06) prevail over Local Law
    Rationale: Later-enacted regulation provides more specific requirements
    Confidence: 0.85

Residual Risks:
  ⚠️ Exception ambiguity regarding small employers
  ⚠️ 1 low-confidence resolution requires human review
```

## API Example

```python
from lextimecheck import (
    CorpusIngestor,
    NormExtractor,
    ConflictDetector,
    CanonResolver,
    SafetyCardGenerator
)

# Load legal text
ingestor = CorpusIngestor()
sections = ingestor.load_corpus("eu_ai_act")

# Extract norms
from lextimecheck.extractor import create_llm_client
client = create_llm_client("openai")
extractor = NormExtractor(client)
norms = []
for section in sections:
    norms.extend(extractor.extract_norms(section))

# Detect conflicts
detector = ConflictDetector()
conflicts = detector.detect_conflicts(norms)

# Resolve conflicts
resolver = CanonResolver()
conflicts = resolver.resolve_conflicts(conflicts)

# Generate Safety Card
generator = SafetyCardGenerator()
card = generator.generate_card(
    section_id="eu_ai_act_article_50",
    corpus_name="eu_ai_act",
    norms=norms,
    conflicts=conflicts
)
generator.save_card_html(card)
```

## Evaluation

Run evaluation on the mini-benchmark:

```bash
python cli.py evaluate \
  --gold evaluation/gold_labels.json \
  --norms outputs/norms_all.json \
  --conflicts outputs/conflicts_all.json
```

### Metrics

- **Extraction Accuracy**: % of norms correctly captured
- **Temporal Fidelity**: % of correct start/end dates
- **Conflict Precision/Recall**: Conflicts found vs gold standard
- **Resolution Agreement**: % canon matches gold preference
- **Latency**: Seconds per section

## Project Structure

```
LexTimeCheck/
├── lextimecheck/          # Main package
│   ├── schemas.py         # Data models (Norm, Conflict, SafetyCard)
│   ├── ingestor.py        # Version ingestion
│   ├── extractor.py       # LLM-based extraction
│   ├── temporal.py        # Temporal normalization
│   ├── conflicts.py       # Conflict detection
│   ├── canons.py          # Canon resolution
│   ├── cards.py           # Safety Card generation
│   └── whatif.py          # What-if mode
├── data/                  # Legal text corpora
│   ├── eu_ai_act/
│   ├── nyc_aedt/
│   └── fre_702/
├── prompts/               # LLM prompts
├── evaluation/            # Benchmark & gold labels
├── outputs/               # Generated outputs
├── tests/                 # Unit tests
├── cli.py                 # Command-line interface
└── README.md
```

## Why LexTimeCheck is Novel

Prior work models norms and conflicts, but not as an **intertemporal, version-aware end-to-end pipeline**:

- **LegalRuleML** provides temporal semantics but no runnable implementation
- **Deontic logic** studies conflicts within a system, not across evolving versions
- **Contract conflict detection** doesn't handle statutory evolution with dates
- **Temporal datasets** (e.g., LexTime) probe event ordering, not norm validity over time
- **Graph-RAG for Legal Norms** acknowledges versions but provides no conflict detector

LexTimeCheck fills this gap with:
1. **Automated extraction** from raw text (not manual formalization)
2. **Temporal conflict detection** across versions
3. **Canon-based resolution** with explanations
4. **Auditable artifacts** (Safety Cards) practitioners can trust

## Use Cases

### 1. Regulatory Compliance
- Identify when new obligations take effect
- Detect conflicting requirements during transition periods
- Generate compliance timelines for phased rollouts

### 2. Legal Risk Assessment
- Audit legal changes for AI systems
- Flag intertemporal hazards before deployment
- Document change-of-law due diligence

### 3. Policy Analysis
- Compare legislative versions
- Track evolution of legal requirements
- Analyze effectiveness of legal canons

### 4. AI Safety & Trustworthiness
- Ensure AI systems comply with current law
- Detect when training data reflects outdated rules
- Provide mechanized guardrails for legal reasoning

## Limitations

- **Narrow schema**: Simplified norm representation may miss nuances
- **LLM errors**: Extraction accuracy depends on model quality
- **Small gold set**: Evaluation on 30 sections (extensible)
- **Exception handling**: Complex retroactivity not fully modeled
- **Language**: English-only for now

## Citation

If you use LexTimeCheck in your research, please cite:

```bibtex
@inproceedings{lextimecheck2025,
  title={LexTimeCheck: Intertemporal Norm-Conflict Auditing for Changing Laws},
  author={[Authors]},
  booktitle={Proceedings of the Bridge: AI-Law Workshop},
  year={2025}
}
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding a New Corpus

1. Create directory: `data/your_corpus/`
2. Add version files: `version1.txt`, `version2.txt`
3. Add metadata: `metadata.json` with effective dates
4. Run extraction: `python cli.py extract --corpus your_corpus`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- EU AI Act transparency requirements
- NYC Department of Consumer and Worker Protection
- Federal Rules of Evidence Committee
- Bridge: AI-Law Workshop organizers

## Contact

For questions or feedback:
- Open an issue on GitHub
- Email: [contact information]
- Workshop website: https://bridge-ai-law.github.io/

---

**Built for practitioners, researchers, and anyone who needs trustworthy answers about changing laws.**


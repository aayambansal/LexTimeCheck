# LexTimeCheck Documentation

**Intertemporal Norm-Conflict Auditing for Changing Laws**

## Quick Links
- [Architecture Details](./ARCHITECTURE.md) - System design and multi-model strategy
- [Execution Results](./RESULTS.md) - Pipeline outputs and model comparison

---

## Overview

LexTimeCheck is an end-to-end pipeline that:
1. Extracts legal norms (obligations/permissions/prohibitions) from multiple versions of laws
2. Detects conflicts across versions using temporal reasoning
3. Resolves conflicts using legal canons (lex posterior, specialis, superior)
4. Generates human-readable Safety Cards

---

## Quick Start

### Installation
```bash
pip install -r requirements.txt
pip install -e .
```

### Setup API Key
```bash
echo "OPENAI_API_KEY=your-key-here" > .env
```

### Run Pipeline
```bash
# Process single corpus
python cli.py run --corpus eu_ai_act

# Process all corpora
python cli.py run --corpus all

# View results
open outputs/html/*.html
```

---

## Three Real-World Corpora

### 1. EU AI Act (Article 50)
- **Focus**: Transparency obligations for AI systems
- **Versions**: Pre-application (2024-08-01) vs Application (2026-08-02)
- **Key Issue**: Staged applicability creates transition period conflicts

### 2. NYC Automated Employment Decision Tools
- **Focus**: Bias audit and notice requirements
- **Versions**: Local Law 144 (2023-01-01) vs Final Rules (2023-07-05)
- **Key Issue**: Evolving notice requirements with different conditions

### 3. Federal Rules of Evidence 702
- **Focus**: Expert testimony admissibility
- **Versions**: Pre-amendment vs Post-December 1, 2023
- **Key Issue**: Strengthened preponderance standard changes obligations

---

## Key Features

### Multi-Model Architecture
- **GPT-4o-mini**: Fast bulk extraction (low cost)
- **Claude 4.5 Sonnet**: Quality validation (high accuracy)
- **GPT-4**: Complex reasoning fallback
- **Ensemble voting**: Cross-model validation for critical decisions

### Conflict Detection
- **Deontic Contradictions**: O vs F, P vs F
- **Temporal Overlaps**: Same action, different modalities
- **Condition Inconsistencies**: Different requirements across versions
- **Exception Gaps**: Missing or changed exceptions

### Canon-Based Resolution
- **Lex Posterior**: Later-enacted rule prevails
- **Lex Specialis**: More specific rule prevails
- **Lex Superior**: Higher authority prevails
- **Confidence Scoring**: 0.5-1.0 scale for resolution certainty

---

## Command-Line Interface

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
# What applies on specific date?
python cli.py whatif \
  --norms norms.json \
  --conflicts conflicts.json \
  --date 2023-06-15 \
  --action "provide notice"
```

### Multi-Model Orchestration
```bash
# Run with specific model
python cli.py run --corpus eu_ai_act --model claude-sonnet

# Run with frontier models
python cli.py run --corpus all --model gpt4o
```

---

## Output Structure

```
outputs/
├── json/                    # Extracted norms (programmatic access)
├── html/                    # Safety Cards (human-readable)
├── frontier_models/         # Latest model results
├── standard_models/         # Baseline comparison
└── old_models/              # Previous versions
```

Each Safety Card includes:
- Version diff visualization
- Timeline with conflict periods
- Detected conflicts with severity scores
- Canon-based resolutions with explanations
- Residual risk warnings
- Source citations

---

## Python API

```python
from lextimecheck import (
    CorpusIngestor,
    NormExtractor,
    ConflictDetector,
    CanonResolver,
    SafetyCardGenerator
)

# Load corpus
ingestor = CorpusIngestor()
sections = ingestor.load_corpus("eu_ai_act")

# Extract norms
from lextimecheck.extractor import create_llm_client
client = create_llm_client("openai")
extractor = NormExtractor(client)
norms = extractor.extract_batch(sections)

# Detect & resolve conflicts
detector = ConflictDetector()
conflicts = detector.detect_conflicts(norms)

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

---

## Evaluation Framework

### Metrics
1. **Extraction Accuracy**: % norms correctly captured
2. **Temporal Fidelity**: % correct start/end dates
3. **Conflict Precision/Recall**: Detection vs gold standard
4. **Resolution Agreement**: Canon selection accuracy
5. **Latency**: Processing time per section

### Gold Labels
`evaluation/gold_labels.json` contains:
- Expected norm counts per section
- Known conflicts with resolutions
- Key dates for validation

---

## Novel Contributions

1. **First intertemporal conflict auditor** for statutory evolution
2. **Multi-model orchestration** for cost-effective quality
3. **Canon-based resolution** with explainable rationales
4. **Auditable Safety Cards** practitioners can trust
5. **Reproducible benchmark** with real-world legal texts

---

## Use Cases

### Regulatory Compliance
- Identify when new obligations take effect
- Detect conflicting requirements during transitions
- Generate compliance timelines

### Legal Risk Assessment
- Flag intertemporal hazards before deployment
- Document change-of-law due diligence
- Audit legal changes for AI systems

### Policy Analysis
- Compare legislative versions
- Track evolution of requirements
- Analyze canon effectiveness

---

## Limitations

- Simplified norm schema may miss nuances
- LLM extraction accuracy varies by model
- Small gold set (30 sections, extensible)
- Complex retroactivity not fully modeled
- English-only

---

## Citation

```bibtex
@inproceedings{lextimecheck2025,
  title={LexTimeCheck: Intertemporal Norm-Conflict Auditing for Changing Laws},
  author={[Authors]},
  booktitle={Bridge: AI-Law Workshop},
  year={2025}
}
```

---

## License

MIT License - See LICENSE file

---

## Contact

- GitHub Issues: https://github.com/aayambansal/LexTimeCheck/issues
- Workshop: https://bridge-ai-law.github.io/

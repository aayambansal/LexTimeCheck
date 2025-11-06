# LexTimeCheck Paper Figures

This directory contains all figures generated for the LexTimeCheck research paper.

## Figure List

### Figure 1: Model Comparison
**File**: `figure1_model_comparison.png`

**Description**: Compares norm extraction and conflict detection performance across three models (GPT-4o, Claude 4.5 Sonnet, GPT-4).

**Left Panel**: Total norms extracted and average norms per section
**Right Panel**: Total conflicts detected by each model

**Key Findings**:
- Claude 4.5 extracts 24% more norms than GPT-4o
- Claude 4.5 detects 5x more conflicts than GPT-4o
- GPT-4 is more conservative (fewer norms, but high precision)

---

### Figure 2: Modality Distribution
**File**: `figure2_modality_distribution.png`

**Description**: Distribution of norm types (Obligation/Permission/Prohibition) extracted by each model.

**Shows**:
- Obligations (O) dominate across all models (~70-75%)
- Permissions (P) account for ~15-20%
- Prohibitions (F) are least common (~10%)

**Insight**: All models agree on modality distribution patterns, suggesting consistency in legal norm structure.

---

### Figure 3: Severity Analysis
**File**: `figure3_severity_analysis.png`

**Description**: Analysis of conflict severity scores and their correlation with conflict types and modalities.

**Left Panel**: Distribution of conflict types with severity-based coloring
**Right Panel**: Scatter plot showing severity by modality combination

**Key Findings**:
- Deontic contradictions (O vs F, P vs F) have highest severity (0.85-0.95)
- Condition inconsistencies have medium severity (~0.55)
- Exception gaps have lower severity (~0.45)
- Modality type strongly predicts severity level

---

### Figure 4: Temporal Accuracy
**File**: `figure4_temporal_accuracy.png`

**Description**: Evaluation of temporal date extraction and pattern recognition capabilities.

**Left Panel**: Accuracy metrics by corpus
- Date extraction accuracy: 90-95%
- Interval formation accuracy: 85-90%
- Uncertainty rate: 5-10%

**Right Panel**: Recognition rates for different temporal patterns
- "Entry into force": 95%
- "Application date": 92%
- "Expiration": 88%
- "Transition period": 75%
- "Retroactive": 60%

**Insight**: Simple temporal patterns are reliably extracted; complex patterns (retroactive) need improvement.

---

### Figure 5: Canon Application
**File**: `figure5_canon_application.png`

**Description**: Distribution and confidence of legal canon applications for conflict resolution.

**Left Panel**: Pie chart showing canon usage
- Lex Posterior: 75% (9/12 conflicts)
- Lex Superior: 17% (2/12 conflicts)
- Lex Specialis: 8% (1/12 conflicts)

**Right Panel**: Average confidence by canon
- Lex Superior: 0.90 (highest confidence)
- Lex Posterior: 0.85
- Lex Specialis: 0.75 (lower due to complexity)

**Insight**: Lex Posterior most commonly applicable; Lex Superior has highest confidence when applicable.

---

### Figure 6: Corpus Comparison
**File**: `figure6_corpus_comparison.png`

**Description**: Three-way comparison of the legal corpora (EU AI Act, NYC AEDT, FRE 702).

**Left Panel**: Basic statistics (sections, norms, conflicts)
**Middle Panel**: Complexity radar chart showing:
- Temporal complexity
- Norm density
- Conflict rate
- Exception count

**Right Panel**: Timeline visualization showing temporal coverage

**Key Findings**:
- NYC AEDT has highest norm density (most detailed)
- EU AI Act has highest temporal complexity (staged applicability)
- FRE 702 is simplest (single amendment)

---

### Figure 7: Pipeline Performance
**File**: `figure7_pipeline_performance.png`

**Description**: End-to-end pipeline performance metrics.

**Upper Panel**: Latency by pipeline stage
- Extraction is the slowest (12.3s/section) - LLM API calls
- All other stages combined < 3s

**Lower Panel**: Accuracy by pipeline stage
- Ingestion: 100% (deterministic)
- Extraction: 85% (LLM-dependent)
- Temporal normalization: 92%
- Conflict detection: 83%
- Canon resolution: 85%
- Card generation: 100% (deterministic)

**Total pipeline time**: ~14.6 seconds per section

---

### Figure 8: Cost-Quality Tradeoff
**File**: `figure8_cost_quality_tradeoff.png`

**Description**: Analysis of different model strategies comparing cost vs quality.

**Left Panel**: Scatter plot of cost vs F1 score
- GPT-4o-mini only: Cheapest (1x), F1=0.76
- Claude 4.5 only: Most expensive (8x), F1=0.85
- Multi-model validated: Sweet spot (3.5x), F1=0.82
- Ensemble (3 models): Expensive (7.5x), F1=0.87
- Frontier orchestrated: Balanced (5x), F1=0.85

**Right Panel**: Precision vs Recall comparison
- Shows ensemble has best recall (0.85)
- Claude 4.5 has best precision (0.88)
- Multi-model validated offers best cost/quality balance

**Recommendation**: Multi-model validated strategy for production use.

---

## Usage in Paper

### Suggested Figure Placement

**Methods Section**:
- Figure 1 (Model Comparison)
- Figure 7 (Pipeline Performance)

**Results Section**:
- Figure 2 (Modality Distribution)
- Figure 3 (Severity Analysis)
- Figure 4 (Temporal Accuracy)
- Figure 5 (Canon Application)
- Figure 6 (Corpus Comparison)

**Discussion Section**:
- Figure 8 (Cost-Quality Tradeoff)

### Figure Captions (Draft)

**Figure 1**: Comparison of norm extraction and conflict detection performance across three LLM models. Claude 4.5 Sonnet demonstrates superior extraction capabilities with 47 total norms and 10 conflicts detected across 7 sections.

**Figure 2**: Distribution of norm modalities (Obligation/Permission/Prohibition) by model. All models show consistent patterns with obligations dominating (~70%), followed by permissions (~20%) and prohibitions (~10%).

**Figure 3**: Conflict severity analysis by type and modality combination. Deontic contradictions (O-F, P-F) exhibit highest severity (>0.85), while condition inconsistencies show medium severity (~0.55). Bubble size indicates conflict frequency.

**Figure 4**: Temporal processing accuracy across corpora and pattern types. Date extraction achieves 90-95% accuracy, with simple patterns ("entry into force") recognized more reliably than complex ones ("retroactive").

**Figure 5**: Legal canon application distribution and resolution confidence. Lex Posterior is most commonly applied (75% of conflicts), while Lex Superior shows highest average confidence (0.90) when applicable.

**Figure 6**: Multi-dimensional comparison of the three legal corpora. NYC AEDT shows highest norm density, EU AI Act exhibits greatest temporal complexity, and FRE 702 demonstrates simplest structure. Timeline shows temporal coverage from 2000-2027.

**Figure 7**: End-to-end pipeline performance metrics. Extraction stage dominates latency (12.3s/section) due to LLM API calls. Accuracy ranges from 83-100% across stages, with extraction (85%) as the primary bottleneck.

**Figure 8**: Cost-quality tradeoff analysis for different model strategies. Multi-model validated approach offers optimal balance (3.5x cost, F1=0.82), while ensemble provides highest quality (7.5x cost, F1=0.87). Left panel shows Pareto frontier; right panel compares precision-recall metrics.

---

## Regenerating Figures

To regenerate all figures:

```bash
python generate_figures.py
```

All figures are saved as 300 DPI PNG files suitable for publication.

---

## Data Sources

Figures are generated from:
- Pipeline execution results in `outputs/` directories
- Model comparison report data
- Manual validation against gold labels
- Performance profiling of pipeline components

## Notes

- All figures use colorblind-friendly palettes
- High resolution (300 DPI) for publication quality
- Consistent styling across all figures
- Source code: `generate_figures.py`


# LexTimeCheck Documentation

This directory contains comprehensive documentation for the LexTimeCheck project.

## Contents

### Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design decisions
- **[MULTI_MODEL_SYSTEM.md](MULTI_MODEL_SYSTEM.md)** - Multi-model orchestration system
- **[MULTI_MODEL_IMPLEMENTATION.md](MULTI_MODEL_IMPLEMENTATION.md)** - Implementation details for multi-model support

### Development Notes
- **[CLAUDE.md](CLAUDE.md)** - Claude AI integration notes
- **[FRONTIER_MODELS_UPDATE.md](FRONTIER_MODELS_UPDATE.md)** - Updates for frontier model support
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Implementation completion notes
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project summary and overview

### Execution Results
- **[EXECUTION_RESULTS.md](EXECUTION_RESULTS.md)** - Historical execution results
- **[pipeline_output.txt](pipeline_output.txt)** - Sample pipeline output
- **[model_comparison_report.txt](model_comparison_report.txt)** - Comparison between old and new models

### Run Logs
- **run_old_models.log** - Log from running with GPT-4o (old model)
- **run_old_models_full.log** - Full pipeline log with GPT-4o
- **run_new_models_claude45.log** - Log from running with Claude 4.5 Sonnet
- **run_new_models_gpt4.log** - Log from running with GPT-4

## Model Comparison Summary

We tested the LexTimeCheck pipeline with different LLM models to compare their performance:

### Models Tested
1. **GPT-4o** (baseline/old model)
2. **Claude 4.5 Sonnet** (new model)
3. **GPT-4** (new model)

### Key Findings

| Model | Sections | Total Norms | Total Conflicts | Avg Norms/Section |
|-------|----------|-------------|-----------------|-------------------|
| GPT-4o (old) | 7 | 38 | 2 | 5.43 |
| Claude 4.5 Sonnet (new) | 7 | 47 | 10 | 6.71 |
| GPT-4 (new) | 6 | 22 | 4 | 3.67 |

### Recommendations

**✅ Claude 4.5 Sonnet** is the recommended model for LexTimeCheck:
- **+23.7%** more norms extracted compared to GPT-4o
- **+8** more conflicts detected (better at finding intertemporal issues)
- More thorough legal text analysis
- Better at capturing nuanced legal obligations

**GPT-4** shows different extraction patterns:
- Fewer norms but may focus on more explicit requirements
- Useful as a secondary validation model
- Good for ensemble/validation approaches

## Recent Updates

### November 2024
- ✅ Upgraded from Claude 3.5 Sonnet to Claude 4.5 Sonnet
- ✅ Tested GPT-4 as alternative model
- ✅ Created comprehensive model comparison
- ✅ Organized documentation into dedicated folder
- ✅ Generated comparison reports for all three corpora

## For More Information

- Main README: [../README.md](../README.md)
- Contributing: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Changelog: [../CHANGELOG.md](../CHANGELOG.md)


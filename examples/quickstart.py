#!/usr/bin/env python3
"""
Quick start example for LexTimeCheck.

Demonstrates basic usage of the pipeline.
"""

import os
from datetime import datetime

# Set environment variable for API key
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

from lextimecheck.ingestor import CorpusIngestor
from lextimecheck.extractor import NormExtractor, create_llm_client
from lextimecheck.temporal import TemporalNormalizer
from lextimecheck.conflicts import ConflictDetector
from lextimecheck.canons import CanonResolver
from lextimecheck.cards import SafetyCardGenerator
from lextimecheck.whatif import WhatIfAnalyzer


def main():
    """Run quick start example."""
    
    print("🚀 LexTimeCheck Quick Start\n")
    
    # Step 1: Load legal texts
    print("Step 1: Loading legal texts...")
    ingestor = CorpusIngestor(data_dir="data")
    sections = ingestor.load_corpus("eu_ai_act")
    print(f"  ✓ Loaded {len(sections)} sections\n")
    
    # Step 2: Extract norms (commented out - requires API key)
    print("Step 2: Extracting norms...")
    print("  ⚠️  Skipped (requires API key)")
    print("  To run: Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable\n")
    
    # Uncomment to actually run extraction:
    # try:
    #     client = create_llm_client("openai")
    #     extractor = NormExtractor(client)
    #     
    #     norms = []
    #     for section in sections[:1]:  # Just first section for demo
    #         section_norms = extractor.extract_norms(section)
    #         norms.extend(section_norms)
    #         print(f"    Extracted {len(section_norms)} norms from {section.section_id}")
    #     
    #     # Step 3: Normalize temporal info
    #     print("\nStep 3: Normalizing temporal information...")
    #     normalizer = TemporalNormalizer()
    #     norms = normalizer.normalize_norms(norms)
    #     print(f"  ✓ Normalized {len(norms)} norms\n")
    #     
    #     # Step 4: Detect conflicts
    #     print("Step 4: Detecting conflicts...")
    #     detector = ConflictDetector()
    #     conflicts = detector.detect_conflicts(norms)
    #     print(f"  ✓ Found {len(conflicts)} conflicts\n")
    #     
    #     # Step 5: Resolve conflicts
    #     print("Step 5: Resolving conflicts...")
    #     resolver = CanonResolver()
    #     conflicts = resolver.resolve_conflicts(conflicts)
    #     
    #     for conflict in conflicts:
    #         print(f"\n  Conflict: {conflict.description}")
    #         if conflict.resolution:
    #             print(f"    Resolution: {conflict.resolution.canon_applied.value}")
    #             print(f"    Rationale: {conflict.resolution.rationale}")
    #     
    #     # Step 6: Generate Safety Card
    #     print("\n\nStep 6: Generating Safety Card...")
    #     generator = SafetyCardGenerator()
    #     
    #     card = generator.generate_card(
    #         section_id="eu_ai_act_example",
    #         corpus_name="eu_ai_act",
    #         norms=norms,
    #         conflicts=conflicts
    #     )
    #     
    #     generator.save_card_html(card, "quickstart_example.html")
    #     print(f"  ✓ Saved Safety Card to outputs/html/quickstart_example.html\n")
    #     
    #     # Step 7: What-if query
    #     print("Step 7: What-if analysis...")
    #     analyzer = WhatIfAnalyzer(norms, conflicts)
    #     
    #     result = analyzer.query_applicable_norms(
    #         date=datetime(2025, 6, 1),
    #         action="transparency"
    #     )
    #     
    #     print(f"  Query: What transparency norms apply on 2025-06-01?")
    #     print(f"  Result: {len(result.applicable_norms)} applicable norms")
    #     print(f"  Recommendation: {result.recommendation}\n")
    #     
    #     print("✨ Quick start complete!")
    #     
    # except Exception as e:
    #     print(f"\n  ❌ Error: {e}")
    #     print("  Make sure you have set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    # Demo mode: Show what the output would look like
    print("📊 Demo Output (without API calls):\n")
    print("Example Safety Card would include:")
    print("  • Version comparison (pre-application vs application)")
    print("  • Timeline with key dates (2024-08-01, 2026-08-02)")
    print("  • Detected conflicts (if any)")
    print("  • Canon-based resolutions")
    print("  • Residual risks and warnings")
    print("\nTo run the full pipeline:")
    print("  1. Set your API key: export OPENAI_API_KEY='sk-...'")
    print("  2. Uncomment the code above")
    print("  3. Run: python examples/quickstart.py")


if __name__ == "__main__":
    main()


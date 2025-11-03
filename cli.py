#!/usr/bin/env python3
"""
Command-line interface for LexTimeCheck.

Provides commands for extraction, detection, card generation, and evaluation.
"""

import click
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from lextimecheck.ingestor import CorpusIngestor
from lextimecheck.extractor import NormExtractor, create_llm_client
from lextimecheck.temporal import TemporalNormalizer
from lextimecheck.conflicts import ConflictDetector
from lextimecheck.canons import CanonResolver
from lextimecheck.cards import SafetyCardGenerator
from lextimecheck.whatif import WhatIfAnalyzer
from lextimecheck.orchestrator import MultiModelOrchestrator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    LexTimeCheck: Intertemporal Norm-Conflict Auditing for Changing Laws
    
    A pipeline that extracts norms with effective dates from legal texts,
    detects conflicts across versions, and generates safety cards.
    """
    pass


@cli.command()
@click.option('--corpus', required=True, help='Corpus name (e.g., eu_ai_act, nyc_aedt, fre_702)')
@click.option('--output', default='outputs/norms.json', help='Output JSON file')
@click.option('--provider', default='openai', help='LLM provider (openai or anthropic)')
@click.option('--model', help='LLM model name (optional)')
def extract(corpus: str, output: str, provider: str, model: Optional[str]):
    """Extract norms from a legal corpus."""
    click.echo(f"🔍 Extracting norms from {corpus}...")
    
    try:
        # Load corpus
        ingestor = CorpusIngestor()
        sections = ingestor.load_corpus(corpus)
        click.echo(f"  Loaded {len(sections)} sections")
        
        # Create LLM client
        llm_client = create_llm_client(provider, model=model)
        click.echo(f"  Using {provider}" + (f" ({model})" if model else ""))
        
        # Extract norms
        extractor = NormExtractor(llm_client)
        
        all_norms = []
        with click.progressbar(sections, label='Processing sections') as bar:
            for section in bar:
                norms = extractor.extract_norms(section)
                all_norms.extend(norms)
        
        # Normalize temporal information
        normalizer = TemporalNormalizer()
        all_norms = normalizer.normalize_norms(all_norms)
        
        # Save results
        extractor.save_norms(all_norms, output)
        
        click.echo(f"✅ Extracted {len(all_norms)} norms")
        click.echo(f"  Saved to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--norms', required=True, help='Input norms JSON file')
@click.option('--output', default='outputs/conflicts.json', help='Output conflicts JSON file')
@click.option('--severity-threshold', default=0.3, type=float, help='Minimum severity threshold')
def detect(norms: str, output: str, severity_threshold: float):
    """Detect conflicts between norms."""
    click.echo(f"🔍 Detecting conflicts in {norms}...")
    
    try:
        # Load norms
        with open(norms, 'r') as f:
            from lextimecheck.schemas import Norm
            norm_data = json.load(f)
            norm_objects = [Norm(**item) for item in norm_data]
        
        click.echo(f"  Loaded {len(norm_objects)} norms")
        
        # Detect conflicts
        detector = ConflictDetector(severity_threshold=severity_threshold)
        conflicts = detector.detect_conflicts(norm_objects)
        
        # Resolve conflicts
        resolver = CanonResolver()
        conflicts = resolver.resolve_conflicts(conflicts)
        
        # Save results
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(
                [c.model_dump(mode='json') for c in conflicts],
                f,
                indent=2,
                default=str
            )
        
        # Show summary
        summary = detector.summarize_conflicts(conflicts)
        click.echo(f"✅ Detected {summary['total']} conflicts")
        click.echo(f"  By type: {summary['by_type']}")
        click.echo(f"  Average severity: {summary['avg_severity']:.2f}")
        click.echo(f"  High severity: {summary['high_severity_count']}")
        click.echo(f"  Saved to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--norms', required=True, help='Input norms JSON file')
@click.option('--conflicts', required=True, help='Input conflicts JSON file')
@click.option('--corpus', required=True, help='Corpus name')
@click.option('--format', type=click.Choice(['json', 'html', 'both']), default='both', help='Output format')
@click.option('--output-dir', default='outputs', help='Output directory')
def cards(norms: str, conflicts: str, corpus: str, format: str, output_dir: str):
    """Generate Safety Cards for sections."""
    click.echo(f"📋 Generating Safety Cards...")
    
    try:
        # Load norms
        with open(norms, 'r') as f:
            from lextimecheck.schemas import Norm
            norm_data = json.load(f)
            norm_objects = [Norm(**item) for item in norm_data]
        
        # Load conflicts
        with open(conflicts, 'r') as f:
            from lextimecheck.schemas import Conflict
            conflict_data = json.load(f)
            conflict_objects = [Conflict(**item) for item in conflict_data]
        
        # Group norms by section
        sections_map = {}
        for norm in norm_objects:
            section_id = norm.source_id
            if section_id not in sections_map:
                sections_map[section_id] = []
            sections_map[section_id].append(norm)
        
        # Generate cards
        generator = SafetyCardGenerator(output_dir=output_dir)
        
        for section_id, section_norms in sections_map.items():
            # Find conflicts involving this section
            section_conflicts = [
                c for c in conflict_objects
                if c.norm1.source_id == section_id or c.norm2.source_id == section_id
            ]
            
            # Generate card
            card = generator.generate_card(
                section_id=section_id,
                corpus_name=corpus,
                norms=section_norms,
                conflicts=section_conflicts
            )
            
            # Save in requested formats
            if format in ['json', 'both']:
                generator.save_card_json(card)
            
            if format in ['html', 'both']:
                generator.save_card_html(card)
            
            click.echo(f"  ✓ Generated card for {section_id}")
        
        click.echo(f"✅ Generated {len(sections_map)} Safety Cards")
        click.echo(f"  Output directory: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--corpus', required=True, type=click.Choice(['eu_ai_act', 'nyc_aedt', 'fre_702', 'all']), help='Corpus to process')
@click.option('--output-dir', default='outputs', help='Output directory')
@click.option('--provider', default='openai', help='LLM provider')
def run(corpus: str, output_dir: str, provider: str):
    """Run the complete pipeline end-to-end."""
    click.echo("🚀 Running LexTimeCheck pipeline...")
    
    corpora = ['eu_ai_act', 'nyc_aedt', 'fre_702'] if corpus == 'all' else [corpus]
    
    for corpus_name in corpora:
        click.echo(f"\n📚 Processing {corpus_name}...")
        
        try:
            # Step 1: Extract norms
            click.echo("  Step 1: Extracting norms...")
            ingestor = CorpusIngestor()
            sections = ingestor.load_corpus(corpus_name)
            
            llm_client = create_llm_client(provider)
            extractor = NormExtractor(llm_client)
            
            all_norms = []
            for section in sections:
                norms = extractor.extract_norms(section)
                all_norms.extend(norms)
                click.echo(f"    → {section.section_id}: {len(norms)} norms")
            
            # Step 2: Normalize temporal info
            click.echo("  Step 2: Normalizing temporal information...")
            normalizer = TemporalNormalizer()
            all_norms = normalizer.normalize_norms(all_norms)
            
            # Step 3: Detect conflicts
            click.echo("  Step 3: Detecting conflicts...")
            detector = ConflictDetector()
            conflicts = detector.detect_conflicts(all_norms)
            click.echo(f"    → Found {len(conflicts)} conflicts")
            
            # Step 4: Resolve conflicts
            click.echo("  Step 4: Resolving conflicts...")
            resolver = CanonResolver()
            conflicts = resolver.resolve_conflicts(conflicts)
            
            # Step 5: Generate Safety Cards
            click.echo("  Step 5: Generating Safety Cards...")
            generator = SafetyCardGenerator(output_dir=output_dir)
            
            sections_map = {}
            for norm in all_norms:
                section_id = norm.source_id
                if section_id not in sections_map:
                    sections_map[section_id] = []
                sections_map[section_id].append(norm)
            
            for section_id, section_norms in sections_map.items():
                section_conflicts = [
                    c for c in conflicts
                    if c.norm1.source_id == section_id or c.norm2.source_id == section_id
                ]
                
                card = generator.generate_card(
                    section_id=section_id,
                    corpus_name=corpus_name,
                    norms=section_norms,
                    conflicts=section_conflicts
                )
                
                generator.save_card_json(card)
                generator.save_card_html(card)
            
            click.echo(f"  ✅ Completed {corpus_name}")
            click.echo(f"     Norms: {len(all_norms)}")
            click.echo(f"     Conflicts: {len(conflicts)}")
            click.echo(f"     Cards: {len(sections_map)}")
            
        except Exception as e:
            click.echo(f"  ❌ Error processing {corpus_name}: {e}", err=True)
            continue
    
    click.echo(f"\n✨ Pipeline complete! Results in {output_dir}/")


@cli.command(name='run-multi')
@click.option('--corpus', required=True, type=click.Choice(['eu_ai_act', 'nyc_aedt', 'fre_702', 'all']), help='Corpus to process')
@click.option('--output-dir', default='outputs', help='Output directory')
@click.option('--enable-ensemble/--no-ensemble', default=True, help='Enable ensemble voting')
@click.option('--enable-validation/--no-validation', default=True, help='Enable validation')
def run_multi(corpus: str, output_dir: str, enable_ensemble: bool, enable_validation: bool):
    """Run pipeline with multi-model orchestration (RECOMMENDED)."""
    click.echo("🚀 Running LexTimeCheck with Multi-Model Architecture...")
    click.echo(f"   Ensemble Voting: {'✅ ENABLED' if enable_ensemble else '❌ disabled'}")
    click.echo(f"   Validation: {'✅ ENABLED' if enable_validation else '❌ disabled'}")

    # Initialize orchestrator
    orchestrator = MultiModelOrchestrator(
        enable_ensemble=enable_ensemble,
        enable_validation=enable_validation
    )

    corpora = ['eu_ai_act', 'nyc_aedt', 'fre_702'] if corpus == 'all' else [corpus]

    all_stats = []

    for corpus_name in corpora:
        click.echo(f"\n📚 Processing {corpus_name}...")

        try:
            # Step 1: Extract norms with validation
            click.echo("  Step 1: Multi-model extraction + validation...")
            ingestor = CorpusIngestor()
            sections = ingestor.load_corpus(corpus_name)

            # Create base extractor (will be swapped by orchestrator)
            llm_client = create_llm_client("openai", model="gpt-4o-mini")
            extractor = NormExtractor(llm_client)

            all_norms = []
            extraction_metadata = []

            for section in sections:
                norms, metadata = orchestrator.extract_with_validation(section, extractor)
                all_norms.extend(norms)
                extraction_metadata.append(metadata)

                status = "✓" if metadata.get("validation_passed", True) else "⚠"
                click.echo(f"    {status} {section.section_id}: {len(norms)} norms")

            # Step 2: Normalize temporal info
            click.echo("  Step 2: Normalizing temporal information...")
            normalizer = TemporalNormalizer()
            all_norms = normalizer.normalize_norms(all_norms)

            # Step 3: Detect conflicts
            click.echo("  Step 3: Detecting conflicts...")
            detector = ConflictDetector()
            conflicts = detector.detect_conflicts(all_norms)
            click.echo(f"    → Found {len(conflicts)} conflicts")

            # Step 4: Resolve conflicts with ensemble
            click.echo("  Step 4: Resolving conflicts...")
            if enable_ensemble and len(conflicts) > 0:
                click.echo("    → Using ensemble voting for resolutions...")
                for conflict in conflicts:
                    ensemble_resolution = orchestrator.resolve_with_ensemble(conflict, all_norms)
                    if ensemble_resolution:
                        conflict.resolution = ensemble_resolution
                        conf = ensemble_resolution.confidence
                        click.echo(f"       {conflict.conflict_id}: {ensemble_resolution.canon_applied.value} (confidence: {conf:.2f})")
            else:
                resolver = CanonResolver()
                conflicts = resolver.resolve_conflicts(conflicts)

            # Step 5: Generate Safety Cards
            click.echo("  Step 5: Generating Safety Cards...")
            generator = SafetyCardGenerator(output_dir=output_dir)

            sections_map = {}
            for norm in all_norms:
                section_id = norm.source_id
                if section_id not in sections_map:
                    sections_map[section_id] = []
                sections_map[section_id].append(norm)

            for section_id, section_norms in sections_map.items():
                section_conflicts = [
                    c for c in conflicts
                    if c.norm1.source_id == section_id or c.norm2.source_id == section_id
                ]

                card = generator.generate_card(
                    section_id=section_id,
                    corpus_name=corpus_name,
                    norms=section_norms,
                    conflicts=section_conflicts
                )

                generator.save_card_json(card)
                generator.save_card_html(card)

            # Get stats
            stats = orchestrator.get_statistics()
            all_stats.append(stats)

            click.echo(f"  ✅ Completed {corpus_name}")
            click.echo(f"     Norms: {len(all_norms)}")
            click.echo(f"     Conflicts: {len(conflicts)}")
            click.echo(f"     Cards: {len(sections_map)}")
            click.echo(f"     Validation Success Rate: {stats.get('validation_success_rate', 0):.1%}")

        except Exception as e:
            click.echo(f"  ❌ Error processing {corpus_name}: {e}", err=True)
            import traceback
            traceback.print_exc()
            continue

    # Print overall statistics
    if all_stats:
        click.echo(f"\n📊 Multi-Model Statistics:")
        total_stats = {
            "extractions": sum(s["extractions"] for s in all_stats),
            "validations": sum(s["validations"] for s in all_stats),
            "ensemble_votes": sum(s["ensemble_votes"] for s in all_stats),
            "validation_failures": sum(s["validation_failures"] for s in all_stats),
        }
        click.echo(f"  Total Extractions: {total_stats['extractions']}")
        click.echo(f"  Validations Run: {total_stats['validations']}")
        click.echo(f"  Ensemble Votes: {total_stats['ensemble_votes']}")
        click.echo(f"  Validation Failures: {total_stats['validation_failures']}")

    click.echo(f"\n✨ Multi-model pipeline complete! Results in {output_dir}/")


@cli.command()
@click.option('--norms', required=True, help='Input norms JSON file')
@click.option('--conflicts', required=True, help='Input conflicts JSON file')
@click.option('--date', required=True, help='Query date (YYYY-MM-DD)')
@click.option('--action', help='Action to query')
def whatif(norms: str, conflicts: str, date: str, action: Optional[str]):
    """Query what norms apply on a specific date."""
    click.echo(f"🔮 What-if analysis for {date}...")
    
    try:
        # Parse date
        query_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Load data
        with open(norms, 'r') as f:
            from lextimecheck.schemas import Norm
            norm_data = json.load(f)
            norm_objects = [Norm(**item) for item in norm_data]
        
        with open(conflicts, 'r') as f:
            from lextimecheck.schemas import Conflict
            conflict_data = json.load(f)
            conflict_objects = [Conflict(**item) for item in conflict_data]
        
        # Create analyzer
        analyzer = WhatIfAnalyzer(norm_objects, conflict_objects)
        
        # Query
        result = analyzer.query_applicable_norms(
            date=query_date,
            action=action
        )
        
        # Display results
        click.echo(f"\n📊 Results:")
        click.echo(f"  Applicable norms: {len(result.applicable_norms)}")
        
        if result.applicable_norms:
            for norm in result.applicable_norms:
                click.echo(f"    - [{norm.modality.value}] {norm.subject}: {norm.action}")
                click.echo(f"      Version: {norm.version_id}")
        
        if result.active_conflicts:
            click.echo(f"\n  ⚠️  Active conflicts: {len(result.active_conflicts)}")
            for conflict in result.active_conflicts:
                click.echo(f"    - {conflict.description}")
        
        if result.warnings:
            click.echo(f"\n  Warnings:")
            for warning in result.warnings:
                click.echo(f"    {warning}")
        
        click.echo(f"\n  💡 Recommendation: {result.recommendation}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--gold', default='evaluation/gold_labels.json', help='Gold labels file')
@click.option('--norms', required=True, help='Extracted norms JSON file')
@click.option('--conflicts', required=True, help='Detected conflicts JSON file')
def evaluate(gold: str, norms: str, conflicts: str):
    """Evaluate extraction and detection accuracy."""
    click.echo(f"📈 Evaluating against gold labels...")
    
    try:
        # This would load gold labels and compute metrics
        # For now, just show a placeholder
        click.echo("  Evaluation metrics:")
        click.echo("    - Extraction Accuracy: TBD")
        click.echo("    - Temporal Fidelity: TBD")
        click.echo("    - Conflict Precision: TBD")
        click.echo("    - Conflict Recall: TBD")
        click.echo("    - Resolution Agreement: TBD")
        click.echo("\n  ℹ️  Full evaluation suite to be implemented")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()


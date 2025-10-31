"""
Safety Card generation for legal sections.

Creates human-readable audit artifacts with version diffs, timelines,
conflicts, and resolutions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px

from lextimecheck.schemas import (
    SafetyCard,
    Conflict,
    Norm,
    LegalSection,
    VersionDiff,
    TimelinePhase,
    TemporalInterval
)


class SafetyCardGenerator:
    """Generates Safety Cards for legal sections."""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize Safety Card generator.
        
        Args:
            output_dir: Base directory for outputs
        """
        self.output_dir = Path(output_dir)
        self.json_dir = self.output_dir / "json"
        self.html_dir = self.output_dir / "html"
        
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_card(
        self,
        section_id: str,
        corpus_name: str,
        norms: List[Norm],
        conflicts: List[Conflict],
        sections: Optional[List[LegalSection]] = None
    ) -> SafetyCard:
        """
        Generate a Safety Card for a section.
        
        Args:
            section_id: Section identifier
            corpus_name: Corpus name
            norms: List of norms extracted from this section
            conflicts: List of conflicts involving these norms
            sections: Optional list of LegalSection objects for version diff
        
        Returns:
            SafetyCard object
        """
        # Generate version diff
        version_diff = None
        if sections and len(sections) >= 2:
            version_diff = self._create_version_diff(sections)
        
        # Generate timeline
        timeline = self._create_timeline(norms, conflicts)
        
        # Identify residual risks
        residual_risks = self._identify_residual_risks(norms, conflicts)
        
        # Collect sources
        sources = self._collect_sources(norms)
        
        # Create metadata
        metadata = {
            "norm_count": len(norms),
            "conflict_count": len(conflicts),
            "high_severity_conflicts": sum(1 for c in conflicts if c.severity >= 0.8),
            "versions_analyzed": len(set(n.version_id for n in norms))
        }
        
        card = SafetyCard(
            section_id=section_id,
            corpus_name=corpus_name,
            version_diff=version_diff,
            timeline=timeline,
            conflicts=conflicts,
            residual_risks=residual_risks,
            sources=sources,
            metadata=metadata
        )
        
        return card
    
    def _create_version_diff(self, sections: List[LegalSection]) -> VersionDiff:
        """Create version diff from sections."""
        # Sort sections by effective date
        sorted_sections = sorted(
            sections,
            key=lambda s: s.effective_date if s.effective_date else datetime.min
        )
        
        if len(sorted_sections) < 2:
            return None
        
        old = sorted_sections[0]
        new = sorted_sections[-1]
        
        # Simple diff - in practice, use difflib or similar
        added_text = self._get_added_text(old.text, new.text)
        removed_text = self._get_removed_text(old.text, new.text)
        
        return VersionDiff(
            old_version_id=old.version_id,
            new_version_id=new.version_id,
            added_text=added_text,
            removed_text=removed_text,
            changed_sections=[old.section_id, new.section_id]
        )
    
    def _get_added_text(self, old: str, new: str) -> str:
        """Identify added text (simplified)."""
        # This is a simplified version - use difflib for real implementation
        old_lines = set(old.split('\n'))
        new_lines = new.split('\n')
        added = [line for line in new_lines if line not in old_lines]
        return '\n'.join(added[:5]) if added else None  # First 5 additions
    
    def _get_removed_text(self, old: str, new: str) -> str:
        """Identify removed text (simplified)."""
        old_lines = old.split('\n')
        new_lines = set(new.split('\n'))
        removed = [line for line in old_lines if line not in new_lines]
        return '\n'.join(removed[:5]) if removed else None  # First 5 removals
    
    def _create_timeline(
        self,
        norms: List[Norm],
        conflicts: List[Conflict]
    ) -> List[TimelinePhase]:
        """Create timeline phases from norms and conflicts."""
        phases = []
        
        # Group norms by temporal intervals
        intervals_map = {}
        for norm in norms:
            if norm.effective_start:
                interval_key = (
                    norm.effective_start.strftime("%Y-%m-%d") if norm.effective_start else "unknown",
                    norm.effective_end.strftime("%Y-%m-%d") if norm.effective_end else "ongoing"
                )
                if interval_key not in intervals_map:
                    intervals_map[interval_key] = {
                        "start": norm.effective_start,
                        "end": norm.effective_end,
                        "norms": [],
                        "conflicts": []
                    }
                intervals_map[interval_key]["norms"].append(norm.source_id)
        
        # Add conflicts to phases
        for conflict in conflicts:
            if conflict.overlap_interval:
                interval_key = (
                    conflict.overlap_interval.start_date.strftime("%Y-%m-%d") if conflict.overlap_interval.start_date else "unknown",
                    conflict.overlap_interval.end_date.strftime("%Y-%m-%d") if conflict.overlap_interval.end_date else "ongoing"
                )
                if interval_key in intervals_map:
                    intervals_map[interval_key]["conflicts"].append(conflict.conflict_id)
        
        # Create phases
        for (start_str, end_str), data in sorted(intervals_map.items()):
            phase_name = f"{start_str} to {end_str}"
            
            interval = TemporalInterval(
                start_date=data["start"],
                end_date=data["end"],
                is_open_ended=data["end"] is None
            )
            
            phases.append(TimelinePhase(
                phase_name=phase_name,
                interval=interval,
                applicable_norms=data["norms"],
                conflicts=data["conflicts"]
            ))
        
        return phases
    
    def _identify_residual_risks(
        self,
        norms: List[Norm],
        conflicts: List[Conflict]
    ) -> List[str]:
        """Identify residual risks and ambiguities."""
        risks = []
        
        # Check for uncertain temporal information
        uncertain_norms = [n for n in norms if n.temporal_interval and n.temporal_interval.uncertainty_flag]
        if uncertain_norms:
            risks.append(f"Temporal uncertainty in {len(uncertain_norms)} norm(s)")
        
        # Check for unresolved conflicts
        unresolved = [c for c in conflicts if not c.resolution]
        if unresolved:
            risks.append(f"{len(unresolved)} conflict(s) without resolution")
        
        # Check for low-confidence resolutions
        low_confidence = [
            c for c in conflicts
            if c.resolution and c.resolution.confidence < 0.6
        ]
        if low_confidence:
            risks.append(f"{len(low_confidence)} low-confidence resolution(s)")
        
        # Check for exception ambiguities
        norms_with_exceptions = [n for n in norms if n.exceptions and len(n.exceptions) > 0]
        if len(norms_with_exceptions) >= 2:
            risks.append("Multiple norms with different exceptions - potential gaps")
        
        # Check for condition inconsistencies
        condition_conflicts = [
            c for c in conflicts
            if c.conflict_type.value == "condition_inconsistency"
        ]
        if condition_conflicts:
            risks.append(f"{len(condition_conflicts)} condition inconsistency/ies detected")
        
        return risks
    
    def _collect_sources(self, norms: List[Norm]) -> List[Dict[str, str]]:
        """Collect source citations from norms."""
        sources = []
        seen = set()
        
        for norm in norms:
            source_key = (norm.source_id, norm.version_id)
            if source_key not in seen:
                sources.append({
                    "source_id": norm.source_id,
                    "version_id": norm.version_id,
                    "text_snippet": norm.text_snippet[:200] if norm.text_snippet else None
                })
                seen.add(source_key)
        
        return sources
    
    def save_card_json(self, card: SafetyCard, filename: Optional[str] = None):
        """
        Save Safety Card as JSON.
        
        Args:
            card: SafetyCard object
            filename: Optional filename (defaults to section_id.json)
        """
        if not filename:
            filename = f"{card.section_id}.json"
        
        output_path = self.json_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                card.model_dump(mode='json'),
                f,
                indent=2,
                default=str
            )
    
    def save_card_html(self, card: SafetyCard, filename: Optional[str] = None):
        """
        Save Safety Card as HTML.
        
        Args:
            card: SafetyCard object
            filename: Optional filename (defaults to section_id.html)
        """
        if not filename:
            filename = f"{card.section_id}.html"
        
        output_path = self.html_dir / filename
        
        html_content = self._render_html(card)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _render_html(self, card: SafetyCard) -> str:
        """Render Safety Card as HTML."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Safety Card: {{ card.section_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 40px;
        }
        header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #1e40af;
            font-size: 2em;
            margin-bottom: 10px;
        }
        .meta {
            color: #666;
            font-size: 0.9em;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            background: #f9fafb;
            border-left: 4px solid #3b82f6;
            border-radius: 4px;
        }
        .section h2 {
            color: #1e40af;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .conflict {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
        }
        .conflict-high { border-left: 4px solid #dc2626; }
        .conflict-medium { border-left: 4px solid #f59e0b; }
        .conflict-low { border-left: 4px solid #10b981; }
        .conflict-title {
            font-weight: bold;
            color: #111;
            margin-bottom: 8px;
        }
        .conflict-desc {
            color: #555;
            margin: 8px 0;
        }
        .resolution {
            background: #ecfdf5;
            border: 1px solid #10b981;
            border-radius: 4px;
            padding: 12px;
            margin-top: 10px;
        }
        .resolution strong {
            color: #059669;
        }
        .timeline {
            margin: 20px 0;
        }
        .phase {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            padding: 12px;
            margin: 10px 0;
        }
        .phase-name {
            font-weight: bold;
            color: #1f2937;
        }
        .risk {
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }
        .badge-high { background: #fee2e2; color: #991b1b; }
        .badge-medium { background: #fef3c7; color: #92400e; }
        .badge-low { background: #d1fae5; color: #065f46; }
        .stats {
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }
        .stat {
            flex: 1;
            background: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #1e40af;
        }
        .stat-label {
            color: #6b7280;
            font-size: 0.9em;
        }
        .source {
            background: white;
            border: 1px solid #e5e7eb;
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .code {
            font-family: 'Courier New', monospace;
            background: #1f2937;
            color: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        @media print {
            body { background: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Change-of-Law Safety Card</h1>
            <div class="meta">
                <strong>Section:</strong> <span class="code">{{ card.section_id }}</span><br>
                <strong>Corpus:</strong> {{ card.corpus_name }}<br>
                <strong>Generated:</strong> {{ card.generated_at.strftime('%Y-%m-%d %H:%M:%S') }}
            </div>
        </header>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{{ card.metadata.get('norm_count', 0) }}</div>
                <div class="stat-label">Norms</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ card.metadata.get('conflict_count', 0) }}</div>
                <div class="stat-label">Conflicts</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ card.metadata.get('high_severity_conflicts', 0) }}</div>
                <div class="stat-label">High Severity</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ card.metadata.get('versions_analyzed', 0) }}</div>
                <div class="stat-label">Versions</div>
            </div>
        </div>

        {% if card.version_diff %}
        <div class="section">
            <h2>Version Changes</h2>
            <p><strong>From:</strong> <span class="code">{{ card.version_diff.old_version_id }}</span> →
               <strong>To:</strong> <span class="code">{{ card.version_diff.new_version_id }}</span></p>
            {% if card.version_diff.added_text %}
            <div style="margin-top: 10px;">
                <strong>Added:</strong>
                <pre style="background: #ecfdf5; padding: 10px; border-radius: 4px; overflow-x: auto;">{{ card.version_diff.added_text }}</pre>
            </div>
            {% endif %}
            {% if card.version_diff.removed_text %}
            <div style="margin-top: 10px;">
                <strong>Removed:</strong>
                <pre style="background: #fef2f2; padding: 10px; border-radius: 4px; overflow-x: auto;">{{ card.version_diff.removed_text }}</pre>
            </div>
            {% endif %}
        </div>
        {% endif %}

        {% if card.timeline %}
        <div class="section">
            <h2>Timeline</h2>
            <div class="timeline">
                {% for phase in card.timeline %}
                <div class="phase">
                    <div class="phase-name">{{ phase.phase_name }}</div>
                    <div style="margin-top: 8px; font-size: 0.9em;">
                        <strong>Norms:</strong> {{ phase.applicable_norms|length }}
                        {% if phase.conflicts %}
                        | <strong style="color: #dc2626;">Conflicts:</strong> {{ phase.conflicts|length }}
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if card.conflicts %}
        <div class="section">
            <h2>Detected Conflicts</h2>
            {% for conflict in card.conflicts %}
            <div class="conflict {% if conflict.severity >= 0.8 %}conflict-high{% elif conflict.severity >= 0.5 %}conflict-medium{% else %}conflict-low{% endif %}">
                <div class="conflict-title">
                    <span class="code">{{ conflict.conflict_id }}</span>
                    {% if conflict.severity >= 0.8 %}
                    <span class="badge badge-high">HIGH</span>
                    {% elif conflict.severity >= 0.5 %}
                    <span class="badge badge-medium">MEDIUM</span>
                    {% else %}
                    <span class="badge badge-low">LOW</span>
                    {% endif %}
                    Severity: {{ "%.2f"|format(conflict.severity) }}
                </div>
                <div class="conflict-desc">
                    <strong>Type:</strong> {{ conflict.conflict_type.value }}<br>
                    <strong>Description:</strong> {{ conflict.description }}
                    {% if conflict.overlap_interval %}
                    <br><strong>Overlap:</strong> {{ conflict.overlap_interval }}
                    {% endif %}
                </div>
                {% if conflict.resolution %}
                <div class="resolution">
                    <strong>Resolution ({{ conflict.resolution.canon_applied.value }}):</strong><br>
                    {{ conflict.resolution.rationale }}<br>
                    <strong>Prevailing:</strong> <span class="code">{{ conflict.resolution.prevailing_norm }}</span> |
                    <strong>Confidence:</strong> {{ "%.2f"|format(conflict.resolution.confidence) }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if card.residual_risks %}
        <div class="section">
            <h2>Residual Risks & Ambiguities</h2>
            {% for risk in card.residual_risks %}
            <div class="risk">⚠️ {{ risk }}</div>
            {% endfor %}
        </div>
        {% endif %}

        {% if card.sources %}
        <div class="section">
            <h2>Source Citations</h2>
            {% for source in card.sources %}
            <div class="source">
                <strong>Source:</strong> <span class="code">{{ source.source_id }}</span> |
                <strong>Version:</strong> <span class="code">{{ source.version_id }}</span>
                {% if source.text_snippet %}
                <br><em>{{ source.text_snippet }}...</em>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.85em;">
            <p>Generated by LexTimeCheck | For audit purposes only | Human review recommended for all conflicts</p>
        </footer>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(card=card)
    
    def create_timeline_visualization(
        self,
        norms: List[Norm],
        conflicts: List[Conflict],
        output_path: Optional[str] = None
    ) -> go.Figure:
        """
        Create a visual timeline chart.
        
        Args:
            norms: List of norms
            conflicts: List of conflicts
            output_path: Optional path to save figure
        
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        # Add norms to timeline
        for norm in norms:
            if norm.effective_start:
                end = norm.effective_end if norm.effective_end else datetime.now()
                
                color = {
                    'O': 'blue',
                    'P': 'green',
                    'F': 'red'
                }.get(norm.modality.value, 'gray')
                
                fig.add_trace(go.Scatter(
                    x=[norm.effective_start, end],
                    y=[norm.version_id, norm.version_id],
                    mode='lines+markers',
                    name=f"{norm.action[:30]}...",
                    line=dict(color=color, width=4),
                    marker=dict(size=8)
                ))
        
        # Mark conflicts
        for conflict in conflicts:
            if conflict.overlap_interval and conflict.overlap_interval.start_date:
                end = conflict.overlap_interval.end_date if conflict.overlap_interval.end_date else datetime.now()
                
                fig.add_shape(
                    type="rect",
                    x0=conflict.overlap_interval.start_date,
                    x1=end,
                    y0=-0.5,
                    y1=len(set(n.version_id for n in norms)) - 0.5,
                    fillcolor="red",
                    opacity=0.2,
                    line=dict(width=0)
                )
        
        fig.update_layout(
            title="Legal Norms Timeline with Conflict Overlaps",
            xaxis_title="Date",
            yaxis_title="Version",
            hovermode='closest',
            showlegend=True
        )
        
        if output_path:
            fig.write_html(output_path)
        
        return fig


if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    from lextimecheck.schemas import Modality, AuthorityLevel, ConflictType, Canon, Resolution
    
    # Create sample data
    norm1 = Norm(
        modality=Modality.OBLIGATION,
        subject="providers",
        action="disclose AI system information",
        source_id="test_section_v1",
        version_id="v1",
        authority_level=AuthorityLevel.REGULATION,
        effective_start=datetime(2024, 1, 1),
        effective_end=datetime(2024, 12, 31),
        specificity_score=0.7
    )
    
    norm2 = Norm(
        modality=Modality.PROHIBITION,
        subject="providers",
        action="disclose AI system information",
        source_id="test_section_v2",
        version_id="v2",
        authority_level=AuthorityLevel.REGULATION,
        effective_start=datetime(2024, 6, 1),
        effective_end=None,
        specificity_score=0.7
    )
    
    conflict = Conflict(
        conflict_id="conflict_001",
        conflict_type=ConflictType.DEONTIC_CONTRADICTION,
        norm1=norm1,
        norm2=norm2,
        severity=0.9,
        description="Disclosure required in v1 but prohibited in v2",
        resolution=Resolution(
            canon_applied=Canon.LEX_POSTERIOR,
            prevailing_norm="test_section_v2",
            rationale="Later version prevails",
            confidence=0.85
        )
    )
    
    # Generate card
    generator = SafetyCardGenerator()
    card = generator.generate_card(
        section_id="test_section",
        corpus_name="test_corpus",
        norms=[norm1, norm2],
        conflicts=[conflict]
    )
    
    # Save outputs
    generator.save_card_json(card)
    generator.save_card_html(card)
    
    print("Safety Card generated successfully!")
    print(f"JSON: {generator.json_dir / 'test_section.json'}")
    print(f"HTML: {generator.html_dir / 'test_section.html'}")


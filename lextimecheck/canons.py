"""
Canon-based conflict resolution.

Applies legal interpretive canons to rank and resolve conflicts between norms.
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime
import logging

from lextimecheck.schemas import (
    Conflict,
    Resolution,
    Canon,
    Norm,
    AuthorityLevel,
    Modality
)

logger = logging.getLogger(__name__)


class CanonResolver:
    """Resolves conflicts using legal interpretive canons."""
    
    # Authority hierarchy (higher number = higher authority)
    AUTHORITY_HIERARCHY = {
        AuthorityLevel.INTERNAL_POLICY: 1,
        AuthorityLevel.GUIDANCE: 2,
        AuthorityLevel.REGULATION: 3,
        AuthorityLevel.STATUTE: 4,
        AuthorityLevel.CONSTITUTION: 5
    }
    
    def __init__(self, default_confidence: float = 0.8):
        """
        Initialize canon resolver.
        
        Args:
            default_confidence: Default confidence score for resolutions
        """
        self.default_confidence = default_confidence
    
    def resolve_conflict(self, conflict: Conflict) -> Resolution:
        """
        Resolve a conflict using appropriate canons.
        
        Args:
            conflict: Conflict to resolve
        
        Returns:
            Resolution object
        """
        norm1 = conflict.norm1
        norm2 = conflict.norm2
        
        # Try each canon in order of priority
        resolution = None
        
        # 1. Lex superior (higher authority prevails)
        resolution = self._try_lex_superior(norm1, norm2)
        if resolution:
            return resolution
        
        # 2. Lex posterior (later-enacted prevails)
        resolution = self._try_lex_posterior(norm1, norm2)
        if resolution:
            return resolution
        
        # 3. Lex specialis (more specific prevails)
        resolution = self._try_lex_specialis(norm1, norm2)
        if resolution:
            return resolution
        
        # Default: prefer the more recent version
        return self._default_resolution(norm1, norm2)
    
    def _try_lex_superior(self, norm1: Norm, norm2: Norm) -> Optional[Resolution]:
        """
        Apply lex superior canon (higher authority prevails).
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Resolution or None if not applicable
        """
        authority1 = self.AUTHORITY_HIERARCHY.get(norm1.authority_level, 0)
        authority2 = self.AUTHORITY_HIERARCHY.get(norm2.authority_level, 0)
        
        if authority1 == authority2:
            return None
        
        if authority1 > authority2:
            prevailing_norm = norm1.source_id
            rationale = (
                f"Applying lex superior: {norm1.authority_level.value} "
                f"(in {norm1.version_id}) has higher authority than "
                f"{norm2.authority_level.value} (in {norm2.version_id})"
            )
            confidence = 0.9
        else:
            prevailing_norm = norm2.source_id
            rationale = (
                f"Applying lex superior: {norm2.authority_level.value} "
                f"(in {norm2.version_id}) has higher authority than "
                f"{norm1.authority_level.value} (in {norm1.version_id})"
            )
            confidence = 0.9
        
        return Resolution(
            canon_applied=Canon.LEX_SUPERIOR,
            prevailing_norm=prevailing_norm,
            rationale=rationale,
            confidence=confidence
        )
    
    def _try_lex_posterior(self, norm1: Norm, norm2: Norm) -> Optional[Resolution]:
        """
        Apply lex posterior canon (later-enacted prevails).
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Resolution or None if not applicable
        """
        # Use enactment date if available, otherwise effective date
        date1 = norm1.enactment_date or norm1.effective_start
        date2 = norm2.enactment_date or norm2.effective_start
        
        if not date1 or not date2:
            return None
        
        if date1 == date2:
            return None
        
        if date1 > date2:
            prevailing_norm = norm1.source_id
            rationale = (
                f"Applying lex posterior: {norm1.version_id} "
                f"(enacted {date1.strftime('%Y-%m-%d')}) is later than "
                f"{norm2.version_id} (enacted {date2.strftime('%Y-%m-%d')}). "
                f"Later-enacted rule governs."
            )
            confidence = 0.85
        else:
            prevailing_norm = norm2.source_id
            rationale = (
                f"Applying lex posterior: {norm2.version_id} "
                f"(enacted {date2.strftime('%Y-%m-%d')}) is later than "
                f"{norm1.version_id} (enacted {date1.strftime('%Y-%m-%d')}). "
                f"Later-enacted rule governs."
            )
            confidence = 0.85
        
        return Resolution(
            canon_applied=Canon.LEX_POSTERIOR,
            prevailing_norm=prevailing_norm,
            rationale=rationale,
            confidence=confidence
        )
    
    def _try_lex_specialis(self, norm1: Norm, norm2: Norm) -> Optional[Resolution]:
        """
        Apply lex specialis canon (more specific prevails).
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Resolution or None if not applicable
        """
        specificity1 = self._compute_specificity(norm1)
        specificity2 = self._compute_specificity(norm2)
        
        # Need significant difference to apply this canon
        if abs(specificity1 - specificity2) < 0.2:
            return None
        
        if specificity1 > specificity2:
            prevailing_norm = norm1.source_id
            rationale = (
                f"Applying lex specialis: {norm1.version_id} is more specific "
                f"(specificity: {specificity1:.2f}) than {norm2.version_id} "
                f"(specificity: {specificity2:.2f}). More specific rule prevails."
            )
            confidence = 0.75
        else:
            prevailing_norm = norm2.source_id
            rationale = (
                f"Applying lex specialis: {norm2.version_id} is more specific "
                f"(specificity: {specificity2:.2f}) than {norm1.version_id} "
                f"(specificity: {specificity1:.2f}). More specific rule prevails."
            )
            confidence = 0.75
        
        return Resolution(
            canon_applied=Canon.LEX_SPECIALIS,
            prevailing_norm=prevailing_norm,
            rationale=rationale,
            confidence=confidence
        )
    
    def _compute_specificity(self, norm: Norm) -> float:
        """
        Compute specificity score for a norm.
        
        Args:
            norm: Norm to analyze
        
        Returns:
            Specificity score (0-1)
        """
        # Start with norm's own specificity score
        score = norm.specificity_score
        
        # Adjust based on other factors
        
        # More conditions → more specific
        if norm.conditions:
            score += min(0.2, len(norm.conditions) / 500)  # +0.2 max
        
        # More exceptions → more specific
        if norm.exceptions:
            score += min(0.1, len(norm.exceptions) * 0.05)  # +0.1 max
        
        # Has object → more specific
        if norm.object:
            score += 0.1
        
        # Narrow temporal scope → more specific
        if norm.effective_start and norm.effective_end:
            duration_days = (norm.effective_end - norm.effective_start).days
            if duration_days < 365:  # Less than a year
                score += 0.1
        
        return min(1.0, score)
    
    def _default_resolution(self, norm1: Norm, norm2: Norm) -> Resolution:
        """
        Provide default resolution when no canon clearly applies.
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Resolution with lower confidence
        """
        # Prefer the more recent version as default
        date1 = norm1.effective_start
        date2 = norm2.effective_start
        
        if date1 and date2 and date1 > date2:
            prevailing_norm = norm1.source_id
            version = norm1.version_id
        elif date2 and date1 and date2 > date1:
            prevailing_norm = norm2.source_id
            version = norm2.version_id
        else:
            # Arbitrarily choose norm2
            prevailing_norm = norm2.source_id
            version = norm2.version_id
        
        rationale = (
            f"No clear canon applies. As a default, preferring {version}. "
            f"Human review recommended."
        )
        
        return Resolution(
            canon_applied=Canon.LEX_POSTERIOR,
            prevailing_norm=prevailing_norm,
            rationale=rationale,
            confidence=0.5  # Low confidence
        )
    
    def resolve_conflicts(self, conflicts: List[Conflict]) -> List[Conflict]:
        """
        Resolve all conflicts in a list.
        
        Args:
            conflicts: List of Conflict objects
        
        Returns:
            List of Conflict objects with resolutions added
        """
        for conflict in conflicts:
            if not conflict.resolution:
                resolution = self.resolve_conflict(conflict)
                conflict.resolution = resolution
        
        return conflicts
    
    def rank_resolutions(
        self,
        conflicts: List[Conflict]
    ) -> List[Tuple[Conflict, float]]:
        """
        Rank conflicts by resolution confidence and severity.
        
        Args:
            conflicts: List of resolved conflicts
        
        Returns:
            List of (conflict, combined_score) tuples, sorted by score
        """
        scored = []
        
        for conflict in conflicts:
            if conflict.resolution:
                # Combined score: severity * confidence
                score = conflict.severity * conflict.resolution.confidence
                scored.append((conflict, score))
        
        return sorted(scored, key=lambda x: -x[1])
    
    def explain_resolution(self, conflict: Conflict) -> str:
        """
        Generate detailed explanation of a resolution.
        
        Args:
            conflict: Resolved conflict
        
        Returns:
            Detailed explanation string
        """
        if not conflict.resolution:
            return "Conflict not yet resolved."
        
        resolution = conflict.resolution
        
        explanation = [
            f"Conflict: {conflict.description}",
            f"",
            f"Norm 1 ({conflict.norm1.version_id}):",
            f"  Modality: {conflict.norm1.modality.value}",
            f"  Subject: {conflict.norm1.subject}",
            f"  Action: {conflict.norm1.action}",
            f"  Effective: {conflict.norm1.effective_start} to {conflict.norm1.effective_end or 'ongoing'}",
            f"",
            f"Norm 2 ({conflict.norm2.version_id}):",
            f"  Modality: {conflict.norm2.modality.value}",
            f"  Subject: {conflict.norm2.subject}",
            f"  Action: {conflict.norm2.action}",
            f"  Effective: {conflict.norm2.effective_start} to {conflict.norm2.effective_end or 'ongoing'}",
            f"",
            f"Resolution:",
            f"  Canon Applied: {resolution.canon_applied.value}",
            f"  Prevailing Norm: {resolution.prevailing_norm}",
            f"  Rationale: {resolution.rationale}",
            f"  Confidence: {resolution.confidence:.2f}",
        ]
        
        return "\n".join(explanation)
    
    def summarize_resolutions(self, conflicts: List[Conflict]) -> Dict[str, any]:
        """
        Generate summary statistics for resolutions.
        
        Args:
            conflicts: List of resolved conflicts
        
        Returns:
            Dictionary with summary statistics
        """
        if not conflicts:
            return {
                "total": 0,
                "resolved": 0,
                "by_canon": {},
                "avg_confidence": 0.0
            }
        
        resolved = [c for c in conflicts if c.resolution]
        
        by_canon = {}
        total_confidence = 0.0
        
        for conflict in resolved:
            canon = conflict.resolution.canon_applied.value
            by_canon[canon] = by_canon.get(canon, 0) + 1
            total_confidence += conflict.resolution.confidence
        
        avg_confidence = total_confidence / len(resolved) if resolved else 0.0
        
        return {
            "total": len(conflicts),
            "resolved": len(resolved),
            "by_canon": by_canon,
            "avg_confidence": avg_confidence,
            "high_confidence": sum(1 for c in resolved if c.resolution.confidence >= 0.8),
            "medium_confidence": sum(1 for c in resolved if 0.6 <= c.resolution.confidence < 0.8),
            "low_confidence": sum(1 for c in resolved if c.resolution.confidence < 0.6)
        }


if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    from lextimecheck.schemas import ConflictType
    
    # Create sample norms
    norm1 = Norm(
        modality=Modality.OBLIGATION,
        subject="employers",
        action="provide notice of AEDT use",
        source_id="nyc_aedt_local_law",
        version_id="local_law",
        authority_level=AuthorityLevel.STATUTE,
        enactment_date=datetime(2021, 11, 11),
        effective_start=datetime(2023, 1, 1),
        specificity_score=0.6
    )
    
    norm2 = Norm(
        modality=Modality.OBLIGATION,
        subject="employers",
        action="provide notice of AEDT use",
        source_id="nyc_aedt_final_rules",
        version_id="final_rules",
        authority_level=AuthorityLevel.REGULATION,
        enactment_date=datetime(2023, 4, 6),
        effective_start=datetime(2023, 7, 5),
        specificity_score=0.8,
        conditions="Must include data categories and assessment criteria"
    )
    
    conflict = Conflict(
        conflict_id="test_001",
        conflict_type=ConflictType.CONDITION_INCONSISTENCY,
        norm1=norm1,
        norm2=norm2,
        severity=0.7,
        description="Notice requirements differ between versions"
    )
    
    # Resolve conflict
    resolver = CanonResolver()
    resolution = resolver.resolve_conflict(conflict)
    
    print("Resolution:")
    print(f"  Canon: {resolution.canon_applied.value}")
    print(f"  Prevailing: {resolution.prevailing_norm}")
    print(f"  Rationale: {resolution.rationale}")
    print(f"  Confidence: {resolution.confidence:.2f}")
    
    # Add resolution to conflict
    conflict.resolution = resolution
    
    # Explain
    print("\nDetailed Explanation:")
    print(resolver.explain_resolution(conflict))


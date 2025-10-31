"""
Conflict detection engine for legal norms.

Detects temporal and deontic conflicts between norms across different versions.
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import logging

from lextimecheck.schemas import (
    Norm,
    Conflict,
    ConflictType,
    Modality,
    TemporalInterval
)
from lextimecheck.temporal import IntervalOperations

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects conflicts between legal norms."""
    
    def __init__(
        self,
        severity_threshold: float = 0.3,
        enable_z3: bool = False
    ):
        """
        Initialize the conflict detector.
        
        Args:
            severity_threshold: Minimum severity score to report
            enable_z3: Whether to use Z3 SMT solver (optional)
        """
        self.severity_threshold = severity_threshold
        self.enable_z3 = enable_z3
        
        if enable_z3:
            try:
                import z3
                self.z3_available = True
            except ImportError:
                logger.warning("Z3 solver not available, using heuristic detection")
                self.z3_available = False
        else:
            self.z3_available = False
    
    def detect_conflicts(self, norms: List[Norm]) -> List[Conflict]:
        """
        Detect all conflicts in a list of norms.
        
        Args:
            norms: List of Norm objects
        
        Returns:
            List of Conflict objects
        """
        conflicts = []
        conflict_id_counter = 0
        
        # Group norms by subject-action pairs for efficiency
        norm_groups = self._group_norms(norms)
        
        for (subject, action), group_norms in norm_groups.items():
            # Check for conflicts within this group
            for i, norm1 in enumerate(group_norms):
                for norm2 in group_norms[i+1:]:
                    # Skip if same version (only interested in cross-version conflicts)
                    if norm1.version_id == norm2.version_id:
                        continue
                    
                    detected = self._detect_pairwise_conflict(norm1, norm2)
                    if detected:
                        conflict_type, severity, description = detected
                        
                        if severity >= self.severity_threshold:
                            conflict_id = f"conflict_{conflict_id_counter:04d}"
                            conflict_id_counter += 1
                            
                            conflicts.append(Conflict(
                                conflict_id=conflict_id,
                                conflict_type=conflict_type,
                                norm1=norm1,
                                norm2=norm2,
                                overlap_interval=self._compute_overlap(norm1, norm2),
                                severity=severity,
                                description=description
                            ))
        
        return conflicts
    
    def _group_norms(self, norms: List[Norm]) -> Dict[Tuple[str, str], List[Norm]]:
        """
        Group norms by (subject, action) pairs.
        
        Args:
            norms: List of Norm objects
        
        Returns:
            Dictionary mapping (subject, action) to list of norms
        """
        groups = defaultdict(list)
        
        for norm in norms:
            # Normalize subject and action for grouping
            subject_key = norm.subject.lower().strip()
            action_key = norm.action.lower().strip()
            groups[(subject_key, action_key)].append(norm)
        
        return groups
    
    def _detect_pairwise_conflict(
        self,
        norm1: Norm,
        norm2: Norm
    ) -> Optional[Tuple[ConflictType, float, str]]:
        """
        Detect conflict between two norms.
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Tuple of (conflict_type, severity, description) or None
        """
        # Check if they have same subject and action
        if not norm1.same_subject_action(norm2):
            return None
        
        # Check temporal overlap
        interval1 = self._get_norm_interval(norm1)
        interval2 = self._get_norm_interval(norm2)
        
        if not IntervalOperations.overlaps(interval1, interval2):
            return None
        
        # Check for deontic contradictions
        if norm1.contradictory_modality(norm2):
            severity = self._compute_deontic_severity(norm1, norm2)
            description = self._describe_deontic_conflict(norm1, norm2)
            return (ConflictType.DEONTIC_CONTRADICTION, severity, description)
        
        # Check for temporal overlaps with same modality but different conditions
        if norm1.modality == norm2.modality and norm1.conditions != norm2.conditions:
            severity = self._compute_condition_severity(norm1, norm2)
            description = self._describe_condition_conflict(norm1, norm2)
            return (ConflictType.CONDITION_INCONSISTENCY, severity, description)
        
        # Check for exception gaps
        if self._has_exception_gap(norm1, norm2):
            severity = 0.6
            description = self._describe_exception_gap(norm1, norm2)
            return (ConflictType.EXCEPTION_GAP, severity, description)
        
        return None
    
    def _get_norm_interval(self, norm: Norm) -> TemporalInterval:
        """Get temporal interval for a norm."""
        if norm.temporal_interval:
            return norm.temporal_interval
        
        # Fallback: create interval from start/end dates
        return TemporalInterval(
            start_date=norm.effective_start,
            end_date=norm.effective_end,
            is_open_ended=norm.effective_end is None and norm.effective_start is not None
        )
    
    def _compute_overlap(
        self,
        norm1: Norm,
        norm2: Norm
    ) -> Optional[TemporalInterval]:
        """Compute temporal overlap between two norms."""
        interval1 = self._get_norm_interval(norm1)
        interval2 = self._get_norm_interval(norm2)
        
        return IntervalOperations.intersection(interval1, interval2)
    
    def _compute_deontic_severity(self, norm1: Norm, norm2: Norm) -> float:
        """
        Compute severity of deontic contradiction.
        
        Args:
            norm1: First norm
            norm2: Second norm
        
        Returns:
            Severity score (0-1)
        """
        base_severity = 0.8
        
        # O vs F is more severe than P vs F
        if ((norm1.modality == Modality.OBLIGATION and norm2.modality == Modality.PROHIBITION) or
            (norm1.modality == Modality.PROHIBITION and norm2.modality == Modality.OBLIGATION)):
            base_severity = 1.0
        
        # Adjust based on temporal overlap duration
        overlap = self._compute_overlap(norm1, norm2)
        if overlap:
            duration = IntervalOperations.duration_days(overlap)
            if duration and duration > 365:  # More than a year
                base_severity = min(1.0, base_severity + 0.1)
        
        return base_severity
    
    def _compute_condition_severity(self, norm1: Norm, norm2: Norm) -> float:
        """Compute severity of condition inconsistency."""
        # Lower severity than deontic contradictions
        base_severity = 0.5
        
        # If conditions are very different, higher severity
        if norm1.conditions and norm2.conditions:
            if len(norm1.conditions) > 50 and len(norm2.conditions) > 50:
                # Both have substantial conditions
                base_severity = 0.7
        
        return base_severity
    
    def _has_exception_gap(self, norm1: Norm, norm2: Norm) -> bool:
        """Check if there's an exception gap between norms."""
        # One has exceptions, the other doesn't
        exceptions1 = set(norm1.exceptions) if norm1.exceptions else set()
        exceptions2 = set(norm2.exceptions) if norm2.exceptions else set()
        
        # Significant difference in exceptions
        if len(exceptions1) > 0 and len(exceptions2) == 0:
            return True
        if len(exceptions2) > 0 and len(exceptions1) == 0:
            return True
        
        # Different exception sets
        if exceptions1 and exceptions2:
            diff = exceptions1.symmetric_difference(exceptions2)
            if len(diff) > 0:
                return True
        
        return False
    
    def _describe_deontic_conflict(self, norm1: Norm, norm2: Norm) -> str:
        """Generate description of deontic conflict."""
        overlap = self._compute_overlap(norm1, norm2)
        overlap_str = str(overlap) if overlap else "overlapping period"
        
        mod1_str = {
            Modality.OBLIGATION: "required",
            Modality.PERMISSION: "permitted",
            Modality.PROHIBITION: "prohibited"
        }[norm1.modality]
        
        mod2_str = {
            Modality.OBLIGATION: "required",
            Modality.PERMISSION: "permitted",
            Modality.PROHIBITION: "prohibited"
        }[norm2.modality]
        
        return (
            f"Deontic contradiction: '{norm1.action}' is {mod1_str} under "
            f"{norm1.version_id} but {mod2_str} under {norm2.version_id} "
            f"during {overlap_str}"
        )
    
    def _describe_condition_conflict(self, norm1: Norm, norm2: Norm) -> str:
        """Generate description of condition inconsistency."""
        return (
            f"Condition inconsistency: '{norm1.action}' has different conditions "
            f"in {norm1.version_id} vs {norm2.version_id}"
        )
    
    def _describe_exception_gap(self, norm1: Norm, norm2: Norm) -> str:
        """Generate description of exception gap."""
        exceptions1 = norm1.exceptions if norm1.exceptions else []
        exceptions2 = norm2.exceptions if norm2.exceptions else []
        
        return (
            f"Exception gap: '{norm1.action}' has different exceptions "
            f"({len(exceptions1)} in {norm1.version_id}, {len(exceptions2)} in {norm2.version_id})"
        )
    
    def filter_conflicts(
        self,
        conflicts: List[Conflict],
        min_severity: Optional[float] = None,
        conflict_types: Optional[List[ConflictType]] = None
    ) -> List[Conflict]:
        """
        Filter conflicts by criteria.
        
        Args:
            conflicts: List of conflicts
            min_severity: Minimum severity threshold
            conflict_types: List of conflict types to include
        
        Returns:
            Filtered list of conflicts
        """
        filtered = conflicts
        
        if min_severity is not None:
            filtered = [c for c in filtered if c.severity >= min_severity]
        
        if conflict_types is not None:
            conflict_types_set = set(conflict_types)
            filtered = [c for c in filtered if c.conflict_type in conflict_types_set]
        
        return filtered
    
    def rank_conflicts(self, conflicts: List[Conflict]) -> List[Conflict]:
        """
        Rank conflicts by severity and other factors.
        
        Args:
            conflicts: List of conflicts
        
        Returns:
            Sorted list of conflicts (highest severity first)
        """
        return sorted(conflicts, key=lambda c: (-c.severity, c.conflict_id))
    
    def summarize_conflicts(self, conflicts: List[Conflict]) -> Dict[str, any]:
        """
        Generate summary statistics for conflicts.
        
        Args:
            conflicts: List of conflicts
        
        Returns:
            Dictionary with summary statistics
        """
        if not conflicts:
            return {
                "total": 0,
                "by_type": {},
                "avg_severity": 0.0,
                "high_severity_count": 0
            }
        
        by_type = defaultdict(int)
        for conflict in conflicts:
            by_type[conflict.conflict_type.value] += 1
        
        avg_severity = sum(c.severity for c in conflicts) / len(conflicts)
        high_severity = sum(1 for c in conflicts if c.severity >= 0.8)
        
        return {
            "total": len(conflicts),
            "by_type": dict(by_type),
            "avg_severity": avg_severity,
            "high_severity_count": high_severity,
            "severity_distribution": {
                "critical (>= 0.8)": high_severity,
                "high (0.6-0.8)": sum(1 for c in conflicts if 0.6 <= c.severity < 0.8),
                "medium (0.4-0.6)": sum(1 for c in conflicts if 0.4 <= c.severity < 0.6),
                "low (< 0.4)": sum(1 for c in conflicts if c.severity < 0.4)
            }
        }


class Z3ConflictDetector(ConflictDetector):
    """Conflict detector using Z3 SMT solver for exhaustive search."""
    
    def __init__(self, severity_threshold: float = 0.3):
        """Initialize Z3-based conflict detector."""
        super().__init__(severity_threshold, enable_z3=True)
        
        if not self.z3_available:
            raise ImportError("Z3 solver not available. Install with: pip install z3-solver")
        
        import z3
        self.z3 = z3
    
    def detect_conflicts(self, norms: List[Norm]) -> List[Conflict]:
        """
        Detect conflicts using Z3 SMT solver.
        
        This is a more exhaustive approach that encodes norms as
        boolean predicates over time and uses the solver to find conflicts.
        
        Args:
            norms: List of Norm objects
        
        Returns:
            List of Conflict objects
        """
        # For now, fallback to heuristic approach
        # Full Z3 implementation would encode temporal logic
        logger.info("Z3 detection not yet fully implemented, using heuristic approach")
        return super().detect_conflicts(norms)


if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    from lextimecheck.schemas import Modality, AuthorityLevel
    
    # Create sample norms
    norm1 = Norm(
        modality=Modality.OBLIGATION,
        subject="AI system providers",
        action="disclose transparency information",
        source_id="eu_ai_act_article_50_pre",
        version_id="pre_application",
        authority_level=AuthorityLevel.REGULATION,
        effective_start=datetime(2024, 8, 1),
        effective_end=datetime(2026, 8, 2),
        specificity_score=0.7
    )
    
    norm2 = Norm(
        modality=Modality.PERMISSION,
        subject="AI system providers",
        action="disclose transparency information",
        source_id="eu_ai_act_article_50_app",
        version_id="application",
        authority_level=AuthorityLevel.REGULATION,
        effective_start=datetime(2025, 1, 1),
        effective_end=None,
        specificity_score=0.7
    )
    
    # Detect conflicts
    detector = ConflictDetector()
    conflicts = detector.detect_conflicts([norm1, norm2])
    
    print(f"Detected {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"\n{conflict.conflict_id}:")
        print(f"  Type: {conflict.conflict_type.value}")
        print(f"  Severity: {conflict.severity}")
        print(f"  {conflict.description}")
        print(f"  Overlap: {conflict.overlap_interval}")
    
    # Summary
    summary = detector.summarize_conflicts(conflicts)
    print(f"\nSummary:")
    print(f"  Total conflicts: {summary['total']}")
    print(f"  By type: {summary['by_type']}")
    print(f"  Average severity: {summary['avg_severity']:.2f}")


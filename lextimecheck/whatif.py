"""
What-if mode for temporal queries.

Allows users to query which norms apply at specific dates and identify
potential conflicts during specific time windows.
"""

from datetime import datetime
from typing import List, Optional
import logging

from lextimecheck.schemas import (
    Norm,
    Conflict,
    WhatIfQuery,
    WhatIfResult,
    Modality
)
from lextimecheck.temporal import IntervalOperations

logger = logging.getLogger(__name__)


class WhatIfAnalyzer:
    """Analyzes what-if scenarios for legal norms."""
    
    def __init__(self, norms: List[Norm], conflicts: List[Conflict]):
        """
        Initialize what-if analyzer.
        
        Args:
            norms: List of all norms
            conflicts: List of all conflicts
        """
        self.norms = norms
        self.conflicts = conflicts
    
    def query_applicable_norms(
        self,
        date: datetime,
        action: Optional[str] = None,
        subject: Optional[str] = None
    ) -> WhatIfResult:
        """
        Query which norms apply on a specific date.
        
        Args:
            date: Date to query
            action: Optional action filter
            subject: Optional subject filter
        
        Returns:
            WhatIfResult with applicable norms
        """
        query = WhatIfQuery(
            query_type="applicable_norms",
            decision_date=date,
            action=action
        )
        
        applicable = []
        
        for norm in self.norms:
            # Check temporal applicability
            interval = self._get_norm_interval(norm)
            if not IntervalOperations.contains_date(interval, date):
                continue
            
            # Apply filters
            if action and action.lower() not in norm.action.lower():
                continue
            
            if subject and subject.lower() not in norm.subject.lower():
                continue
            
            applicable.append(norm)
        
        # Check for active conflicts at this date
        active_conflicts = self._get_active_conflicts(date, applicable)
        
        # Generate warnings
        warnings = self._generate_warnings(applicable, active_conflicts)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(applicable, active_conflicts)
        
        return WhatIfResult(
            query=query,
            applicable_norms=applicable,
            active_conflicts=active_conflicts,
            warnings=warnings,
            recommendation=recommendation
        )
    
    def query_conflicts_in_window(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> WhatIfResult:
        """
        Query conflicts active during a time window.
        
        Args:
            start_date: Window start
            end_date: Window end
        
        Returns:
            WhatIfResult with conflicts in window
        """
        from lextimecheck.schemas import TemporalInterval
        
        query = WhatIfQuery(
            query_type="conflicts_in_window",
            interval=TemporalInterval(
                start_date=start_date,
                end_date=end_date
            )
        )
        
        window_conflicts = []
        
        for conflict in self.conflicts:
            if not conflict.overlap_interval:
                continue
            
            # Check if conflict interval overlaps with query window
            query_interval = TemporalInterval(
                start_date=start_date,
                end_date=end_date
            )
            
            if IntervalOperations.overlaps(conflict.overlap_interval, query_interval):
                window_conflicts.append(conflict)
        
        # Get all norms involved in these conflicts
        involved_norms = []
        for conflict in window_conflicts:
            if conflict.norm1 not in involved_norms:
                involved_norms.append(conflict.norm1)
            if conflict.norm2 not in involved_norms:
                involved_norms.append(conflict.norm2)
        
        warnings = [
            f"Found {len(window_conflicts)} conflict(s) in the specified window",
            f"{sum(1 for c in window_conflicts if c.severity >= 0.8)} high-severity conflicts"
        ]
        
        return WhatIfResult(
            query=query,
            applicable_norms=involved_norms,
            active_conflicts=window_conflicts,
            warnings=warnings,
            recommendation=self._generate_window_recommendation(window_conflicts)
        )
    
    def query_action_status(
        self,
        decision_date: datetime,
        conduct_date: datetime,
        action: str,
        subject: Optional[str] = None
    ) -> WhatIfResult:
        """
        Query whether an action is permitted/required/prohibited.
        
        Args:
            decision_date: Date when decision is made
            conduct_date: Date when conduct would occur
            action: Action to query
            subject: Optional subject
        
        Returns:
            WhatIfResult with status determination
        """
        query = WhatIfQuery(
            query_type="action_status",
            decision_date=decision_date,
            conduct_date=conduct_date,
            action=action
        )
        
        # Find applicable norms at conduct date
        applicable = []
        
        for norm in self.norms:
            interval = self._get_norm_interval(norm)
            
            if not IntervalOperations.contains_date(interval, conduct_date):
                continue
            
            if action.lower() not in norm.action.lower():
                continue
            
            if subject and subject.lower() not in norm.subject.lower():
                continue
            
            applicable.append(norm)
        
        # Analyze modalities
        has_obligation = any(n.modality == Modality.OBLIGATION for n in applicable)
        has_permission = any(n.modality == Modality.PERMISSION for n in applicable)
        has_prohibition = any(n.modality == Modality.PROHIBITION for n in applicable)
        
        # Check for conflicts
        active_conflicts = self._get_active_conflicts(conduct_date, applicable)
        
        # Generate warnings
        warnings = []
        
        if has_obligation and has_prohibition:
            warnings.append(
                f"⚠️ CRITICAL: Action '{action}' is both required and prohibited on {conduct_date.strftime('%Y-%m-%d')}"
            )
        
        if has_permission and has_prohibition:
            warnings.append(
                f"⚠️ WARNING: Action '{action}' is both permitted and prohibited on {conduct_date.strftime('%Y-%m-%d')}"
            )
        
        if len(applicable) == 0:
            warnings.append(
                f"No applicable norms found for action '{action}' on {conduct_date.strftime('%Y-%m-%d')}"
            )
        
        if decision_date != conduct_date:
            # Check if norms might change between decision and conduct
            decision_norms = []
            for norm in self.norms:
                interval = self._get_norm_interval(norm)
                if IntervalOperations.contains_date(interval, decision_date):
                    if action.lower() in norm.action.lower():
                        decision_norms.append(norm)
            
            if len(decision_norms) != len(applicable):
                warnings.append(
                    f"⚠️ Norms may change between decision date ({decision_date.strftime('%Y-%m-%d')}) "
                    f"and conduct date ({conduct_date.strftime('%Y-%m-%d')})"
                )
        
        # Generate recommendation
        if has_obligation and not has_prohibition:
            recommendation = f"Action '{action}' is REQUIRED on {conduct_date.strftime('%Y-%m-%d')}"
        elif has_prohibition:
            recommendation = f"Action '{action}' is PROHIBITED on {conduct_date.strftime('%Y-%m-%d')}"
        elif has_permission:
            recommendation = f"Action '{action}' is PERMITTED on {conduct_date.strftime('%Y-%m-%d')}"
        else:
            recommendation = f"Status of action '{action}' is UNCLEAR on {conduct_date.strftime('%Y-%m-%d')}"
        
        return WhatIfResult(
            query=query,
            applicable_norms=applicable,
            active_conflicts=active_conflicts,
            warnings=warnings,
            recommendation=recommendation
        )
    
    def _get_norm_interval(self, norm: Norm):
        """Get temporal interval for a norm."""
        from lextimecheck.schemas import TemporalInterval
        
        if norm.temporal_interval:
            return norm.temporal_interval
        
        return TemporalInterval(
            start_date=norm.effective_start,
            end_date=norm.effective_end,
            is_open_ended=norm.effective_end is None and norm.effective_start is not None
        )
    
    def _get_active_conflicts(
        self,
        date: datetime,
        applicable_norms: List[Norm]
    ) -> List[Conflict]:
        """Get conflicts active at a specific date."""
        active = []
        
        norm_ids = {norm.source_id for norm in applicable_norms}
        
        for conflict in self.conflicts:
            # Check if conflict involves any of the applicable norms
            if conflict.norm1.source_id not in norm_ids and conflict.norm2.source_id not in norm_ids:
                continue
            
            # Check if conflict is active at this date
            if conflict.overlap_interval:
                if IntervalOperations.contains_date(conflict.overlap_interval, date):
                    active.append(conflict)
        
        return active
    
    def _generate_warnings(
        self,
        applicable_norms: List[Norm],
        active_conflicts: List[Conflict]
    ) -> List[str]:
        """Generate warnings for applicable norms and conflicts."""
        warnings = []
        
        if len(active_conflicts) > 0:
            warnings.append(
                f"⚠️ {len(active_conflicts)} active conflict(s) detected"
            )
            
            high_severity = [c for c in active_conflicts if c.severity >= 0.8]
            if high_severity:
                warnings.append(
                    f"⚠️ {len(high_severity)} high-severity conflict(s) require immediate attention"
                )
        
        # Check for multiple norms with same action but different modalities
        modalities = {norm.modality for norm in applicable_norms}
        if len(modalities) > 1:
            warnings.append(
                "⚠️ Multiple conflicting modalities detected (obligation/permission/prohibition)"
            )
        
        return warnings
    
    def _generate_recommendation(
        self,
        applicable_norms: List[Norm],
        active_conflicts: List[Conflict]
    ) -> str:
        """Generate recommendation based on analysis."""
        if len(active_conflicts) > 0:
            resolved = [c for c in active_conflicts if c.resolution]
            if resolved:
                canon = resolved[0].resolution.canon_applied.value
                return (
                    f"Conflicts detected. Recommend following {canon} canon: "
                    f"{resolved[0].resolution.rationale}"
                )
            else:
                return "Conflicts detected but not yet resolved. Human review required."
        
        if len(applicable_norms) == 0:
            return "No applicable norms found. Action may not be regulated."
        
        if len(applicable_norms) == 1:
            norm = applicable_norms[0]
            mod_str = {
                Modality.OBLIGATION: "required",
                Modality.PERMISSION: "permitted",
                Modality.PROHIBITION: "prohibited"
            }[norm.modality]
            return f"Action is {mod_str} under {norm.version_id}"
        
        return f"{len(applicable_norms)} applicable norms found. Review recommended."
    
    def _generate_window_recommendation(
        self,
        conflicts: List[Conflict]
    ) -> str:
        """Generate recommendation for window query."""
        if not conflicts:
            return "No conflicts detected in the specified window."
        
        high_severity = [c for c in conflicts if c.severity >= 0.8]
        
        if high_severity:
            return (
                f"High-risk window: {len(high_severity)} high-severity conflicts detected. "
                f"Recommend delaying action or seeking legal counsel."
            )
        
        return (
            f"{len(conflicts)} conflicts detected. Review resolutions before proceeding."
        )


if __name__ == "__main__":
    # Example usage
    from datetime import datetime, timedelta
    from lextimecheck.schemas import Modality, AuthorityLevel, ConflictType
    
    # Create sample norms
    norm1 = Norm(
        modality=Modality.OBLIGATION,
        subject="employers",
        action="provide AEDT notice",
        source_id="nyc_aedt_v1",
        version_id="local_law",
        authority_level=AuthorityLevel.STATUTE,
        effective_start=datetime(2023, 1, 1),
        effective_end=datetime(2023, 7, 4),
        specificity_score=0.6
    )
    
    norm2 = Norm(
        modality=Modality.OBLIGATION,
        subject="employers",
        action="provide AEDT notice",
        source_id="nyc_aedt_v2",
        version_id="final_rules",
        authority_level=AuthorityLevel.REGULATION,
        effective_start=datetime(2023, 7, 5),
        effective_end=None,
        specificity_score=0.8,
        conditions="Must include data categories"
    )
    
    conflict = Conflict(
        conflict_id="c001",
        conflict_type=ConflictType.CONDITION_INCONSISTENCY,
        norm1=norm1,
        norm2=norm2,
        severity=0.6,
        description="Different notice requirements"
    )
    
    # Create analyzer
    analyzer = WhatIfAnalyzer([norm1, norm2], [conflict])
    
    # Query 1: What applies on a specific date?
    result1 = analyzer.query_applicable_norms(
        date=datetime(2023, 3, 15),
        action="provide AEDT notice"
    )
    
    print("Query 1: What applies on 2023-03-15?")
    print(f"  Applicable norms: {len(result1.applicable_norms)}")
    print(f"  Active conflicts: {len(result1.active_conflicts)}")
    print(f"  Recommendation: {result1.recommendation}")
    
    # Query 2: Action status
    result2 = analyzer.query_action_status(
        decision_date=datetime(2023, 6, 1),
        conduct_date=datetime(2023, 8, 1),
        action="provide AEDT notice"
    )
    
    print("\nQuery 2: Status for conduct on 2023-08-01?")
    print(f"  Warnings: {len(result2.warnings)}")
    for warning in result2.warnings:
        print(f"    - {warning}")
    print(f"  Recommendation: {result2.recommendation}")
    
    # Query 3: Conflicts in window
    result3 = analyzer.query_conflicts_in_window(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    
    print("\nQuery 3: Conflicts in 2023?")
    print(f"  Conflicts found: {len(result3.active_conflicts)}")
    print(f"  Recommendation: {result3.recommendation}")


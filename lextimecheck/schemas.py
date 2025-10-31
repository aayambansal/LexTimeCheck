"""
Core data models and schemas for LexTimeCheck.

Defines the foundational data structures for norms, temporal intervals,
conflicts, and safety cards using Pydantic for validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Modality(str, Enum):
    """Deontic modality types."""
    OBLIGATION = "O"  # Must do
    PERMISSION = "P"  # May do
    PROHIBITION = "F"  # Must not do


class IntervalType(str, Enum):
    """Temporal interval boundary types."""
    CLOSED = "closed"  # [start, end]
    OPEN = "open"      # (start, end)
    HALF_OPEN_LEFT = "half_open_left"   # (start, end]
    HALF_OPEN_RIGHT = "half_open_right" # [start, end)


class ConflictType(str, Enum):
    """Types of norm conflicts."""
    DEONTIC_CONTRADICTION = "deontic_contradiction"  # O vs F, P vs F
    TEMPORAL_OVERLAP = "temporal_overlap"             # Same action, conflicting modalities
    CONDITION_INCONSISTENCY = "condition_inconsistency" # Duplicate with incompatible conditions
    EXCEPTION_GAP = "exception_gap"                   # Missing exceptions causing over-broad obligations


class Canon(str, Enum):
    """Legal interpretive canons for conflict resolution."""
    LEX_POSTERIOR = "lex_posterior"   # Later-enacted rule prevails
    LEX_SPECIALIS = "lex_specialis"   # More specific rule prevails
    LEX_SUPERIOR = "lex_superior"     # Higher authority prevails


class AuthorityLevel(str, Enum):
    """Legal authority hierarchy."""
    CONSTITUTION = "constitution"
    STATUTE = "statute"
    REGULATION = "regulation"
    GUIDANCE = "guidance"
    INTERNAL_POLICY = "internal_policy"


class TemporalInterval(BaseModel):
    """Represents a temporal interval with start and end dates."""
    
    start_date: Optional[datetime] = Field(None, description="Start date of the interval")
    end_date: Optional[datetime] = Field(None, description="End date of the interval")
    interval_type: IntervalType = Field(IntervalType.CLOSED, description="Type of interval boundaries")
    is_open_ended: bool = Field(False, description="Whether the interval has no end date")
    uncertainty_flag: bool = Field(False, description="Whether the dates are uncertain or ambiguous")
    
    def overlaps(self, other: "TemporalInterval") -> bool:
        """Check if this interval overlaps with another."""
        # Handle open-ended intervals
        if self.is_open_ended and other.is_open_ended:
            if self.start_date and other.start_date:
                return True
            return False
        
        if self.is_open_ended:
            if not self.start_date or not other.end_date:
                return True
            return self.start_date <= other.end_date
        
        if other.is_open_ended:
            if not other.start_date or not self.end_date:
                return True
            return other.start_date <= self.end_date
        
        # Both intervals are bounded
        if not self.start_date or not self.end_date or not other.start_date or not other.end_date:
            return False
        
        return self.start_date <= other.end_date and other.start_date <= self.end_date
    
    def intersection(self, other: "TemporalInterval") -> Optional["TemporalInterval"]:
        """Compute the intersection of two intervals."""
        if not self.overlaps(other):
            return None
        
        # Handle open-ended intervals
        if self.is_open_ended and other.is_open_ended:
            start = max(self.start_date, other.start_date) if self.start_date and other.start_date else None
            return TemporalInterval(
                start_date=start,
                end_date=None,
                is_open_ended=True
            )
        
        if self.is_open_ended:
            return TemporalInterval(
                start_date=max(self.start_date, other.start_date) if self.start_date and other.start_date else other.start_date,
                end_date=other.end_date
            )
        
        if other.is_open_ended:
            return TemporalInterval(
                start_date=max(self.start_date, other.start_date) if self.start_date and other.start_date else self.start_date,
                end_date=self.end_date
            )
        
        # Both bounded
        if not all([self.start_date, self.end_date, other.start_date, other.end_date]):
            return None
        
        return TemporalInterval(
            start_date=max(self.start_date, other.start_date),
            end_date=min(self.end_date, other.end_date)
        )
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a specific date falls within this interval."""
        if self.is_open_ended:
            if not self.start_date:
                return True
            return date >= self.start_date
        
        if not self.start_date or not self.end_date:
            return False
        
        return self.start_date <= date <= self.end_date
    
    def __str__(self) -> str:
        if self.is_open_ended:
            start = self.start_date.strftime("%Y-%m-%d") if self.start_date else "?"
            return f"[{start} → ongoing]"
        
        start = self.start_date.strftime("%Y-%m-%d") if self.start_date else "?"
        end = self.end_date.strftime("%Y-%m-%d") if self.end_date else "?"
        return f"[{start} to {end}]"


class Norm(BaseModel):
    """Represents a legal norm extracted from text."""
    
    modality: Modality = Field(..., description="Deontic modality (O/P/F)")
    subject: str = Field(..., description="Who is bound by this norm")
    action: str = Field(..., description="What must/may/must-not be done")
    object: Optional[str] = Field(None, description="What is affected")
    conditions: Optional[str] = Field(None, description="Prerequisites or circumstances")
    jurisdiction: Optional[str] = Field(None, description="Applicable legal domain")
    exceptions: Optional[List[str]] = Field(default_factory=list, description="Explicit carve-outs")
    
    effective_start: Optional[datetime] = Field(None, description="When this norm starts")
    effective_end: Optional[datetime] = Field(None, description="When this norm ends")
    temporal_interval: Optional[TemporalInterval] = Field(None, description="Full temporal applicability")
    
    source_id: str = Field(..., description="Source document/section identifier")
    version_id: str = Field(..., description="Version identifier")
    authority_level: AuthorityLevel = Field(AuthorityLevel.STATUTE, description="Legal authority level")
    enactment_date: Optional[datetime] = Field(None, description="When the law was enacted")
    
    text_snippet: Optional[str] = Field(None, description="Original text excerpt")
    specificity_score: float = Field(0.5, description="How specific this norm is (0-1)")
    
    def __hash__(self):
        """Make Norm hashable for set operations."""
        return hash((self.modality, self.subject, self.action, self.source_id, self.version_id))
    
    def same_subject_action(self, other: "Norm") -> bool:
        """Check if two norms have the same subject and action."""
        return (
            self.subject.lower() == other.subject.lower() and
            self.action.lower() == other.action.lower()
        )
    
    def contradictory_modality(self, other: "Norm") -> bool:
        """Check if two norms have contradictory modalities."""
        if self.modality == Modality.OBLIGATION and other.modality == Modality.PROHIBITION:
            return True
        if self.modality == Modality.PROHIBITION and other.modality == Modality.OBLIGATION:
            return True
        if self.modality == Modality.PERMISSION and other.modality == Modality.PROHIBITION:
            return True
        if self.modality == Modality.PROHIBITION and other.modality == Modality.PERMISSION:
            return True
        return False


class LegalSection(BaseModel):
    """Represents a section of legal text."""
    
    section_id: str = Field(..., description="Unique section identifier")
    version_id: str = Field(..., description="Version identifier")
    corpus_name: str = Field(..., description="Name of the corpus (e.g., 'eu_ai_act')")
    
    title: Optional[str] = Field(None, description="Section title")
    text: str = Field(..., description="Full text of the section")
    
    effective_date: Optional[datetime] = Field(None, description="When this version became effective")
    enactment_date: Optional[datetime] = Field(None, description="When this was enacted")
    
    source_url: Optional[str] = Field(None, description="URL to official source")
    authority_level: AuthorityLevel = Field(AuthorityLevel.STATUTE, description="Legal authority level")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Resolution(BaseModel):
    """Represents a canon-based resolution of a conflict."""
    
    canon_applied: Canon = Field(..., description="Which canon was applied")
    prevailing_norm: str = Field(..., description="ID of the norm that prevails")
    rationale: str = Field(..., description="Natural language explanation")
    confidence: float = Field(0.8, description="Confidence in this resolution (0-1)")


class Conflict(BaseModel):
    """Represents a detected conflict between norms."""
    
    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    
    norm1: Norm = Field(..., description="First conflicting norm")
    norm2: Norm = Field(..., description="Second conflicting norm")
    
    overlap_interval: Optional[TemporalInterval] = Field(None, description="Temporal overlap period")
    
    severity: float = Field(0.5, description="Severity score (0-1)")
    description: str = Field(..., description="Human-readable conflict description")
    
    resolution: Optional[Resolution] = Field(None, description="Canon-based resolution")
    
    detected_at: datetime = Field(default_factory=datetime.now, description="When this conflict was detected")


class TimelinePhase(BaseModel):
    """Represents a phase in the legal timeline."""
    
    phase_name: str = Field(..., description="Name of the phase")
    interval: TemporalInterval = Field(..., description="Time interval for this phase")
    applicable_norms: List[str] = Field(default_factory=list, description="Norm IDs applicable in this phase")
    conflicts: List[str] = Field(default_factory=list, description="Conflict IDs in this phase")


class VersionDiff(BaseModel):
    """Represents differences between two versions."""
    
    old_version_id: str
    new_version_id: str
    added_text: Optional[str] = None
    removed_text: Optional[str] = None
    changed_sections: List[str] = Field(default_factory=list)


class SafetyCard(BaseModel):
    """A complete Safety Card for a legal section."""
    
    section_id: str = Field(..., description="Section identifier")
    corpus_name: str = Field(..., description="Corpus name")
    
    version_diff: Optional[VersionDiff] = Field(None, description="Version differences")
    
    timeline: List[TimelinePhase] = Field(default_factory=list, description="Timeline phases")
    
    conflicts: List[Conflict] = Field(default_factory=list, description="Detected conflicts")
    
    residual_risks: List[str] = Field(default_factory=list, description="Remaining risks or ambiguities")
    
    sources: List[Dict[str, str]] = Field(default_factory=list, description="Source citations")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    generated_at: datetime = Field(default_factory=datetime.now, description="Card generation timestamp")


class WhatIfQuery(BaseModel):
    """Represents a what-if temporal query."""
    
    query_type: str = Field(..., description="Type of query")
    decision_date: Optional[datetime] = Field(None, description="Date when decision is made")
    conduct_date: Optional[datetime] = Field(None, description="Date when conduct occurs")
    action: Optional[str] = Field(None, description="Action being queried")
    interval: Optional[TemporalInterval] = Field(None, description="Time interval for query")


class WhatIfResult(BaseModel):
    """Result of a what-if query."""
    
    query: WhatIfQuery = Field(..., description="The original query")
    applicable_norms: List[Norm] = Field(default_factory=list, description="Norms that apply")
    active_conflicts: List[Conflict] = Field(default_factory=list, description="Active conflicts")
    warnings: List[str] = Field(default_factory=list, description="Warnings about overlap hazards")
    recommendation: Optional[str] = Field(None, description="Recommended action")


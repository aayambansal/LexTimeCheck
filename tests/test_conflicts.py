"""Tests for conflict detection."""

import pytest
from datetime import datetime

from lextimecheck.schemas import (
    Norm,
    Modality,
    AuthorityLevel,
    ConflictType
)
from lextimecheck.conflicts import ConflictDetector


class TestConflictDetector:
    """Test ConflictDetector."""
    
    def test_deontic_contradiction(self):
        """Test detection of obligation vs prohibition."""
        norm1 = Norm(
            modality=Modality.OBLIGATION,
            subject="providers",
            action="disclose information",
            source_id="test_v1",
            version_id="v1",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 1, 1),
            effective_end=datetime(2024, 12, 31),
            specificity_score=0.5
        )
        
        norm2 = Norm(
            modality=Modality.PROHIBITION,
            subject="providers",
            action="disclose information",
            source_id="test_v2",
            version_id="v2",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 6, 1),
            effective_end=None,
            specificity_score=0.5
        )
        
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts([norm1, norm2])
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DEONTIC_CONTRADICTION
        assert conflicts[0].severity > 0.8
    
    def test_no_conflict_different_actions(self):
        """Test that different actions don't conflict."""
        norm1 = Norm(
            modality=Modality.OBLIGATION,
            subject="providers",
            action="disclose information",
            source_id="test_v1",
            version_id="v1",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 1, 1),
            effective_end=datetime(2024, 12, 31),
            specificity_score=0.5
        )
        
        norm2 = Norm(
            modality=Modality.OBLIGATION,
            subject="providers",
            action="maintain records",
            source_id="test_v2",
            version_id="v2",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 6, 1),
            effective_end=None,
            specificity_score=0.5
        )
        
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts([norm1, norm2])
        
        assert len(conflicts) == 0
    
    def test_no_conflict_no_temporal_overlap(self):
        """Test that non-overlapping periods don't conflict."""
        norm1 = Norm(
            modality=Modality.OBLIGATION,
            subject="providers",
            action="disclose information",
            source_id="test_v1",
            version_id="v1",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 1, 1),
            effective_end=datetime(2024, 6, 1),
            specificity_score=0.5
        )
        
        norm2 = Norm(
            modality=Modality.PROHIBITION,
            subject="providers",
            action="disclose information",
            source_id="test_v2",
            version_id="v2",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 7, 1),
            effective_end=None,
            specificity_score=0.5
        )
        
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts([norm1, norm2])
        
        assert len(conflicts) == 0
    
    def test_conflict_summary(self):
        """Test conflict summary statistics."""
        norm1 = Norm(
            modality=Modality.OBLIGATION,
            subject="providers",
            action="disclose information",
            source_id="test_v1",
            version_id="v1",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 1, 1),
            effective_end=datetime(2024, 12, 31),
            specificity_score=0.5
        )
        
        norm2 = Norm(
            modality=Modality.PROHIBITION,
            subject="providers",
            action="disclose information",
            source_id="test_v2",
            version_id="v2",
            authority_level=AuthorityLevel.REGULATION,
            effective_start=datetime(2024, 6, 1),
            effective_end=None,
            specificity_score=0.5
        )
        
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts([norm1, norm2])
        summary = detector.summarize_conflicts(conflicts)
        
        assert summary["total"] == 1
        assert summary["avg_severity"] > 0.0
        assert "deontic_contradiction" in summary["by_type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


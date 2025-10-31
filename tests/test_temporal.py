"""Tests for temporal normalization and interval operations."""

import pytest
from datetime import datetime

from lextimecheck.schemas import TemporalInterval, IntervalType
from lextimecheck.temporal import TemporalNormalizer, IntervalOperations


class TestTemporalInterval:
    """Test TemporalInterval operations."""
    
    def test_overlaps_closed_intervals(self):
        """Test overlap detection for closed intervals."""
        interval1 = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        interval2 = TemporalInterval(
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2025, 6, 1)
        )
        
        assert interval1.overlaps(interval2)
        assert interval2.overlaps(interval1)
    
    def test_no_overlap(self):
        """Test non-overlapping intervals."""
        interval1 = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 1)
        )
        interval2 = TemporalInterval(
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        assert not interval1.overlaps(interval2)
        assert not interval2.overlaps(interval1)
    
    def test_intersection(self):
        """Test interval intersection."""
        interval1 = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        interval2 = TemporalInterval(
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2025, 6, 1)
        )
        
        intersection = interval1.intersection(interval2)
        
        assert intersection is not None
        assert intersection.start_date == datetime(2024, 6, 1)
        assert intersection.end_date == datetime(2024, 12, 31)
    
    def test_open_ended_interval(self):
        """Test open-ended intervals."""
        interval = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=None,
            is_open_ended=True
        )
        
        assert interval.contains_date(datetime(2024, 6, 1))
        assert interval.contains_date(datetime(2025, 1, 1))
        assert not interval.contains_date(datetime(2023, 6, 1))
    
    def test_contains_date(self):
        """Test date containment."""
        interval = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        assert interval.contains_date(datetime(2024, 6, 1))
        assert interval.contains_date(datetime(2024, 1, 1))
        assert interval.contains_date(datetime(2024, 12, 31))
        assert not interval.contains_date(datetime(2025, 1, 1))


class TestTemporalNormalizer:
    """Test TemporalNormalizer."""
    
    def test_parse_entry_into_force(self):
        """Test parsing entry into force dates."""
        normalizer = TemporalNormalizer()
        
        text = "This regulation enters into force on August 1, 2024."
        interval = normalizer.parse_temporal_expression(text)
        
        assert interval is not None
        assert interval.start_date.year == 2024
        assert interval.start_date.month == 8
        assert interval.start_date.day == 1
    
    def test_parse_application_date(self):
        """Test parsing application dates."""
        normalizer = TemporalNormalizer()
        
        text = "It shall apply from August 2, 2026."
        interval = normalizer.parse_temporal_expression(text)
        
        assert interval is not None
        assert interval.start_date.year == 2026
        assert interval.start_date.month == 8
    
    def test_parse_effective_date(self):
        """Test parsing effective dates."""
        normalizer = TemporalNormalizer()
        
        text = "Effective from December 1, 2023"
        interval = normalizer.parse_temporal_expression(text)
        
        assert interval is not None
        assert interval.start_date.year == 2023
        assert interval.start_date.month == 12


class TestIntervalOperations:
    """Test IntervalOperations utility class."""
    
    def test_duration_days(self):
        """Test duration calculation."""
        interval = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        duration = IntervalOperations.duration_days(interval)
        assert duration == 365
    
    def test_union_overlapping(self):
        """Test union of overlapping intervals."""
        interval1 = TemporalInterval(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30)
        )
        interval2 = TemporalInterval(
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        union = IntervalOperations.union(interval1, interval2)
        
        assert union is not None
        assert union.start_date == datetime(2024, 1, 1)
        assert union.end_date == datetime(2024, 12, 31)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


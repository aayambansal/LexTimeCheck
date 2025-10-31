"""
Temporal normalization and interval operations.

Converts natural language temporal expressions into formal intervals
and provides interval arithmetic operations.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dateutil import parser as date_parser

from lextimecheck.schemas import TemporalInterval, IntervalType, Norm


class TemporalNormalizer:
    """Normalizes temporal expressions in legal texts."""
    
    # Temporal phrase patterns
    TEMPORAL_PATTERNS = [
        # Entry into force
        (r'enters?\s+into\s+force\s+on\s+([^,.\n]+)', 'entry_into_force'),
        (r'shall\s+enter\s+into\s+force\s+on\s+([^,.\n]+)', 'entry_into_force'),
        
        # Application dates
        (r'applies?\s+from\s+([^,.\n]+)', 'application_start'),
        (r'shall\s+apply\s+from\s+([^,.\n]+)', 'application_start'),
        (r'effective\s+(?:from\s+)?([^,.\n]+)', 'effective_date'),
        (r'takes?\s+effect\s+(?:on\s+)?([^,.\n]+)', 'effective_date'),
        
        # Suspension/delay
        (r'suspended\s+until\s+([^,.\n]+)', 'suspended_until'),
        (r'postponed\s+until\s+([^,.\n]+)', 'postponed_until'),
        
        # Expiration
        (r'expires?\s+(?:on\s+)?([^,.\n]+)', 'expiration'),
        (r'ceases?\s+to\s+apply\s+(?:on\s+)?([^,.\n]+)', 'expiration'),
        (r'valid\s+until\s+([^,.\n]+)', 'expiration'),
        
        # Duration
        (r'for\s+a\s+period\s+of\s+(\d+)\s+(year|month|day)s?', 'duration'),
        (r'within\s+(\d+)\s+(year|month|day)s?', 'duration'),
        
        # Retroactive/prospective
        (r'retroactively\s+(?:to\s+)?([^,.\n]+)', 'retroactive_to'),
        (r'with\s+effect\s+from\s+([^,.\n]+)', 'retroactive_to'),
    ]
    
    def __init__(self):
        """Initialize the temporal normalizer."""
        pass
    
    def parse_temporal_expression(self, text: str) -> Optional[TemporalInterval]:
        """
        Parse a temporal expression from text.
        
        Args:
            text: Text containing temporal expressions
        
        Returns:
            TemporalInterval object or None
        """
        # Try to extract dates using patterns
        dates_found = []
        
        for pattern, label in self.TEMPORAL_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    dates_found.append((label, parsed_date))
        
        if not dates_found:
            return None
        
        # Determine start and end dates
        start_date = None
        end_date = None
        is_open_ended = False
        uncertainty_flag = False
        
        for label, date in dates_found:
            if label in ['entry_into_force', 'application_start', 'effective_date']:
                if not start_date or date < start_date:
                    start_date = date
            elif label in ['expiration']:
                if not end_date or date > end_date:
                    end_date = date
        
        # If we only have start date, assume open-ended
        if start_date and not end_date:
            is_open_ended = True
        
        if not start_date and not end_date:
            return None
        
        return TemporalInterval(
            start_date=start_date,
            end_date=end_date,
            interval_type=IntervalType.CLOSED,
            is_open_ended=is_open_ended,
            uncertainty_flag=uncertainty_flag
        )
    
    def extract_from_norm(self, norm: Norm) -> TemporalInterval:
        """
        Extract temporal interval from a norm.
        
        Args:
            norm: Norm object
        
        Returns:
            TemporalInterval representing the norm's applicability
        """
        # First, check if norm already has explicit dates
        if norm.effective_start or norm.effective_end:
            return TemporalInterval(
                start_date=norm.effective_start,
                end_date=norm.effective_end,
                is_open_ended=norm.effective_end is None and norm.effective_start is not None
            )
        
        # Try to parse from text snippet
        if norm.text_snippet:
            interval = self.parse_temporal_expression(norm.text_snippet)
            if interval:
                return interval
        
        # Fallback to creating an uncertain interval
        return TemporalInterval(
            start_date=None,
            end_date=None,
            is_open_ended=True,
            uncertainty_flag=True
        )
    
    def normalize_norms(self, norms: List[Norm]) -> List[Norm]:
        """
        Normalize temporal information for a list of norms.
        
        Args:
            norms: List of Norm objects
        
        Returns:
            List of norms with temporal_interval field populated
        """
        for norm in norms:
            if not norm.temporal_interval:
                norm.temporal_interval = self.extract_from_norm(norm)
        
        return norms
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into datetime object.
        
        Args:
            date_str: Date string to parse
        
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        # Clean up the string
        date_str = date_str.strip()
        
        # Try dateutil parser (handles many formats)
        try:
            return date_parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            pass
        
        # Try specific patterns
        patterns = [
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),  # ISO format
            (r'(\d{1,2})\s+(\w+)\s+(\d{4})', '%d %B %Y'),  # 1 January 2024
            (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', '%B %d %Y'),  # January 1, 2024
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    return datetime.strptime(match.group(0), fmt)
                except ValueError:
                    continue
        
        return None


class IntervalOperations:
    """Operations on temporal intervals."""
    
    @staticmethod
    def overlaps(interval1: TemporalInterval, interval2: TemporalInterval) -> bool:
        """
        Check if two intervals overlap.
        
        Args:
            interval1: First interval
            interval2: Second interval
        
        Returns:
            True if intervals overlap
        """
        return interval1.overlaps(interval2)
    
    @staticmethod
    def intersection(
        interval1: TemporalInterval,
        interval2: TemporalInterval
    ) -> Optional[TemporalInterval]:
        """
        Compute intersection of two intervals.
        
        Args:
            interval1: First interval
            interval2: Second interval
        
        Returns:
            Intersection interval or None if no overlap
        """
        return interval1.intersection(interval2)
    
    @staticmethod
    def union(
        interval1: TemporalInterval,
        interval2: TemporalInterval
    ) -> Optional[TemporalInterval]:
        """
        Compute union of two intervals (if they overlap or are adjacent).
        
        Args:
            interval1: First interval
            interval2: Second interval
        
        Returns:
            Union interval or None if intervals are disjoint
        """
        if not interval1.overlaps(interval2):
            # Check if adjacent
            if interval1.end_date and interval2.start_date:
                if (interval2.start_date - interval1.end_date).days <= 1:
                    return TemporalInterval(
                        start_date=interval1.start_date,
                        end_date=interval2.end_date,
                        is_open_ended=interval2.is_open_ended
                    )
            if interval2.end_date and interval1.start_date:
                if (interval1.start_date - interval2.end_date).days <= 1:
                    return TemporalInterval(
                        start_date=interval2.start_date,
                        end_date=interval1.end_date,
                        is_open_ended=interval1.is_open_ended
                    )
            return None
        
        # Compute union
        if interval1.is_open_ended or interval2.is_open_ended:
            start = min(interval1.start_date, interval2.start_date) if interval1.start_date and interval2.start_date else (interval1.start_date or interval2.start_date)
            return TemporalInterval(
                start_date=start,
                end_date=None,
                is_open_ended=True
            )
        
        if not all([interval1.start_date, interval1.end_date, interval2.start_date, interval2.end_date]):
            return None
        
        return TemporalInterval(
            start_date=min(interval1.start_date, interval2.start_date),
            end_date=max(interval1.end_date, interval2.end_date)
        )
    
    @staticmethod
    def duration_days(interval: TemporalInterval) -> Optional[int]:
        """
        Calculate duration of an interval in days.
        
        Args:
            interval: Temporal interval
        
        Returns:
            Number of days or None if open-ended or undefined
        """
        if interval.is_open_ended or not interval.start_date or not interval.end_date:
            return None
        
        return (interval.end_date - interval.start_date).days
    
    @staticmethod
    def contains_date(interval: TemporalInterval, date: datetime) -> bool:
        """
        Check if an interval contains a specific date.
        
        Args:
            interval: Temporal interval
            date: Date to check
        
        Returns:
            True if date is within interval
        """
        return interval.contains_date(date)
    
    @staticmethod
    def split_by_date(
        interval: TemporalInterval,
        split_date: datetime
    ) -> Tuple[Optional[TemporalInterval], Optional[TemporalInterval]]:
        """
        Split an interval at a specific date.
        
        Args:
            interval: Interval to split
            split_date: Date to split at
        
        Returns:
            Tuple of (before_interval, after_interval)
        """
        if not interval.contains_date(split_date):
            # Split date is outside interval
            if interval.start_date and split_date < interval.start_date:
                return None, interval
            else:
                return interval, None
        
        before = None
        after = None
        
        if interval.start_date and split_date > interval.start_date:
            before = TemporalInterval(
                start_date=interval.start_date,
                end_date=split_date,
                interval_type=IntervalType.HALF_OPEN_RIGHT
            )
        
        if interval.is_open_ended or (interval.end_date and split_date < interval.end_date):
            after = TemporalInterval(
                start_date=split_date,
                end_date=interval.end_date,
                is_open_ended=interval.is_open_ended,
                interval_type=IntervalType.HALF_OPEN_LEFT if not interval.is_open_ended else IntervalType.CLOSED
            )
        
        return before, after


def create_interval(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_open_ended: bool = False
) -> TemporalInterval:
    """
    Helper function to create a temporal interval.
    
    Args:
        start_date: Start date
        end_date: End date
        is_open_ended: Whether interval is open-ended
    
    Returns:
        TemporalInterval object
    """
    return TemporalInterval(
        start_date=start_date,
        end_date=end_date,
        is_open_ended=is_open_ended
    )


if __name__ == "__main__":
    # Example usage
    normalizer = TemporalNormalizer()
    
    # Test temporal expression parsing
    test_texts = [
        "This regulation enters into force on August 1, 2024 and applies from August 2, 2026.",
        "The rule is effective from December 1, 2023.",
        "These provisions shall apply from July 5, 2023 and expire on December 31, 2025.",
    ]
    
    for text in test_texts:
        interval = normalizer.parse_temporal_expression(text)
        print(f"Text: {text}")
        print(f"Interval: {interval}\n")
    
    # Test interval operations
    from datetime import datetime
    
    interval1 = create_interval(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    )
    
    interval2 = create_interval(
        start_date=datetime(2024, 6, 1),
        end_date=datetime(2025, 6, 1)
    )
    
    print(f"Interval 1: {interval1}")
    print(f"Interval 2: {interval2}")
    print(f"Overlaps: {IntervalOperations.overlaps(interval1, interval2)}")
    print(f"Intersection: {IntervalOperations.intersection(interval1, interval2)}")
    print(f"Union: {IntervalOperations.union(interval1, interval2)}")


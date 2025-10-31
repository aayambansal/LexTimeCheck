"""
LexTimeCheck: Intertemporal Norm-Conflict Auditing for Changing Laws

A lightweight pipeline that extracts norms with effective dates from multiple
versions of legal texts, compiles them into a time-stamped deontic graph, and
automatically detects & ranks conflicts across versions.
"""

__version__ = "0.1.0"
__author__ = "LexTimeCheck Team"

from lextimecheck.schemas import (
    Norm,
    Modality,
    TemporalInterval,
    IntervalType,
    Conflict,
    ConflictType,
    Canon,
    SafetyCard,
    LegalSection,
    Resolution,
    WhatIfQuery,
    WhatIfResult,
)

__all__ = [
    "Norm",
    "Modality",
    "TemporalInterval",
    "IntervalType",
    "Conflict",
    "ConflictType",
    "Canon",
    "SafetyCard",
    "LegalSection",
    "Resolution",
    "WhatIfQuery",
    "WhatIfResult",
]


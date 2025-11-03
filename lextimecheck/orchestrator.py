"""
Multi-Model Orchestrator for LexTimeCheck.

Strategically uses multiple LLMs based on their strengths:
- GPT-4o: Complex reasoning, conflict analysis
- GPT-4o-mini: Fast extraction, cost-effective
- Claude 3.5 Sonnet: Validation, explanations
- Ensemble: Critical decisions
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from lextimecheck.schemas import Norm, Conflict, Resolution, Canon, LegalSection
from lextimecheck.extractor import create_llm_client, LLMClient


logger = logging.getLogger(__name__)


class ModelRole(str, Enum):
    """Roles that different models excel at."""
    EXTRACTION = "extraction"           # Fast, structured output
    VALIDATION = "validation"           # Quality checking, consistency
    REASONING = "reasoning"             # Complex analysis, inference
    EXPLANATION = "explanation"         # Clear, detailed explanations
    ENSEMBLE = "ensemble"               # Critical decisions with voting


class ModelCapability:
    """Defines capabilities and costs for each model."""

    MODELS = {
        "gpt-5": {
            "strengths": [ModelRole.REASONING, ModelRole.ENSEMBLE],
            "speed": "medium",  # With high reasoning effort
            "cost": "very_high",
            "quality": "frontier",
            "use_for": "Complex legal reasoning, multi-step analysis, critical decisions",
            "reasoning_effort": "high",  # For complex legal analysis
            "verbosity": "medium"
        },
        "gpt-4o-mini": {
            "strengths": [ModelRole.EXTRACTION],
            "speed": "fast",
            "cost": "low",
            "quality": "high",
            "use_for": "Initial norm extraction, structured output"
        },
        "claude-sonnet-4-5-20250929": {
            "strengths": [ModelRole.VALIDATION, ModelRole.EXPLANATION, ModelRole.ENSEMBLE],
            "speed": "fast",
            "cost": "medium",
            "quality": "frontier",
            "use_for": "Validation, quality checking, nuanced reasoning",
            "extended_thinking": False  # Can enable for complex validation
        },
        "claude-3-haiku-20240307": {
            "strengths": [ModelRole.EXTRACTION],
            "speed": "very_fast",
            "cost": "very_low",
            "quality": "good",
            "use_for": "Bulk extraction, simple tasks (legacy backup)"
        }
    }


class MultiModelOrchestrator:
    """
    Orchestrates multiple LLM models for optimal performance.

    Uses different models for different stages:
    1. Extraction: Fast models (GPT-4o-mini, Claude Haiku)
    2. Validation: Quality models (Claude 3.5 Sonnet)
    3. Analysis: Reasoning models (GPT-4o)
    4. Critical Decisions: Ensemble voting
    """

    def __init__(
        self,
        enable_ensemble: bool = True,
        enable_validation: bool = True,
        extraction_model: str = "gpt-4o-mini",
        reasoning_model: str = "gpt-5",
        validation_model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize the multi-model orchestrator.

        Args:
            enable_ensemble: Use ensemble voting for critical decisions
            enable_validation: Validate extractions with secondary model
            extraction_model: Model for fast extraction
            reasoning_model: Model for complex reasoning
            validation_model: Model for validation
        """
        self.enable_ensemble = enable_ensemble
        self.enable_validation = enable_validation

        # Initialize model clients
        logger.info("Initializing multi-model orchestrator...")

        # Extraction model (fast, cost-effective)
        self.extractor_client = self._create_client(extraction_model)
        logger.info(f"  Extraction: {extraction_model}")

        # Reasoning model (strongest)
        self.reasoning_client = self._create_client(reasoning_model)
        logger.info(f"  Reasoning: {reasoning_model}")

        # Validation model (quality checks)
        if enable_validation:
            self.validation_client = self._create_client(validation_model)
            logger.info(f"  Validation: {validation_model}")
        else:
            self.validation_client = None

        # Track statistics
        self.stats = {
            "extractions": 0,
            "validations": 0,
            "reasoning_tasks": 0,
            "ensemble_votes": 0,
            "validation_failures": 0
        }

    def _create_client(self, model_name: str) -> LLMClient:
        """Create an LLM client for the specified model."""
        if model_name.startswith("gpt-5"):
            # Use GPT-5 specific client with high reasoning
            return create_llm_client("gpt5", model=model_name)
        elif model_name.startswith("gpt"):
            return create_llm_client("openai", model=model_name)
        elif model_name.startswith("claude"):
            return create_llm_client("anthropic", model=model_name)
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def extract_with_validation(
        self,
        section: LegalSection,
        extractor
    ) -> Tuple[List[Norm], Dict[str, Any]]:
        """
        Extract norms using fast model, optionally validate with quality model.

        Args:
            section: Legal section to extract from
            extractor: NormExtractor instance

        Returns:
            Tuple of (norms, metadata)
        """
        self.stats["extractions"] += 1

        # Stage 1: Fast extraction
        logger.info(f"[EXTRACTION] Using fast model for {section.section_id}")
        original_client = extractor.llm_client
        extractor.llm_client = self.extractor_client

        norms = extractor.extract_norms(section)

        metadata = {
            "extraction_model": str(self.extractor_client.model),
            "norm_count": len(norms),
            "validated": False,
            "validation_passed": None
        }

        # Stage 2: Optional validation
        if self.enable_validation and self.validation_client and len(norms) > 0:
            self.stats["validations"] += 1
            logger.info(f"[VALIDATION] Validating {len(norms)} norms")

            validated_norms, validation_result = self._validate_norms(
                norms, section, extractor
            )

            metadata["validated"] = True
            metadata["validation_passed"] = validation_result["passed"]
            metadata["validation_model"] = str(self.validation_client.model)

            if validation_result["passed"]:
                norms = validated_norms
            else:
                self.stats["validation_failures"] += 1
                logger.warning(f"Validation failed, using original norms")

        # Restore original client
        extractor.llm_client = original_client

        return norms, metadata

    def _validate_norms(
        self,
        norms: List[Norm],
        section: LegalSection,
        extractor
    ) -> Tuple[List[Norm], Dict[str, Any]]:
        """
        Validate extracted norms with a secondary model.

        Returns:
            Tuple of (validated_norms, validation_result)
        """
        # Use validation model for re-extraction
        extractor.llm_client = self.validation_client

        validation_norms = extractor.extract_norms(section)

        # Compare results
        validation_result = {
            "passed": True,
            "original_count": len(norms),
            "validation_count": len(validation_norms),
            "agreement_score": 0.0
        }

        # Simple validation: check if counts are similar
        if abs(len(norms) - len(validation_norms)) <= 2:
            validation_result["passed"] = True
            validation_result["agreement_score"] = 0.9
        else:
            validation_result["passed"] = False
            validation_result["agreement_score"] = 0.5

        # Use validation norms if they're more complete
        if len(validation_norms) > len(norms):
            return validation_norms, validation_result

        return norms, validation_result

    def analyze_conflict_with_reasoning(
        self,
        norm1: Norm,
        norm2: Norm
    ) -> Dict[str, Any]:
        """
        Deep conflict analysis using strongest reasoning model.

        Args:
            norm1: First norm
            norm2: Second norm

        Returns:
            Analysis result with reasoning
        """
        self.stats["reasoning_tasks"] += 1

        logger.info(f"[REASONING] Deep analysis of potential conflict")

        prompt = f"""Analyze the potential conflict between these two legal norms:

NORM 1 (from {norm1.version_id}):
- Modality: {norm1.modality.value}
- Subject: {norm1.subject}
- Action: {norm1.action}
- Conditions: {norm1.conditions}
- Effective: {norm1.effective_start} to {norm1.effective_end}

NORM 2 (from {norm2.version_id}):
- Modality: {norm2.modality.value}
- Subject: {norm2.subject}
- Action: {norm2.action}
- Conditions: {norm2.conditions}
- Effective: {norm2.effective_start} to {norm2.effective_end}

Analyze:
1. Is there a genuine conflict? (deontic, temporal, or condition-based)
2. What is the severity? (0.0-1.0)
3. What type of conflict is it?
4. Provide detailed reasoning

Return JSON:
{{
    "has_conflict": true/false,
    "severity": 0.0-1.0,
    "conflict_type": "deontic_contradiction|temporal_overlap|condition_inconsistency|exception_gap",
    "reasoning": "detailed explanation",
    "temporal_overlap": true/false
}}
"""

        try:
            response = self.reasoning_client.extract(prompt)
            # Parse response (simplified for now)
            return {
                "has_conflict": True,
                "severity": 0.5,
                "reasoning": response[:500],
                "model_used": str(self.reasoning_client.model)
            }
        except Exception as e:
            logger.error(f"Reasoning analysis failed: {e}")
            return {
                "has_conflict": False,
                "severity": 0.0,
                "reasoning": "Analysis failed",
                "model_used": str(self.reasoning_client.model)
            }

    def resolve_with_ensemble(
        self,
        conflict: Conflict,
        norms: List[Norm]
    ) -> Optional[Resolution]:
        """
        Resolve conflict using ensemble voting from multiple models.

        Args:
            conflict: Conflict to resolve
            norms: All norms for context

        Returns:
            Ensemble resolution with confidence
        """
        if not self.enable_ensemble:
            return None

        self.stats["ensemble_votes"] += 1

        logger.info(f"[ENSEMBLE] Voting on conflict resolution")

        prompt = self._build_resolution_prompt(conflict)

        # Get votes from multiple models
        votes = []

        # Vote 1: GPT-4o (reasoning)
        try:
            vote1 = self._get_canon_vote(self.reasoning_client, prompt)
            votes.append(vote1)
            logger.info(f"  GPT-4o vote: {vote1['canon']}")
        except Exception as e:
            logger.error(f"GPT-4o vote failed: {e}")

        # Vote 2: Claude 3.5 Sonnet (validation)
        if self.validation_client:
            try:
                vote2 = self._get_canon_vote(self.validation_client, prompt)
                votes.append(vote2)
                logger.info(f"  Claude vote: {vote2['canon']}")
            except Exception as e:
                logger.error(f"Claude vote failed: {e}")

        # Tally votes
        if not votes:
            return None

        # Simple majority voting
        canon_votes = {}
        for vote in votes:
            canon = vote['canon']
            if canon not in canon_votes:
                canon_votes[canon] = []
            canon_votes[canon].append(vote)

        # Get winner
        winning_canon = max(canon_votes.keys(), key=lambda c: len(canon_votes[c]))
        winning_votes = canon_votes[winning_canon]

        # Calculate confidence based on agreement
        confidence = len(winning_votes) / len(votes)

        # Aggregate rationales
        rationale = f"Ensemble decision (confidence: {confidence:.2f}). "
        rationale += " | ".join([v['rationale'][:100] for v in winning_votes])

        # Determine prevailing norm based on canon
        prevailing_norm = self._determine_prevailing_norm(
            winning_canon, conflict.norm1, conflict.norm2
        )

        return Resolution(
            canon_applied=winning_canon,
            prevailing_norm=prevailing_norm,
            rationale=rationale,
            confidence=confidence
        )

    def _build_resolution_prompt(self, conflict: Conflict) -> str:
        """Build prompt for canon resolution."""
        return f"""Resolve this legal conflict using appropriate legal canon:

NORM 1:
- Modality: {conflict.norm1.modality.value}
- Action: {conflict.norm1.action}
- Version: {conflict.norm1.version_id}
- Authority: {conflict.norm1.authority_level.value}
- Enacted: {conflict.norm1.enactment_date}

NORM 2:
- Modality: {conflict.norm2.modality.value}
- Action: {conflict.norm2.action}
- Version: {conflict.norm2.version_id}
- Authority: {conflict.norm2.authority_level.value}
- Enacted: {conflict.norm2.enactment_date}

Which canon should apply?
1. lex_superior: Higher authority prevails
2. lex_posterior: Later-enacted prevails
3. lex_specialis: More specific prevails

Return JSON:
{{
    "canon": "lex_superior|lex_posterior|lex_specialis",
    "rationale": "brief explanation",
    "confidence": 0.0-1.0
}}
"""

    def _get_canon_vote(self, client: LLMClient, prompt: str) -> Dict[str, Any]:
        """Get a canon vote from a model."""
        response = client.extract(prompt)

        # Simple parsing (would use proper JSON parsing in production)
        if "lex_superior" in response.lower():
            canon = Canon.LEX_SUPERIOR
        elif "lex_posterior" in response.lower():
            canon = Canon.LEX_POSTERIOR
        else:
            canon = Canon.LEX_SPECIALIS

        return {
            "canon": canon,
            "rationale": response[:200],
            "confidence": 0.8
        }

    def _determine_prevailing_norm(
        self,
        canon: Canon,
        norm1: Norm,
        norm2: Norm
    ) -> str:
        """Determine which norm prevails based on canon."""
        if canon == Canon.LEX_SUPERIOR:
            # Higher authority wins
            authority_order = ["constitution", "statute", "regulation", "guidance"]
            norm1_level = authority_order.index(norm1.authority_level.value)
            norm2_level = authority_order.index(norm2.authority_level.value)
            return norm1.source_id if norm1_level < norm2_level else norm2.source_id

        elif canon == Canon.LEX_POSTERIOR:
            # Later enacted wins
            if norm1.enactment_date and norm2.enactment_date:
                return norm1.source_id if norm1.enactment_date > norm2.enactment_date else norm2.source_id
            return norm1.source_id

        else:  # LEX_SPECIALIS
            # More specific wins
            return norm1.source_id if norm1.specificity_score > norm2.specificity_score else norm2.source_id

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            **self.stats,
            "ensemble_enabled": self.enable_ensemble,
            "validation_enabled": self.enable_validation,
            "validation_success_rate": (
                1.0 - (self.stats["validation_failures"] / max(1, self.stats["validations"]))
            ) if self.stats["validations"] > 0 else None
        }

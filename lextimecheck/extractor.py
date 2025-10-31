"""
LLM-based norm extraction from legal texts.

Extracts formal norms (obligations, permissions, prohibitions) with temporal
information using LLM APIs (OpenAI or Anthropic).
"""

import json
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from pydantic import ValidationError

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from lextimecheck.schemas import Norm, LegalSection, Modality, AuthorityLevel
from dateutil import parser as date_parser


logger = logging.getLogger(__name__)


class LLMClient:
    """Base class for LLM clients."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
    
    def extract(self, prompt: str) -> str:
        """Extract text using the LLM."""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        super().__init__(api_key, model)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def extract(self, prompt: str) -> str:
        """Extract using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal expert specialized in analyzing legal texts and extracting formal norms. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229"
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        
        super().__init__(api_key, model)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def extract(self, prompt: str) -> str:
        """Extract using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class NormExtractor:
    """Extracts norms from legal sections using LLMs."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_template_path: str = "prompts/norm_extraction.txt",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the norm extractor.
        
        Args:
            llm_client: LLM client to use for extraction
            prompt_template_path: Path to prompt template file
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.llm_client = llm_client
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Load prompt template
        prompt_path = Path(prompt_template_path)
        if not prompt_path.exists():
            # Try relative to package
            prompt_path = Path(__file__).parent.parent / prompt_template_path
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def extract_norms(self, section: LegalSection) -> List[Norm]:
        """
        Extract norms from a legal section.
        
        Args:
            section: LegalSection to extract norms from
        
        Returns:
            List of Norm objects
        """
        # Build prompt
        prompt = self.prompt_template.format(
            text=section.text,
            section_id=section.section_id,
            version_id=section.version_id,
            corpus_name=section.corpus_name
        )
        
        # Extract with retries
        for attempt in range(self.max_retries):
            try:
                raw_response = self.llm_client.extract(prompt)
                norms = self._parse_response(raw_response, section)
                return norms
            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All extraction attempts failed for {section.section_id}")
                    return []
        
        return []
    
    def _parse_response(self, response: str, section: LegalSection) -> List[Norm]:
        """
        Parse LLM response into Norm objects.
        
        Args:
            response: Raw LLM response
            section: Source LegalSection
        
        Returns:
            List of Norm objects
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            json_str = json_str.strip()
        
        if json_str.startswith("```json"):
            json_str = json_str[7:].strip()
        
        if json_str.endswith("```"):
            json_str = json_str[:-3].strip()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {json_str}")
            return []
        
        if not isinstance(data, list):
            logger.error("Response is not a JSON array")
            return []
        
        norms = []
        for item in data:
            try:
                norm = self._create_norm(item, section)
                norms.append(norm)
            except (ValidationError, ValueError) as e:
                logger.warning(f"Failed to create norm from item: {e}")
                logger.debug(f"Item was: {item}")
                continue
        
        return norms
    
    def _create_norm(self, data: Dict[str, Any], section: LegalSection) -> Norm:
        """
        Create a Norm object from extracted data.
        
        Args:
            data: Extracted norm data
            section: Source LegalSection
        
        Returns:
            Norm object
        """
        # Parse modality
        modality_str = data.get("modality", "").upper()
        if modality_str not in ["O", "P", "F"]:
            raise ValueError(f"Invalid modality: {modality_str}")
        modality = Modality(modality_str)
        
        # Parse dates
        effective_start = self._parse_date(data.get("effective_start"))
        effective_end = self._parse_date(data.get("effective_end"))
        
        # Use section dates as fallback
        if not effective_start and section.effective_date:
            effective_start = section.effective_date
        
        # Parse exceptions
        exceptions = data.get("exceptions", [])
        if exceptions and not isinstance(exceptions, list):
            exceptions = [str(exceptions)]
        
        # Create norm
        norm = Norm(
            modality=modality,
            subject=data.get("subject", ""),
            action=data.get("action", ""),
            object=data.get("object"),
            conditions=data.get("conditions"),
            jurisdiction=data.get("jurisdiction"),
            exceptions=exceptions,
            effective_start=effective_start,
            effective_end=effective_end,
            source_id=section.section_id,
            version_id=section.version_id,
            authority_level=section.authority_level,
            enactment_date=section.enactment_date,
            text_snippet=data.get("text_snippet"),
            specificity_score=float(data.get("specificity_score", 0.5))
        )
        
        return norm
    
    def _parse_date(self, date_str: Optional[str]) -> Optional:
        """Parse a date string into datetime object."""
        if not date_str or date_str == "null":
            return None
        
        try:
            # Try ISO format first
            from datetime import datetime
            if isinstance(date_str, str):
                # Handle various date formats
                return date_parser.parse(date_str)
            return None
        except (ValueError, TypeError):
            return None
    
    def extract_batch(
        self,
        sections: List[LegalSection],
        show_progress: bool = True
    ) -> Dict[str, List[Norm]]:
        """
        Extract norms from multiple sections.
        
        Args:
            sections: List of LegalSection objects
            show_progress: Whether to show progress
        
        Returns:
            Dictionary mapping section_id to list of Norm objects
        """
        results = {}
        
        for i, section in enumerate(sections):
            if show_progress:
                print(f"Processing {i+1}/{len(sections)}: {section.section_id}")
            
            norms = self.extract_norms(section)
            results[section.section_id] = norms
            
            if show_progress:
                print(f"  → Extracted {len(norms)} norms")
        
        return results
    
    def save_norms(self, norms: List[Norm], output_path: str):
        """
        Save norms to JSON file.
        
        Args:
            norms: List of Norm objects
            output_path: Path to save JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                [n.model_dump(mode='json') for n in norms],
                f,
                indent=2,
                default=str
            )
    
    def load_norms(self, input_path: str) -> List[Norm]:
        """
        Load norms from JSON file.
        
        Args:
            input_path: Path to JSON file
        
        Returns:
            List of Norm objects
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Norm(**item) for item in data]


def create_llm_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> LLMClient:
    """
    Create an LLM client.
    
    Args:
        provider: LLM provider ('openai' or 'anthropic')
        api_key: API key (optional, will use env var if not provided)
        model: Model name (optional, will use default)
    
    Returns:
        LLMClient instance
    """
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAIClient(api_key=api_key, model=model or "gpt-4-turbo-preview")
    elif provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model or "claude-3-sonnet-20240229")
    else:
        raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <corpus_name>")
        sys.exit(1)
    
    corpus_name = sys.argv[1]
    
    # Load sections
    from lextimecheck.ingestor import CorpusIngestor
    ingestor = CorpusIngestor()
    sections = ingestor.load_corpus(corpus_name)
    
    print(f"Loaded {len(sections)} sections from {corpus_name}")
    
    # Create extractor
    provider = os.getenv("LLM_PROVIDER", "openai")
    client = create_llm_client(provider)
    extractor = NormExtractor(client)
    
    # Extract norms
    results = extractor.extract_batch(sections)
    
    # Save results
    all_norms = []
    for section_id, norms in results.items():
        all_norms.extend(norms)
    
    output_path = f"outputs/norms_{corpus_name}.json"
    extractor.save_norms(all_norms, output_path)
    
    print(f"\nExtracted {len(all_norms)} total norms")
    print(f"Saved to {output_path}")


"""
Version and section ingestion for legal texts.

Loads multiple versions of legal texts, splits them into sections,
and prepares them for norm extraction.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from lextimecheck.schemas import LegalSection, AuthorityLevel


class CorpusIngestor:
    """Loads and processes legal text corpora."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the ingestor.
        
        Args:
            data_dir: Base directory containing corpus data
        """
        self.data_dir = Path(data_dir)
    
    def load_corpus(self, corpus_name: str) -> List[LegalSection]:
        """
        Load a complete corpus with all versions.
        
        Args:
            corpus_name: Name of the corpus (e.g., 'eu_ai_act', 'nyc_aedt', 'fre_702')
        
        Returns:
            List of LegalSection objects
        """
        corpus_dir = self.data_dir / corpus_name
        if not corpus_dir.exists():
            raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")
        
        # Load corpus metadata
        metadata_path = corpus_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                corpus_metadata = json.load(f)
        else:
            corpus_metadata = {}
        
        sections = []
        
        # Load all version files
        for version_file in sorted(corpus_dir.glob("*.txt")):
            version_sections = self._load_version(
                corpus_name,
                version_file,
                corpus_metadata.get(version_file.stem, {})
            )
            sections.extend(version_sections)
        
        return sections
    
    def _load_version(
        self,
        corpus_name: str,
        file_path: Path,
        metadata: Dict
    ) -> List[LegalSection]:
        """
        Load a single version file and split into sections.
        
        Args:
            corpus_name: Name of the corpus
            file_path: Path to the version file
            metadata: Version metadata
        
        Returns:
            List of LegalSection objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        version_id = file_path.stem
        
        # Parse dates from metadata
        effective_date = self._parse_date(metadata.get('effective_date'))
        enactment_date = self._parse_date(metadata.get('enactment_date'))
        
        # Parse authority level
        authority_level = AuthorityLevel(metadata.get('authority_level', 'statute'))
        
        # Split into sections
        sections = self.split_sections(text, version_id, corpus_name)
        
        # Add metadata to each section
        for section in sections:
            section.effective_date = effective_date
            section.enactment_date = enactment_date
            section.authority_level = authority_level
            section.source_url = metadata.get('source_url')
            section.metadata = metadata
        
        return sections
    
    def split_sections(
        self,
        text: str,
        version_id: str,
        corpus_name: str
    ) -> List[LegalSection]:
        """
        Split text into numbered sections.
        
        Args:
            text: Full text to split
            version_id: Version identifier
            corpus_name: Name of the corpus
        
        Returns:
            List of LegalSection objects
        """
        sections = []
        
        # Try different section patterns based on corpus type
        if corpus_name == 'eu_ai_act':
            sections = self._split_eu_sections(text, version_id, corpus_name)
        elif corpus_name == 'nyc_aedt':
            sections = self._split_nyc_sections(text, version_id, corpus_name)
        elif corpus_name == 'fre_702':
            sections = self._split_fre_sections(text, version_id, corpus_name)
        else:
            # Generic splitting
            sections = self._split_generic_sections(text, version_id, corpus_name)
        
        return sections
    
    def _split_eu_sections(
        self,
        text: str,
        version_id: str,
        corpus_name: str
    ) -> List[LegalSection]:
        """Split EU regulation text into articles."""
        sections = []
        
        # Pattern for "Article X" or "Article X."
        article_pattern = r'Article\s+(\d+[a-z]?)\s*[:\.]?\s*([^\n]+)?'
        matches = list(re.finditer(article_pattern, text, re.IGNORECASE))
        
        for i, match in enumerate(matches):
            article_num = match.group(1)
            title = match.group(2).strip() if match.group(2) else None
            
            # Extract text until next article or end
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            
            section_id = f"{corpus_name}_article_{article_num}_{version_id}"
            
            sections.append(LegalSection(
                section_id=section_id,
                version_id=version_id,
                corpus_name=corpus_name,
                title=title or f"Article {article_num}",
                text=section_text
            ))
        
        return sections
    
    def _split_nyc_sections(
        self,
        text: str,
        version_id: str,
        corpus_name: str
    ) -> List[LegalSection]:
        """Split NYC local law text into sections."""
        sections = []
        
        # Pattern for "§ X" or "Section X"
        section_pattern = r'(?:§|Section)\s+(\d+-\d+|\d+)\s*[:\.]?\s*([^\n]+)?'
        matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            title = match.group(2).strip() if match.group(2) else None
            
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            
            section_id = f"{corpus_name}_section_{section_num}_{version_id}"
            
            sections.append(LegalSection(
                section_id=section_id,
                version_id=version_id,
                corpus_name=corpus_name,
                title=title or f"Section {section_num}",
                text=section_text
            ))
        
        return sections
    
    def _split_fre_sections(
        self,
        text: str,
        version_id: str,
        corpus_name: str
    ) -> List[LegalSection]:
        """Split Federal Rules of Evidence text."""
        sections = []
        
        # Pattern for "Rule XXX"
        rule_pattern = r'Rule\s+(\d+[a-z]?)\s*[:\.]?\s*([^\n]+)?'
        matches = list(re.finditer(rule_pattern, text, re.IGNORECASE))
        
        for i, match in enumerate(matches):
            rule_num = match.group(1)
            title = match.group(2).strip() if match.group(2) else None
            
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            
            section_id = f"{corpus_name}_rule_{rule_num}_{version_id}"
            
            sections.append(LegalSection(
                section_id=section_id,
                version_id=version_id,
                corpus_name=corpus_name,
                title=title or f"Rule {rule_num}",
                text=section_text
            ))
        
        return sections
    
    def _split_generic_sections(
        self,
        text: str,
        version_id: str,
        corpus_name: str
    ) -> List[LegalSection]:
        """Generic section splitting by paragraphs."""
        # Split by double newlines
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        sections = []
        for i, para in enumerate(paragraphs, 1):
            section_id = f"{corpus_name}_para_{i}_{version_id}"
            
            sections.append(LegalSection(
                section_id=section_id,
                version_id=version_id,
                corpus_name=corpus_name,
                title=f"Paragraph {i}",
                text=para
            ))
        
        return sections
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string into datetime object."""
        if not date_str:
            return None
        
        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%d %B %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def save_sections(self, sections: List[LegalSection], output_path: str):
        """
        Save sections to JSON file.
        
        Args:
            sections: List of LegalSection objects
            output_path: Path to save JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                [s.model_dump(mode='json') for s in sections],
                f,
                indent=2,
                default=str
            )
    
    def load_sections(self, input_path: str) -> List[LegalSection]:
        """
        Load sections from JSON file.
        
        Args:
            input_path: Path to JSON file
        
        Returns:
            List of LegalSection objects
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [LegalSection(**item) for item in data]


def create_sample_corpus_files():
    """Create sample corpus files with metadata for testing."""
    
    # EU AI Act Article 50
    eu_dir = Path("data/eu_ai_act")
    eu_dir.mkdir(parents=True, exist_ok=True)
    
    eu_metadata = {
        "pre_application": {
            "effective_date": "2024-08-01",
            "enactment_date": "2024-07-12",
            "authority_level": "regulation",
            "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        },
        "application": {
            "effective_date": "2026-08-02",
            "enactment_date": "2024-07-12",
            "authority_level": "regulation",
            "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        }
    }
    
    with open(eu_dir / "metadata.json", 'w') as f:
        json.dump(eu_metadata, f, indent=2)
    
    # NYC AEDT
    nyc_dir = Path("data/nyc_aedt")
    nyc_dir.mkdir(parents=True, exist_ok=True)
    
    nyc_metadata = {
        "local_law": {
            "effective_date": "2023-01-01",
            "enactment_date": "2021-11-11",
            "authority_level": "statute",
            "source_url": "https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=4344524"
        },
        "final_rules": {
            "effective_date": "2023-07-05",
            "enactment_date": "2023-04-06",
            "authority_level": "regulation",
            "source_url": "https://rules.cityofnewyork.us/rule/automated-employment-decision-tools/"
        }
    }
    
    with open(nyc_dir / "metadata.json", 'w') as f:
        json.dump(nyc_metadata, f, indent=2)
    
    # FRE 702
    fre_dir = Path("data/fre_702")
    fre_dir.mkdir(parents=True, exist_ok=True)
    
    fre_metadata = {
        "pre_amendment": {
            "effective_date": "2000-12-01",
            "enactment_date": "2000-04-17",
            "authority_level": "statute",
            "source_url": "https://www.uscourts.gov/rules-policies/archives/committee-reports/advisory-committee-rules-evidence-spring-2000"
        },
        "post_amendment": {
            "effective_date": "2023-12-01",
            "enactment_date": "2023-04-26",
            "authority_level": "statute",
            "source_url": "https://www.uscourts.gov/rules-policies/current-rules-practice-procedure/federal-rules-evidence"
        }
    }
    
    with open(fre_dir / "metadata.json", 'w') as f:
        json.dump(fre_metadata, f, indent=2)


if __name__ == "__main__":
    # Create sample corpus structure
    create_sample_corpus_files()
    print("Sample corpus structure created.")


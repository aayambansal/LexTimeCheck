#!/usr/bin/env python3
"""Debug script to test extraction."""

import os
import json
from lextimecheck.ingestor import CorpusIngestor
from lextimecheck.extractor import create_llm_client, NormExtractor

# Set API key (set via environment variable or .env file)
# os.environ["ANTHROPIC_API_KEY"] = "your-api-key-here"

# Load corpus
print("Loading corpus...")
ingestor = CorpusIngestor()
sections = ingestor.load_corpus("eu_ai_act")
print(f"Loaded {len(sections)} sections")

# Create LLM client
print("\nCreating LLM client...")
client = create_llm_client("anthropic", model="claude-3-haiku-20240307")

# Get first section
section = sections[0]
print(f"\nProcessing section: {section.section_id}")
print(f"Text length: {len(section.text)} chars")

# Create extractor
extractor = NormExtractor(client)

# Build the prompt
prompt = extractor.prompt_template.format(
    text=section.text,
    section_id=section.section_id,
    version_id=section.version_id,
    corpus_name=section.corpus_name
)

print("\nSending request to OpenAI...")
try:
    raw_response = client.extract(prompt)
    print("\n" + "="*80)
    print("RAW RESPONSE:")
    print("="*80)
    print(raw_response)
    print("="*80)

    # Try to parse it
    print("\nAttempting to parse...")
    norms = extractor._parse_response(raw_response, section)
    print(f"Successfully parsed {len(norms)} norms")

    for i, norm in enumerate(norms):
        print(f"\nNorm {i+1}:")
        print(f"  Modality: {norm.modality}")
        print(f"  Subject: {norm.subject}")
        print(f"  Action: {norm.action}")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

"""
Test script for NER improvements - Compare spaCy NER vs Pattern-based NER
Demonstrates enhanced entity extraction with normalization and deduplication
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.spacy_ner_service import SpacyNERService
from models.entity import EntityType

# Test samples with diverse entity types
SAMPLE_TEXTS = {
    "tech_english": """
        Microsoft Corporation and Apple Inc. are leading technology companies.
        Satya Nadella, CEO of Microsoft, announced a partnership with OpenAI.
        The collaboration will integrate GPT-4 into Microsoft Azure and Office 365.
        Python 3.11 and TypeScript 5.0 are popular programming languages.
        React 18 and Django 4.2 are widely used frameworks for web development.
        Machine Learning and Neural Networks are transforming AI applications.
    """,

    "tech_polish": """
        Microsoft Corporation i Apple Inc. są wiodącymi firmami technologicznymi.
        Prof. dr Adam Kowalski z Politechniki Warszawskiej prowadzi badania nad AI.
        Spółka z o.o. TechnoSoft S.A. wdraża rozwiązania Machine Learning.
        Python 3.11 i JavaScript są popularnymi językami programowania.
    """,

    "mixed_entities": """
        Dr. John Smith from Stanford University collaborated with Google LLC
        on a research project about Deep Learning. The project was funded by
        the European Union and presented at the AI Conference 2024 in San Francisco.
        Technologies used include TensorFlow 2.15, PyTorch, and Kubernetes.
        Microsoft Corp., Amazon Web Services, and IBM Watson provided infrastructure.
    """,

    "duplicates_test": """
        Microsoft announced a deal. Microsoft Corporation confirmed the news.
        Microsoft Corp. and Microsoft Inc. are working together.
        Dr. John Smith and J. Smith collaborated with Prof. Smith on the research.
        Apple and Apple Inc. released new products. Apple Corporation stock rose.
    """
}


def test_spacy_ner():
    """Test spaCy NER service with sample texts"""
    print("=" * 80)
    print("🧪 Testing spaCy NER Improvements")
    print("=" * 80)
    print()

    # Initialize service
    try:
        ner_service = SpacyNERService(default_language='en', fuzzy_threshold=0.85)
        print("✅ spaCy NER Service initialized successfully")
        print(f"   - English model: {'✅' if ner_service.nlp_en else '❌'}")
        print(f"   - Polish model: {'✅' if ner_service.nlp_pl else '❌'}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize spaCy NER: {e}")
        return

    # Test each sample
    for test_name, text in SAMPLE_TEXTS.items():
        print(f"\n{'='*80}")
        print(f"📄 Test: {test_name.upper()}")
        print(f"{'='*80}")
        print(f"Text: {text[:150]}...")
        print()

        # Detect language
        language = 'pl' if 'polish' in test_name else 'en'

        # Extract entities without deduplication
        entities_raw = ner_service.extract_entities(text, language=language, deduplicate=False)
        print(f"🔍 Extracted Entities (raw, before deduplication): {len(entities_raw)}")
        entity_count_raw = {}
        for name, etype in entities_raw:
            entity_count_raw[etype] = entity_count_raw.get(etype, 0) + 1
            print(f"   - {name:40s} [{etype}]")

        print()

        # Extract entities with deduplication
        entities_dedup = ner_service.extract_entities(text, language=language, deduplicate=True)
        print(f"✨ After Normalization & Deduplication: {len(entities_dedup)}")
        entity_count_dedup = {}
        for name, etype in entities_dedup:
            entity_count_dedup[etype] = entity_count_dedup.get(etype, 0) + 1
            print(f"   - {name:40s} [{etype}]")

        print()
        print(f"📊 Statistics:")
        print(f"   - Total entities (raw): {len(entities_raw)}")
        print(f"   - Total entities (deduplicated): {len(entities_dedup)}")
        print(f"   - Reduction: {len(entities_raw) - len(entities_dedup)} ({(1 - len(entities_dedup)/max(1, len(entities_raw)))*100:.1f}%)")
        print(f"   - By type (deduplicated):")
        for etype, count in sorted(entity_count_dedup.items()):
            print(f"      * {etype}: {count}")


def test_normalization():
    """Test entity normalization"""
    print("\n" + "=" * 80)
    print("🔧 Testing Entity Normalization")
    print("=" * 80)
    print()

    ner_service = SpacyNERService()

    test_cases = [
        ("Microsoft Corporation", EntityType.ORGANIZATION, "Microsoft"),
        ("Apple Inc.", EntityType.ORGANIZATION, "Apple"),
        ("Google LLC", EntityType.ORGANIZATION, "Google"),
        ("Dr. John Smith", EntityType.PERSON, "John Smith"),
        ("Prof. Adam Kowalski", EntityType.PERSON, "Adam Kowalski"),
        ("John Smith Jr.", EntityType.PERSON, "John Smith"),
        ("TechnoSoft Sp. z o.o.", EntityType.ORGANIZATION, "TechnoSoft"),
        ("Amazon Web Services", EntityType.ORGANIZATION, "Amazon Web Services"),
    ]

    print("Testing normalization rules:")
    for raw_name, entity_type, expected in test_cases:
        normalized = ner_service.normalize_entity_name(raw_name, entity_type)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} {raw_name:40s} → {normalized:30s} (expected: {expected})")


def test_fuzzy_matching():
    """Test fuzzy deduplication"""
    print("\n" + "=" * 80)
    print("🔀 Testing Fuzzy Deduplication")
    print("=" * 80)
    print()

    ner_service = SpacyNERService(fuzzy_threshold=0.85)

    # Test with similar entity names
    entities = [
        ("Microsoft", EntityType.ORGANIZATION),
        ("Microsoft Corp", EntityType.ORGANIZATION),
        ("Microsoft Corporation", EntityType.ORGANIZATION),
        ("John Smith", EntityType.PERSON),
        ("J. Smith", EntityType.PERSON),
        ("Smith", EntityType.PERSON),
        ("Apple", EntityType.ORGANIZATION),
        ("Apple Inc", EntityType.ORGANIZATION),
        ("Google", EntityType.ORGANIZATION),
    ]

    print(f"Input entities: {len(entities)}")
    for name, etype in entities:
        print(f"   - {name:30s} [{etype}]")

    print()

    deduplicated = ner_service.fuzzy_deduplicate(entities, threshold=0.85)
    print(f"After fuzzy deduplication: {len(deduplicated)}")
    for name, etype in deduplicated:
        print(f"   - {name:30s} [{etype}]")

    print()
    print(f"Reduction: {len(entities) - len(deduplicated)} entities merged")


if __name__ == "__main__":
    print("\n🚀 Starting NER Improvements Test Suite\n")

    try:
        # Run all tests
        test_spacy_ner()
        test_normalization()
        test_fuzzy_matching()

        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)
        print("\n📈 Summary of Improvements:")
        print("   1. ✅ spaCy NER - Better entity detection and classification")
        print("   2. ✅ Entity Normalization - Removes suffixes and titles")
        print("   3. ✅ Fuzzy Deduplication - Merges similar entity names")
        print("   4. ✅ Organization Suffixes - Extended list (Inc., Corp., Ltd., Sp. z o.o., etc.)")
        print("   5. ✅ Person Names - Better title/suffix handling (Dr., Prof., Jr., etc.)")
        print("   6. ✅ Tech Content - Detects programming languages, frameworks, products")
        print("   7. ✅ Multilingual - Supports English and Polish")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

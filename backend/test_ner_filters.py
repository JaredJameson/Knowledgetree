"""
Test NER improvements - filters and custom classification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.spacy_ner_service import SpacyNERService
from models.entity import EntityType


def test_filters():
    """Test new entity filters"""

    ner = SpacyNERService()

    print("=" * 80)
    print("🧪 Testing NER Improvements - Filters")
    print("=" * 80)
    print()

    # Test cases for new filters
    test_cases = [
        {
            "text": "Introducing Claude Sonnet 4.5, the new AI model.",
            "expected_filtered": ["Introducing Claude Sonnet", "Introducing Claude Sonnet 4.5"],
            "description": "Should filter 'Introducing X' fragments"
        },
        {
            "text": "Claude Code Claude Code is a new tool.",
            "expected_filtered": ["Claude Code Claude Code"],
            "description": "Should filter duplicate text artifacts"
        },
        {
            "text": "We recruited many engineers for the project.",
            "expected_filtered": ["We recruited"],
            "description": "Should filter 'We X' fragments"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"   Text: {test['text']}")

        # Extract entities (with deduplication)
        entities = ner.extract_entities(test['text'], language='en', deduplicate=True)

        print(f"   Extracted entities: {len(entities)}")
        for name, etype in entities:
            print(f"      • {name} [{etype}]")

        # Check if expected filtered entities are NOT in results
        filtered_correctly = all(
            not any(expected in name for name, _ in entities)
            for expected in test.get('expected_filtered', [])
        )

        status = "✅ PASS" if filtered_correctly else "❌ FAIL"
        print(f"   {status}")
        print()


def test_custom_classification():
    """Test custom classification rules"""

    ner = SpacyNERService()

    print("=" * 80)
    print("🧪 Testing NER Improvements - Custom Classification")
    print("=" * 80)
    print()

    # Test cases for classification
    test_cases = [
        {
            "text": "Anthropic and OpenAI are leading AI companies.",
            "expected": [("Anthropic", EntityType.ORGANIZATION), ("OpenAI", EntityType.ORGANIZATION)],
            "description": "AI companies should be ORGANIZATION"
        },
        {
            "text": "Claude Sonnet 4.5 and GPT-4 are powerful AI models.",
            "expected": [("Claude Sonnet", EntityType.CONCEPT), ("GPT", EntityType.CONCEPT)],
            "description": "AI models should be CONCEPT"
        },
        {
            "text": "GitHub, Jira, and Twitter are popular platforms.",
            "expected": [("GitHub", EntityType.ORGANIZATION), ("Jira", EntityType.ORGANIZATION), ("Twitter", EntityType.ORGANIZATION)],
            "description": "Tech platforms should be ORGANIZATION"
        },
        {
            "text": "The API and SDK documentation is available.",
            "expected": [("API", EntityType.CONCEPT), ("SDK", EntityType.CONCEPT)],
            "description": "API/SDK should be CONCEPT"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"   Text: {test['text']}")

        # Extract entities
        entities = ner.extract_entities(test['text'], language='en', deduplicate=True)

        print(f"   Extracted entities: {len(entities)}")
        for name, etype in entities:
            print(f"      • {name} [{etype}]")

        # Check if expected classifications are correct
        classification_correct = True
        for expected_name, expected_type in test.get('expected', []):
            # Check if entity with similar name exists with correct type
            found = any(
                expected_name.lower() in name.lower() and etype == expected_type
                for name, etype in entities
            )
            if not found:
                classification_correct = False
                print(f"   ⚠️  Expected '{expected_name}' as {expected_type} but not found")

        status = "✅ PASS" if classification_correct else "❌ FAIL"
        print(f"   {status}")
        print()


def test_real_data_sample():
    """Test on real data sample"""

    ner = SpacyNERService()

    print("=" * 80)
    print("🧪 Testing on Real Data Sample")
    print("=" * 80)
    print()

    # Sample from actual documents
    text = """
    Introducing Claude Sonnet 4.5, Anthropic's flagship AI model.
    Claude Code is a powerful tool that integrates with GitHub and Jira.
    The API documentation covers both Claude and GPT models.
    We recruited top engineers from Twitter and Microsoft.
    """

    print("Sample text:")
    print(text)
    print()

    entities = ner.extract_entities(text, language='en', deduplicate=True)

    print(f"Extracted {len(entities)} entities:")
    print()

    # Group by type
    by_type = {}
    for name, etype in entities:
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(name)

    for etype in [EntityType.ORGANIZATION, EntityType.CONCEPT, EntityType.PERSON]:
        if etype in by_type:
            print(f"{etype.upper()}:")
            for name in sorted(by_type[etype]):
                print(f"   • {name}")
            print()

    # Check quality metrics
    total = len(entities)
    org_count = len(by_type.get(EntityType.ORGANIZATION, []))
    concept_count = len(by_type.get(EntityType.CONCEPT, []))
    person_count = len(by_type.get(EntityType.PERSON, []))

    # Check for known issues
    issues = []
    for name, etype in entities:
        name_lower = name.lower()
        # Check for "Introducing X" that slipped through
        if name_lower.startswith('introducing'):
            issues.append(f"'Introducing X' fragment: {name}")
        # Check for duplicates
        words = name.split()
        if len(words) >= 2 and len(words) % 2 == 0:
            mid = len(words) // 2
            if ' '.join(words[:mid]) == ' '.join(words[mid:]):
                issues.append(f"Duplicate text: {name}")
        # Check for "We X" fragments
        if name_lower.startswith('we '):
            issues.append(f"'We X' fragment: {name}")

    print("Quality Assessment:")
    print(f"   Total entities: {total}")
    print(f"   Organizations: {org_count}")
    print(f"   Concepts: {concept_count}")
    print(f"   Persons: {person_count}")
    print()

    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("✅ No known issues detected!")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 NER Improvements Test Suite")
    print("=" * 80)
    print()

    try:
        test_filters()
        test_custom_classification()
        test_real_data_sample()

        print("=" * 80)
        print("✅ Test suite completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

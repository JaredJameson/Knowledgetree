"""
Debug fuzzy deduplication algorithm
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.spacy_ner_service import SpacyNERService
from models.entity import EntityType


def test_fuzzy_dedup():
    """Test fuzzy deduplication with known cases"""

    ner = SpacyNERService(fuzzy_threshold=0.85)

    print("=" * 80)
    print("🔍 Testing Fuzzy Deduplication Algorithm")
    print("=" * 80)

    # Test case 1: Should merge similar names
    print("\n📋 Test 1: Similar organization names")
    entities1 = [
        ("Microsoft", EntityType.ORGANIZATION),
        ("Microsoft Corp", EntityType.ORGANIZATION),
        ("Microsoft Corporation", EntityType.ORGANIZATION),
    ]

    print("Input:")
    for name, etype in entities1:
        print(f"   - {name:40s} [{etype}]")

    # Test similarity scores
    print("\nSimilarity scores:")
    for i, (name1, _) in enumerate(entities1):
        for name2, _ in entities1[i+1:]:
            sim = ner._calculate_similarity(name1, name2)
            status = "✓" if sim >= 0.85 else "✗"
            print(f"   {status} '{name1}' vs '{name2}': {sim:.3f}")

    result1 = ner.fuzzy_deduplicate(entities1, threshold=0.85)
    print(f"\nOutput ({len(result1)} entities):")
    for name, etype in result1:
        print(f"   - {name:40s} [{etype}]")

    expected_count = 1
    status = "✅ PASS" if len(result1) == expected_count else f"❌ FAIL (expected {expected_count})"
    print(f"\n{status}\n")

    # Test case 2: Claude variants
    print("=" * 80)
    print("📋 Test 2: Claude product names")
    entities2 = [
        ("Claude Sonnet 4.5", EntityType.PERSON),
        ("Claude Sonnet 4", EntityType.PERSON),
        ("Claude", EntityType.PERSON),
    ]

    print("Input:")
    for name, etype in entities2:
        print(f"   - {name:40s} [{etype}]")

    # Test similarity scores
    print("\nSimilarity scores:")
    for i, (name1, _) in enumerate(entities2):
        for name2, _ in entities2[i+1:]:
            sim = ner._calculate_similarity(name1, name2)
            status = "✓" if sim >= 0.85 else "✗"
            print(f"   {status} '{name1}' vs '{name2}': {sim:.3f}")

    result2 = ner.fuzzy_deduplicate(entities2, threshold=0.85)
    print(f"\nOutput ({len(result2)} entities):")
    for name, etype in result2:
        print(f"   - {name:40s} [{etype}]")

    expected_count = 2  # Claude Sonnet 4.5 + Claude (below threshold)
    status = "✅ PASS" if len(result2) == expected_count else f"❌ FAIL (expected {expected_count})"
    print(f"\n{status}\n")

    # Test case 3: Exact duplicates
    print("=" * 80)
    print("📋 Test 3: Exact duplicates")
    entities3 = [
        ("Claude Sonnet", EntityType.CONCEPT),
        ("Claude Sonnet", EntityType.CONCEPT),
        ("Claude Sonnet", EntityType.CONCEPT),
    ]

    print("Input:")
    for name, etype in entities3:
        print(f"   - {name:40s} [{etype}]")

    result3 = ner.fuzzy_deduplicate(entities3, threshold=0.85)
    print(f"\nOutput ({len(result3)} entities):")
    for name, etype in result3:
        print(f"   - {name:40s} [{etype}]")

    expected_count = 1
    status = "✅ PASS" if len(result3) == expected_count else f"❌ FAIL (expected {expected_count})"
    print(f"\n{status}\n")

    # Test case 4: Mixed types - should NOT merge
    print("=" * 80)
    print("📋 Test 4: Same name, different types (should NOT merge)")
    entities4 = [
        ("Claude", EntityType.ORGANIZATION),
        ("Claude", EntityType.PERSON),
    ]

    print("Input:")
    for name, etype in entities4:
        print(f"   - {name:40s} [{etype}]")

    result4 = ner.fuzzy_deduplicate(entities4, threshold=0.85)
    print(f"\nOutput ({len(result4)} entities):")
    for name, etype in result4:
        print(f"   - {name:40s} [{etype}]")

    expected_count = 2  # Different types, should stay separate
    status = "✅ PASS" if len(result4) == expected_count else f"❌ FAIL (expected {expected_count})"
    print(f"\n{status}\n")

    print("=" * 80)
    print("🏁 Debug Testing Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_fuzzy_dedup()

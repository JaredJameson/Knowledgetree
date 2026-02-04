"""
Debug entity normalization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.spacy_ner_service import SpacyNERService
from models.entity import EntityType


def test_normalization():
    """Test entity normalization"""

    ner = SpacyNERService()

    print("=" * 80)
    print("🔧 Testing Entity Normalization")
    print("=" * 80)

    test_cases = [
        ("Microsoft Corporation", EntityType.ORGANIZATION, "Microsoft"),
        ("Microsoft Corp", EntityType.ORGANIZATION, "Microsoft"),
        ("Microsoft Corp.", EntityType.ORGANIZATION, "Microsoft"),
        ("Apple Inc.", EntityType.ORGANIZATION, "Apple"),
        ("Google LLC", EntityType.ORGANIZATION, "Google"),
        ("Amazon Web Services", EntityType.ORGANIZATION, "Amazon Web Services"),  # Services is a suffix!
        ("TechnoSoft Sp. z o.o.", EntityType.ORGANIZATION, "TechnoSoft"),
        ("Dr. John Smith", EntityType.PERSON, "John Smith"),
        ("Prof. Adam Kowalski", EntityType.PERSON, "Adam Kowalski"),
    ]

    print("\nNormalization results:")
    for raw_name, entity_type, expected in test_cases:
        normalized = ner.normalize_entity_name(raw_name, entity_type)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} {raw_name:35s} → {normalized:25s} (expected: {expected})")

    print("\n" + "=" * 80)
    print("🏁 Normalization Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_normalization()

"""
KnowledgeTree Backend - Command Parser Service
Parse chat commands for artifact generation
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.artifact import ArtifactType
from models.category import Category

logger = logging.getLogger(__name__)


class CommandParser:
    """
    Service for parsing chat commands to trigger artifact generation

    Supported command patterns:
    - "summarize chapter 3"
    - "create summary of chapter 3"
    - "generate notes for section 2.1"
    - "write article about neural networks"
    - "make outline of chapter 5"
    - "create comparison between chapters 2 and 3"
    - "explain the concept of backpropagation"
    - "extract key points from chapter 1"
    """

    # Command verbs that trigger artifact generation
    COMMAND_VERBS = [
        "summarize", "summary",
        "create", "generate", "make", "write",
        "explain", "explanation",
        "extract",
        "outline",
        "compare", "comparison",
        "notes",
    ]

    # Artifact type mappings from command text
    TYPE_KEYWORDS = {
        ArtifactType.SUMMARY: ["summarize", "summary"],
        ArtifactType.ARTICLE: ["article", "write about"],
        ArtifactType.EXTRACT: ["extract", "key points", "highlights"],
        ArtifactType.NOTES: ["notes", "study notes"],
        ArtifactType.OUTLINE: ["outline", "structure"],
        ArtifactType.COMPARISON: ["compare", "comparison", "versus", "vs"],
        ArtifactType.EXPLANATION: ["explain", "explanation", "how does", "what is"],
    }

    # Chapter/section pattern: "chapter 3", "section 2.1", "ch 5"
    CHAPTER_PATTERN = re.compile(
        r'\b(?:chapter|ch\.?|section|sec\.?)\s+(\d+(?:\.\d+)?)\b',
        re.IGNORECASE
    )

    # Category reference pattern: "of chapter X", "for section Y", "about chapter Z"
    CATEGORY_REF_PATTERN = re.compile(
        r'\b(?:of|for|about|from|in)\s+(?:chapter|ch\.?|section|sec\.?)\s+(\d+(?:\.\d+)?)\b',
        re.IGNORECASE
    )

    def is_command(self, message: str) -> bool:
        """
        Check if message is an artifact generation command

        Args:
            message: User message

        Returns:
            True if message starts with a command verb
        """
        message_lower = message.lower().strip()

        # Check if message starts with command verb
        for verb in self.COMMAND_VERBS:
            if message_lower.startswith(verb):
                return True

        return False

    def parse_command(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse artifact generation command

        Args:
            message: User message (e.g., "summarize chapter 3")

        Returns:
            Command data dict with:
            - artifact_type: ArtifactType
            - title: Generated title
            - query: Search query for content retrieval
            - category_identifier: Chapter/section number (e.g., "3", "2.1")
            - instructions: Optional custom instructions

            Returns None if not a valid command
        """
        if not self.is_command(message):
            return None

        message_lower = message.lower().strip()

        # Detect artifact type
        artifact_type = self._detect_artifact_type(message_lower)

        # Extract chapter/section reference
        category_identifier = self._extract_category_identifier(message)

        # Generate title
        title = self._generate_title(message, artifact_type, category_identifier)

        # Generate search query
        query = self._generate_query(message, category_identifier)

        # Extract custom instructions (text after main command)
        instructions = self._extract_instructions(message)

        logger.info(
            f"Parsed command: type={artifact_type}, "
            f"category={category_identifier}, query={query[:50]}"
        )

        return {
            "artifact_type": artifact_type,
            "title": title,
            "query": query,
            "category_identifier": category_identifier,
            "instructions": instructions,
        }

    def _detect_artifact_type(self, message_lower: str) -> ArtifactType:
        """Detect artifact type from message text"""
        for artifact_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return artifact_type

        # Default to summary if no specific type detected
        return ArtifactType.SUMMARY

    def _extract_category_identifier(self, message: str) -> Optional[str]:
        """
        Extract chapter/section identifier from message

        Examples:
        - "summarize chapter 3" → "3"
        - "notes for section 2.1" → "2.1"
        - "chapter 5 summary" → "5"
        """
        # Try category reference pattern first (more specific)
        match = self.CATEGORY_REF_PATTERN.search(message)
        if match:
            return match.group(1)

        # Try general chapter pattern
        match = self.CHAPTER_PATTERN.search(message)
        if match:
            return match.group(1)

        return None

    def _generate_title(
        self,
        message: str,
        artifact_type: ArtifactType,
        category_identifier: Optional[str]
    ) -> str:
        """Generate descriptive title for artifact"""
        # Clean message for title (remove command verbs)
        clean_message = message
        for verb in self.COMMAND_VERBS:
            clean_message = re.sub(
                rf'\b{verb}\b',
                '',
                clean_message,
                flags=re.IGNORECASE
            ).strip()

        # Build title with artifact type
        type_label = artifact_type.value.capitalize()

        if category_identifier:
            # Include chapter reference in title
            if '.' in category_identifier:
                return f"{type_label}: Section {category_identifier}"
            else:
                return f"{type_label}: Chapter {category_identifier}"
        else:
            # Use cleaned message or generic title
            if len(clean_message) > 5:
                # Capitalize first letter and limit length
                title_text = clean_message[:100].strip()
                title_text = title_text[0].upper() + title_text[1:] if title_text else ""
                return f"{type_label}: {title_text}"
            else:
                return f"{type_label}"

    def _generate_query(
        self,
        message: str,
        category_identifier: Optional[str]
    ) -> str:
        """
        Generate search query for content retrieval

        The query should match content in the target chapter/section
        """
        # If category identifier exists, use it prominently in query
        if category_identifier:
            if '.' in category_identifier:
                return f"section {category_identifier} content"
            else:
                return f"chapter {category_identifier} content"

        # Otherwise, use the full message (removing command verbs)
        clean_message = message
        for verb in self.COMMAND_VERBS:
            clean_message = re.sub(
                rf'\b{verb}\b',
                '',
                clean_message,
                flags=re.IGNORECASE
            ).strip()

        return clean_message or "content"

    def _extract_instructions(self, message: str) -> Optional[str]:
        """
        Extract custom instructions from command

        Looks for text after commas or "with" keyword
        Example: "summarize chapter 3, focus on key formulas" → "focus on key formulas"
        """
        # Look for comma-separated instructions
        if ',' in message:
            parts = message.split(',', 1)
            if len(parts) > 1:
                instructions = parts[1].strip()
                if len(instructions) > 5:
                    return instructions

        # Look for "with" keyword
        with_match = re.search(r'\bwith\s+(.+)$', message, re.IGNORECASE)
        if with_match:
            return with_match.group(1).strip()

        return None

    async def resolve_category_id(
        self,
        db: AsyncSession,
        project_id: int,
        category_identifier: Optional[str]
    ) -> Optional[int]:
        """
        Resolve category identifier to category ID

        Args:
            db: Database session
            project_id: Project ID
            category_identifier: Chapter/section number (e.g., "3", "2.1")

        Returns:
            Category ID if found, None otherwise
        """
        if not category_identifier:
            return None

        # Search for category with matching name/slug
        # Look for patterns: "Chapter 3", "3", "Section 2.1", "2.1"
        search_patterns = [
            f"chapter {category_identifier}",
            f"ch {category_identifier}",
            f"section {category_identifier}",
            category_identifier,
        ]

        for pattern in search_patterns:
            result = await db.execute(
                select(Category).where(
                    Category.project_id == project_id,
                    Category.name.ilike(f"%{pattern}%")
                ).limit(1)
            )
            category = result.scalar_one_or_none()

            if category:
                logger.info(
                    f"Resolved category '{category_identifier}' to "
                    f"ID {category.id} (name: {category.name})"
                )
                return category.id

        logger.warning(f"Could not resolve category identifier: {category_identifier}")
        return None


# Global instance
command_parser = CommandParser()

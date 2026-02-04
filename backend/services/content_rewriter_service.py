"""
Content Rewriter Service
AI-powered content transformations and quote extraction
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.category import Category
from models.content import ExtractedQuote
from core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ContentRewriterService:
    """
    Service for AI-powered content transformations.

    Provides text rewriting operations using OpenAI GPT-4o-mini:
    - Summarize: Create concise summaries
    - Expand: Add detail and context
    - Simplify: Make content more accessible
    - Rewrite Tone: Change writing style
    - Extract Quotes: Find key quotes with context

    All operations use streaming for real-time feedback.
    """

    def __init__(self):
        from openai import AsyncOpenAI
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Cost-effective model for text operations

    async def summarize(
        self,
        content: str,
        max_length: Optional[int] = None,
        focus: Optional[str] = None
    ) -> str:
        """
        Create concise summary of content.

        Args:
            content: Text to summarize
            max_length: Target summary length in words (optional)
            focus: Specific aspect to focus on (e.g., "technical details", "business impact")

        Returns:
            Summarized text
        """
        # Build prompt
        prompt = f"Create a concise, accurate summary of the following content.\n\n"

        if max_length:
            prompt += f"Target length: approximately {max_length} words.\n"

        if focus:
            prompt += f"Focus on: {focus}\n"

        prompt += f"\nContent:\n{content}\n\nSummary:"

        # Call OpenAI
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating clear, concise summaries that capture key points and essential information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for factual summaries
                max_tokens=1000
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Summarized content: {len(content)} → {len(summary)} chars")

            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise

    async def expand(
        self,
        content: str,
        target_length: Optional[int] = None,
        add_details: Optional[str] = None
    ) -> str:
        """
        Expand content with additional detail and context.

        Args:
            content: Text to expand
            target_length: Target expanded length in words (optional)
            add_details: Specific aspects to elaborate (e.g., "examples", "technical implementation")

        Returns:
            Expanded text
        """
        # Build prompt
        prompt = f"Expand the following content with more detail, context, and explanation.\n\n"

        if target_length:
            prompt += f"Target length: approximately {target_length} words.\n"

        if add_details:
            prompt += f"Add details about: {add_details}\n"

        prompt += f"\nOriginal content:\n{content}\n\nExpanded version:"

        # Call OpenAI
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at expanding content with relevant details, examples, and context while maintaining accuracy and coherence."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,  # Moderate creativity for expansion
                max_tokens=2000
            )

            expanded = response.choices[0].message.content.strip()
            logger.info(f"Expanded content: {len(content)} → {len(expanded)} chars")

            return expanded

        except Exception as e:
            logger.error(f"Expansion failed: {str(e)}")
            raise

    async def simplify(
        self,
        content: str,
        reading_level: str = "general"
    ) -> str:
        """
        Simplify content for better accessibility.

        Args:
            content: Text to simplify
            reading_level: Target reading level ('basic', 'general', 'advanced')

        Returns:
            Simplified text
        """
        # Reading level guidance
        level_guidance = {
            "basic": "Use simple words and short sentences. Avoid jargon and technical terms. Explain concepts clearly for beginners.",
            "general": "Use clear, straightforward language. Explain technical terms when necessary. Suitable for general audience.",
            "advanced": "Maintain technical accuracy but improve clarity. Simplify complex sentences while preserving nuance."
        }

        guidance = level_guidance.get(reading_level, level_guidance["general"])

        # Build prompt
        prompt = f"Simplify the following content while maintaining accuracy.\n\n"
        prompt += f"Guidelines: {guidance}\n\n"
        prompt += f"Original content:\n{content}\n\nSimplified version:"

        # Call OpenAI
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at making complex content accessible without losing important information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1500
            )

            simplified = response.choices[0].message.content.strip()
            logger.info(f"Simplified content for {reading_level} level")

            return simplified

        except Exception as e:
            logger.error(f"Simplification failed: {str(e)}")
            raise

    async def rewrite_tone(
        self,
        content: str,
        tone: str,
        preserve_facts: bool = True
    ) -> str:
        """
        Rewrite content in a different tone or style.

        Args:
            content: Text to rewrite
            tone: Target tone ('professional', 'casual', 'technical', 'friendly', 'formal', 'conversational')
            preserve_facts: Keep factual information unchanged (default: True)

        Returns:
            Rewritten text
        """
        # Tone descriptions
        tone_descriptions = {
            "professional": "Business-professional tone. Clear, respectful, and authoritative.",
            "casual": "Casual, conversational tone. Friendly and approachable.",
            "technical": "Technical, precise tone. Focus on accuracy and detail.",
            "friendly": "Warm, friendly tone. Engaging and personable.",
            "formal": "Formal, academic tone. Objective and scholarly.",
            "conversational": "Natural, conversational tone. Like talking to a colleague."
        }

        tone_desc = tone_descriptions.get(tone, tone)

        # Build prompt
        prompt = f"Rewrite the following content in a {tone_desc}\n\n"

        if preserve_facts:
            prompt += "IMPORTANT: Preserve all factual information, numbers, and key points. Only change the writing style and tone.\n\n"

        prompt += f"Original content:\n{content}\n\nRewritten version:"

        # Call OpenAI
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at adapting writing style while maintaining content accuracy and message integrity."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,  # Higher creativity for style changes
                max_tokens=1500
            )

            rewritten = response.choices[0].message.content.strip()
            logger.info(f"Rewrote content in {tone} tone")

            return rewritten

        except Exception as e:
            logger.error(f"Tone rewriting failed: {str(e)}")
            raise

    async def extract_quotes(
        self,
        db: AsyncSession,
        category_id: int,
        content: str,
        max_quotes: int = 10,
        quote_types: Optional[List[str]] = None
    ) -> List[ExtractedQuote]:
        """
        Extract key quotes from content using AI.

        Identifies important quotes (facts, statistics, definitions, opinions)
        with surrounding context. Saves quotes to database.

        Args:
            db: Database session
            category_id: Category ID to associate quotes with
            content: Text to extract quotes from
            max_quotes: Maximum number of quotes to extract (default: 10)
            quote_types: Filter by types (e.g., ['fact', 'statistic', 'definition'])

        Returns:
            List of created ExtractedQuote instances
        """
        # Verify category exists
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        # Build prompt
        types_str = ", ".join(quote_types) if quote_types else "fact, opinion, statistic, definition"

        prompt = f"""Extract up to {max_quotes} key quotes from the following content.

For each quote, provide:
1. The exact quote text
2. Brief context before the quote (1-2 sentences)
3. Brief context after the quote (1-2 sentences)
4. Quote type: {types_str}

Format each quote as JSON:
{{
  "quote_text": "exact quote here",
  "context_before": "context before",
  "context_after": "context after",
  "quote_type": "fact|opinion|statistic|definition"
}}

Content:
{content}

Extracted quotes (JSON array):"""

        # Call OpenAI
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying and extracting key quotes from text. Focus on impactful, meaningful quotes that support understanding."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for accurate extraction
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            # Parse response
            import json
            result_text = response.choices[0].message.content.strip()
            quotes_data = json.loads(result_text)

            # Handle both array and object with "quotes" key
            if isinstance(quotes_data, dict) and "quotes" in quotes_data:
                quotes_list = quotes_data["quotes"]
            elif isinstance(quotes_data, list):
                quotes_list = quotes_data
            else:
                quotes_list = [quotes_data]

            # Create ExtractedQuote instances
            extracted_quotes = []

            for quote_data in quotes_list[:max_quotes]:
                quote = ExtractedQuote(
                    category_id=category_id,
                    quote_text=quote_data.get("quote_text", ""),
                    context_before=quote_data.get("context_before"),
                    context_after=quote_data.get("context_after"),
                    quote_type=quote_data.get("quote_type", "fact")
                )
                db.add(quote)
                extracted_quotes.append(quote)

            await db.commit()

            logger.info(f"Extracted {len(extracted_quotes)} quotes for category {category_id}")

            return extracted_quotes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quotes JSON: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Quote extraction failed: {str(e)}")
            raise

    async def generate_outline(
        self,
        topic: str,
        depth: int = 2,
        style: str = "article"
    ) -> str:
        """
        Generate content outline for a topic.

        Useful for planning content structure before writing.

        Args:
            topic: Topic to create outline for
            depth: Outline depth (1-3 levels)
            style: Content style ('article', 'tutorial', 'how-to', 'faq', 'reference')

        Returns:
            Markdown-formatted outline
        """
        style_guidance = {
            "article": "Create a journalistic article outline with introduction, main points, and conclusion.",
            "tutorial": "Create a step-by-step tutorial outline with prerequisites, steps, and troubleshooting.",
            "how-to": "Create a practical how-to guide outline with clear steps and tips.",
            "faq": "Create an FAQ outline with common questions and concise answers.",
            "reference": "Create a reference documentation outline with comprehensive coverage."
        }

        guidance = style_guidance.get(style, style_guidance["article"])

        prompt = f"""Create a {depth}-level outline for content about: {topic}

Style: {guidance}

Provide a well-structured markdown outline with clear headings and subheadings.

Outline:"""

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating well-structured content outlines that provide clear organization and logical flow."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )

            outline = response.choices[0].message.content.strip()
            logger.info(f"Generated outline for: {topic}")

            return outline

        except Exception as e:
            logger.error(f"Outline generation failed: {str(e)}")
            raise

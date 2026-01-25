"""
KnowledgeTree Backend - YouTube Transcriber Service
Extract transcript from YouTube videos and generate knowledge tree
"""

import logging
import re
import asyncio
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import timedelta

import httpx
from anthropic import Anthropic

from models.category import Category
from models.document import Document, DocumentType, ProcessingStatus
from core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Metadata extracted from YouTube video"""
    video_id: str
    title: str
    description: str
    channel: str
    duration: int  # in seconds
    publish_date: str
    thumbnail_url: str
    url: str


@dataclass
class TranscriptSegment:
    """Single segment of transcript with timing"""
    text: str
    start: float  # seconds
    duration: float  # seconds


@dataclass
class TranscriptResult:
    """Complete transcript with metadata"""
    video_id: str
    metadata: VideoMetadata
    segments: List[TranscriptSegment]
    full_text: str
    language: str


class YouTubeTranscriber:
    """
    Service for extracting and processing YouTube video transcripts

    Features:
    - Extract video ID from various URL formats
    - Fetch video metadata (title, description, channel, etc.)
    - Download transcript with timestamps
    - Generate hierarchical category tree from content
    - Extract key insights using Claude API
    - Create searchable chunks with embeddings
    """

    # YouTube URL patterns
    URL_PATTERNS = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\?\/]+)',
        r'^([a-zA-Z0-9_-]{11})$',  # Direct video ID
    ]

    # YouTube API endpoints (no API key required for basic info)
    INFO_URL = "https://www.youtube.com/youtubei/v1/player"
    TRANSCRIPT_URL = "https://www.youtube.com/api/timedtext"

    def __init__(self, anthropic_api_key: str):
        """
        Initialize YouTube transcriber

        Args:
            anthropic_api_key: Claude API key for content analysis
        """
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats

        Args:
            url: YouTube URL or video ID

        Returns:
            Video ID (11 characters) or None

        Examples:
            >>> transcriber.extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")
            'dQw4w9WgXcQ'
            >>> transcriber.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
            'dQw4w9WgXcQ'
            >>> transcriber.extract_video_id("dQw4w9WgXcQ")
            'dQw4w9WgXcQ'
        """
        url = url.strip()

        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                # Validate video ID format
                if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                    return video_id

        return None

    async def fetch_video_metadata(self, video_id: str) -> VideoMetadata:
        """
        Fetch video metadata from YouTube

        Args:
            video_id: 11-character YouTube video ID

        Returns:
            VideoMetadata object

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If video not found
        """
        # Try to fetch from noembed (simpler, no API key needed)
        try:
            url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                raise ValueError(f"Video not found: {video_id}")

            return VideoMetadata(
                video_id=video_id,
                title=data.get("title", "Unknown Title"),
                description=data.get("author_name", ""),  # noembed doesn't provide description
                channel=data.get("author_name", "Unknown Channel"),
                duration=0,  # noembed doesn't provide duration
                publish_date="",
                thumbnail_url=data.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"),
                url=data.get("url", f"https://www.youtube.com/watch?v={video_id}")
            )
        except Exception as e:
            logger.error(f"Failed to fetch video metadata: {e}")
            # Return minimal metadata
            return VideoMetadata(
                video_id=video_id,
                title=f"YouTube Video {video_id}",
                description="",
                channel="Unknown",
                duration=0,
                publish_date="",
                thumbnail_url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                url=f"https://www.youtube.com/watch?v={video_id}"
            )

    async def fetch_transcript(self, video_id: str, language: str = "pl") -> TranscriptResult:
        """
        Fetch transcript from YouTube video

        Args:
            video_id: 11-character YouTube video ID
            language: Preferred language code (default: "pl")

        Returns:
            TranscriptResult with segments and metadata

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If transcript not available
        """
        # First fetch metadata
        metadata = await self.fetch_video_metadata(video_id)

        # Try to fetch transcript
        transcript_params = {
            "v": video_id,
            "lang": language,
            "fmt": "json3",  # JSON format with metadata
        }

        try:
            response = await self.http_client.get(self.TRANSCRIPT_URL, params=transcript_params)

            # If Polish not available, try English
            if response.status_code == 404 and language == "pl":
                transcript_params["lang"] = "en"
                response = await self.http_client.get(self.TRANSCRIPT_URL, params=transcript_params)

            response.raise_for_status()
            transcript_data = response.json()

            # Parse transcript segments
            segments = []
            full_text_parts = []

            for event in transcript_data.get("events", []):
                if "segs" in event:
                    segment_text = "".join([seg.get("utf8", "") for seg in event["segs"]]).strip()

                    if segment_text:
                        segments.append(TranscriptSegment(
                            text=segment_text,
                            start=event.get("tStartMs", 0) / 1000.0,  # Convert ms to seconds
                            duration=event.get("dDurationMs", 0) / 1000.0
                        ))
                        full_text_parts.append(segment_text)

            full_text = " ".join(full_text_parts)

            logger.info(f"Extracted {len(segments)} transcript segments from video {video_id}")

            return TranscriptResult(
                video_id=video_id,
                metadata=metadata,
                segments=segments,
                full_text=full_text,
                language=language
            )

        except Exception as e:
            logger.error(f"Failed to fetch transcript for {video_id}: {e}")
            raise ValueError(f"Transcript not available for video {video_id}: {e}")

    async def analyze_with_claude(
        self,
        transcript: TranscriptResult,
        project_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze transcript with Claude to extract structured knowledge

        Args:
            transcript: Transcript result from fetch_transcript
            project_context: Optional context about the project

        Returns:
            Dictionary with structured analysis:
            - topics: List of main topics
            - summary: Overall summary
            - key_points: Key insights (with timestamps)
            - categories: Hierarchical category tree
            - questions: Discussion questions
            - resources: Related resources mentioned
        """
        # Prepare prompt for Claude
        prompt = self._build_analysis_prompt(transcript, project_context)

        try:
            message = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            response_text = message.content[0].text
            analysis = self._parse_claude_response(response_text, transcript)

            logger.info(f"Claude analysis completed for video {transcript.video_id}")
            return analysis

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            # Return basic analysis
            return {
                "topics": ["General"],
                "summary": transcript.full_text[:500] + "...",
                "key_points": [],
                "categories": [],
                "questions": [],
                "resources": []
            }

    def _build_analysis_prompt(self, transcript: TranscriptResult, project_context: Optional[str]) -> str:
        """Build prompt for Claude analysis"""
        prompt = f"""You are a knowledge extraction expert. Analyze this YouTube video transcript and create a structured knowledge base.

**Video Information:**
- Title: {transcript.metadata.title}
- Channel: {transcript.metadata.channel}
- URL: {transcript.metadata.url}

**Description:**
{transcript.metadata.description[:1000] if transcript.metadata.description else "No description available"}

**Transcript:**
{transcript.full_text[:15000]}  # Limit to avoid token limits

**Instructions:**
1. Extract 5-10 main topics covered
2. Create a concise summary (2-3 sentences)
3. Identify 5-10 key insights with approximate timestamps (if available from segment timing)
4. Design a hierarchical category tree (3-5 levels deep) to organize the content
5. Suggest 3-5 discussion questions
6. List any resources, books, or links mentioned

**Output Format (JSON):**
```json
{{
  "topics": ["topic1", "topic2", ...],
  "summary": "Concise summary...",
  "key_points": [
    {{"insight": "Key point...", "timestamp": "MM:SS", "category": "topic"}}
  ],
  "category_tree": [
    {{
      "name": "Main Category",
      "description": "Description",
      "children": [
        {{
          "name": "Subcategory",
          "description": "Description",
          "children": []
        }}
      ]
    }}
  ],
  "questions": ["question1", ...],
  "resources": ["resource1", ...]
}}
```
"""
        if project_context:
            prompt = f"**Project Context:** {project_context}\n\n" + prompt

        return prompt

    def _parse_claude_response(self, response_text: str, transcript: TranscriptResult) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        import json

        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Return fallback structure
            return {
                "topics": ["General"],
                "summary": transcript.metadata.title,
                "key_points": [],
                "category_tree": [
                    {
                        "name": transcript.metadata.title,
                        "description": "Main topic",
                        "children": []
                    }
                ],
                "questions": [],
                "resources": []
            }

    async def process_video(
        self,
        url: str,
        project_id: int,
        db,
        language: str = "pl",
        project_context: Optional[str] = None
    ) -> Tuple[Document, List[Category], Dict[str, Any]]:
        """
        Complete processing pipeline for YouTube video

        Args:
            url: YouTube video URL
            project_id: Project ID
            db: Database session
            language: Transcript language preference
            project_context: Optional project context

        Returns:
            Tuple of (Document, Categories list, Analysis metadata)

        Raises:
            ValueError: If video ID extraction or processing fails
        """
        # Extract video ID
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        logger.info(f"Processing YouTube video: {video_id}")

        # Fetch transcript
        transcript = await self.fetch_transcript(video_id, language)

        # Analyze with Claude
        analysis = await self.analyze_with_claude(transcript, project_context)

        # Create document record
        document = Document(
            filename=f"{transcript.metadata.title} ({video_id}).txt",
            title=transcript.metadata.title,
            source_type=DocumentType.YOUTUBE,
            source_url=url,
            file_path=None,  # No file stored for YouTube
            file_size=len(transcript.full_text.encode('utf-8')),
            processing_status=ProcessingStatus.COMPLETED,
            category_id=None,  # Will be set after category creation
            project_id=project_id,
            processed_at=transcript.metadata.publish_date or None
        )

        db.add(document)
        db.flush()  # Get document ID

        # Store transcript metadata in document (using error_message for now, can add JSONB column later)
        transcript_metadata = {
            "video_id": video_id,
            "duration": transcript.metadata.duration,
            "channel": transcript.metadata.channel,
            "segment_count": len(transcript.segments),
            "language": language
        }
        document.error_message = str(transcript_metadata)  # Temporary storage

        logger.info(f"Created document {document.id} for YouTube video {video_id}")

        # Generate categories from analysis
        categories = []
        category_map = {}  # Track parent-child relationships

        for category_data in analysis.get("category_tree", []):
            category = await self._create_category_from_data(
                category_data,
                project_id,
                None,
                db,
                0,
                document.id
            )
            if category:
                categories.append(category)
                category_map[category_data["name"]] = category

        # Link document to first category if available
        if categories:
            document.category_id = categories[0].id

        db.commit()

        logger.info(f"Created {len(categories)} categories for YouTube video {video_id}")

        # Return processing metadata
        metadata = {
            "video_id": video_id,
            "title": transcript.metadata.title,
            "channel": transcript.metadata.channel,
            "duration": transcript.metadata.duration,
            "topics": analysis.get("topics", []),
            "summary": analysis.get("summary", ""),
            "key_points": analysis.get("key_points", []),
            "questions": analysis.get("questions", []),
            "resources": analysis.get("resources", []),
            "category_count": len(categories)
        }

        return document, categories, metadata

    async def _create_category_from_data(
        self,
        data: Dict,
        project_id: int,
        parent_id: Optional[int],
        db,
        depth: int,
        document_id: int
    ) -> Optional[Category]:
        """Recursively create category from analysis data"""
        try:
            category = Category(
                name=data.get("name", "Untitled")[:200],
                description=data.get("description", "")[:1000],
                color=self._get_color_for_depth(depth),
                icon=self._get_icon_for_depth(depth),
                depth=depth,
                order=0,
                parent_id=parent_id,
                project_id=project_id
            )

            db.add(category)
            db.flush()

            # Process children
            children = data.get("children", [])
            for child_data in children:
                await self._create_category_from_data(
                    child_data,
                    project_id,
                    category.id,
                    db,
                    depth + 1,
                    document_id
                )

            return category

        except Exception as e:
            logger.error(f"Failed to create category: {e}")
            return None

    def _get_color_for_depth(self, depth: int) -> str:
        """Get pastel color for depth level"""
        colors = [
            "#E6E6FA",  # Lavender
            "#FFE4E1",  # Misty Rose
            "#E0FFE0",  # Light Green
            "#FFE4B5",  # Moccasin
            "#E0F4FF",  # Light Blue
            "#FFE4FF",  # Light Pink
            "#FFEAA7",  # Light Yellow
            "#DCD0FF",  # Light Purple
        ]
        return colors[depth % len(colors)]

    def _get_icon_for_depth(self, depth: int) -> str:
        """Get icon for depth level"""
        icons = {
            0: "PlayCircle",
            1: "Video",
            2: "FileVideo",
            3: "Film",
            4: "Radio",
        }
        return icons.get(depth, "File")


# Convenience function
async def process_youtube_video(
    url: str,
    project_id: int,
    db,
    anthropic_api_key: str,
    language: str = "pl",
    project_context: Optional[str] = None
) -> Tuple[Document, List[Category], Dict[str, Any]]:
    """
    Convenience function to process YouTube video

    Args:
        url: YouTube video URL
        project_id: Project ID
        db: Database session
        anthropic_api_key: Claude API key
        language: Transcript language
        project_context: Optional project context

    Returns:
        Tuple of (Document, Categories, Metadata)
    """
    transcriber = YouTubeTranscriber(anthropic_api_key)
    try:
        return await transcriber.process_video(url, project_id, db, language, project_context)
    finally:
        await transcriber.close()

"""
KnowledgeTree - AI Insights Service

Generates AI-powered insights from documents and projects:
- Document summaries and key findings
- Project-level analysis
- Pattern identification
- Actionable recommendations
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic import Anthropic

from core.config import settings
from models.document import Document
from models.category import Category

logger = logging.getLogger(__name__)


@dataclass
class DocumentInsight:
    """Insights for a single document"""
    document_id: int
    title: str
    summary: str
    key_findings: List[str]
    topics: List[str]
    entities: List[str]
    sentiment: str  # positive, neutral, negative, mixed
    action_items: List[str]
    importance_score: float  # 0-1


@dataclass
class ProjectInsight:
    """Insights for an entire project"""
    project_id: int
    project_name: str
    executive_summary: str
    total_documents: int
    key_themes: List[str]
    top_categories: List[Dict[str, Any]]
    document_summaries: List[DocumentInsight]
    patterns: List[str]
    recommendations: List[str]
    generated_at: datetime


class InsightsService:
    """
    AI-powered insights generation service
    
    Uses Claude API to analyze documents and generate actionable insights.
    """
    
    def __init__(self):
        """Initialize insights service"""
        self.anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = settings.ANTHROPIC_MODEL
        
        if not self.anthropic:
            logger.warning("ANTHROPIC_API_KEY not set. AI Insights will be limited.")
    
    async def generate_document_insights(
        self,
        db: AsyncSession,
        document_id: int,
        project_id: int
    ) -> DocumentInsight:
        """
        Generate insights for a single document
        
        Args:
            db: Database session
            document_id: Document ID
            project_id: Project ID for authorization
            
        Returns:
            DocumentInsight with analysis
        """
        # Get document
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.project_id == project_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Prepare text for analysis
        text = document.processed_text or ""
        if not text:
            raise ValueError(f"Document {document_id} has no processed text")
        
        # Truncate if too long (Claude has 200K token limit, keep safe)
        max_chars = 50000
        text_to_analyze = text[:max_chars]
        
        # Generate insights using Claude
        prompt = f"""Analizuj poniższy dokument i wygeneruj strukturyzowane wnioski.

Tytuł dokumentu: {document.filename or "Bez tytułu"}

Tekst dokumentu:
{text_to_analyze}

Wygeneruj JSON z następującymi polami:
{{
    "summary": "krótkie podsumowanie dokumentu (2-3 zdania)",
    "key_findings": ["kluczowe odkrycia 1", "kluczowe odkrycie 2", ...],
    "topics": ["temat 1", "temat 2", ...],
    "entities": ["encja 1", "encja 2", ...],
    "sentiment": "positive|neutral|negative|mixed",
    "action_items": ["zalecana akcja 1", "zalecana akcja 2", ...],
    "importance_score": 0.8  // wartość od 0.0 do 1.0
}}

Zwróć tylko JSON bez dodatkowego tekstu."""
        
        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            import json
            content = response.content[0].text
            
            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            insights_data = json.loads(content)
            
            return DocumentInsight(
                document_id=document.id,
                title=document.filename or "Bez tytułu",
                summary=insights_data.get("summary", ""),
                key_findings=insights_data.get("key_findings", []),
                topics=insights_data.get("topics", []),
                entities=insights_data.get("entities", []),
                sentiment=insights_data.get("sentiment", "neutral"),
                action_items=insights_data.get("action_items", []),
                importance_score=insights_data.get("importance_score", 0.5)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate insights for document {document_id}: {e}")
            # Return basic insights
            return DocumentInsight(
                document_id=document.id,
                title=document.filename or "Bez tytułu",
                summary=f"Dokument zawierający {len(text)} znaków.",
                key_findings=[],
                topics=[],
                entities=[],
                sentiment="neutral",
                action_items=[],
                importance_score=0.5
            )
    
    async def generate_project_insights(
        self,
        db: AsyncSession,
        project_id: int,
        max_documents: int = 10,
        include_categories: bool = True
    ) -> ProjectInsight:
        """
        Generate insights for an entire project
        
        Args:
            db: Database session
            project_id: Project ID
            max_documents: Maximum number of documents to analyze
            include_categories: Whether to include category analysis
            
        Returns:
            ProjectInsight with comprehensive analysis
        """
        # Get documents
        result = await db.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .where(Document.status == "completed")
            .order_by(Document.created_at.desc())
            .limit(max_documents)
        )
        documents = result.scalars().all()
        
        if not documents:
            raise ValueError(f"No completed documents found for project {project_id}")
        
        # Generate insights for each document
        document_insights = []
        all_texts = []
        
        for doc in documents:
            try:
                insight = await self.generate_document_insights(db, doc.id, project_id)
                document_insights.append(insight)
                all_texts.append(doc.processed_text or "")
            except Exception as e:
                logger.warning(f"Failed to analyze document {doc.id}: {e}")
        
        # Prepare combined text for project-level analysis
        combined_text = "\n\n".join([f"Doc {i+1}: {t[:2000]}" for i, t in enumerate(all_texts)])
        
        # Get categories if requested
        category_info = []
        if include_categories:
            cat_result = await db.execute(
                select(Category)
                .where(Category.project_id == project_id)
                .order_by(Category.document_count.desc())
                .limit(5)
            )
            categories = cat_result.scalars().all()
            category_info = [
                {"name": c.name, "documents": c.document_count or 0}
                for c in categories
            ]
        
        # Generate project-level insights
        prompt = f"""Analizuj poniższy zbiór dokumentów z projektu i wygeneruj projektowe wnioski.

Liczba dokumentów: {len(documents)}
Teksty (fragmenty):
{combined_text[:30000]}

Wygeneruj JSON z następującymi polami:
{{
    "executive_summary": "podsumowanie executive (3-4 zdania)",
    "key_themes": ["główny temat 1", "główny temat 2", ...],
    "patterns": ["wykryta wzorzec 1", "wykryty wzorzec 2", ...],
    "recommendations": ["rekomendacja 1", "rekomendacja 2", ...]
}}

Zwróć tylko JSON bez dodatkowego tekstu."""
        
        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            import json
            content = response.content[0].text
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            project_data = json.loads(content)
            
        except Exception as e:
            logger.error(f"Failed to generate project insights: {e}")
            project_data = {
                "executive_summary": f"Projekt zawierający {len(documents)} dokumentów.",
                "key_themes": [],
                "patterns": [],
                "recommendations": []
            }
        
        return ProjectInsight(
            project_id=project_id,
            project_name=f"Project {project_id}",  # Could fetch from DB
            executive_summary=project_data.get("executive_summary", ""),
            total_documents=len(documents),
            key_themes=project_data.get("key_themes", []),
            top_categories=category_info,
            document_summaries=document_insights,
            patterns=project_data.get("patterns", []),
            recommendations=project_data.get("recommendations", []),
            generated_at=datetime.utcnow()
        )
    
    def check_availability(self) -> Dict[str, Any]:
        """Check if AI Insights service is available"""
        return {
            "available": self.anthropic is not None,
            "model": self.model if self.anthropic else None,
            "message": (
                "AI Insights is ready" if self.anthropic
                else "ANTHROPIC_API_KEY not configured. AI Insights will be limited."
            )
        }


# Global singleton instance
insights_service = InsightsService()

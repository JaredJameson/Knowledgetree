# TIER 2 Phase 5: Gap Analysis & Sprint Plan Updates

**Date**: 2026-01-20
**Context**: Advanced PDF Processing Requirements

## Executive Summary

### Current State
✅ **Completed**:
- Sprint 0: Foundation (Database, Auth, Design System, i18n)
- TIER 1 Advanced RAG: Hybrid Search, Cross-Encoder Reranking, Contextual Embeddings
- TIER 2 Enhanced RAG (Phases 1-4): Conditional Reranking, Explainability, Query Expansion, CRAG

⚠️ **Gap Identified**: Current roadmap focuses on basic PDF processing but lacks advanced document structure preservation and intelligent interaction features.

### User Requirements (New/Enhanced)

**Core Use Case**: Transform large PDF documents (entire books) into structured, interactive knowledge trees

**Key Requirements**:
1. 📚 **Intelligent PDF Structure Extraction**
   - Preserve document hierarchy (books → chapters → sections → paragraphs)
   - Extract and map table of contents (ToC) to category tree
   - Handle very large PDFs (100+ pages, entire books)

2. 📊 **Advanced Content Extraction**
   - Extract tables with structure preservation
   - Extract formulas (LaTeX/MathML conversion)
   - Extract charts and diagrams (OCR, image analysis)
   - Extract metadata (authors, dates, references)

3. 🌳 **Knowledge Tree Structuring**
   - Automatic PDF → Tree mapping based on ToC
   - Hierarchical organization matching document structure
   - Visual tree representation in UI
   - Categorized content organization

4. 💬 **Interactive Artifact System**
   - Chat-based interaction with specific chapters/sections
   - Agent-generated artifacts (summaries, articles, extracts)
   - Right-side artifact panel with slide-out animation
   - Chapter-level commands (e.g., "summarize chapter 3")

5. 🎨 **Intuitive UX/UI**
   - Clean, professional interface
   - Visual PDF structure representation
   - Easy navigation through document hierarchy
   - Responsive design for large documents

---

## Gap Analysis: Current vs Required

### 1. PDF Processing

| Feature | Current (PRD/ROADMAP) | Required | Gap |
|---------|----------------------|----------|-----|
| **Extraction Engine** | Docling + PyMuPDF fallback | ✅ Same | None |
| **Chunking Strategy** | Fixed size (1000/200) | Intelligent (structure-based) | **HIGH** |
| **Structure Detection** | Not specified | ToC extraction, hierarchy detection | **HIGH** |
| **Table Extraction** | Basic (via Docling) | Structure-preserving extraction | **MEDIUM** |
| **Formula Extraction** | Not mentioned | LaTeX/MathML conversion | **HIGH** |
| **Chart Extraction** | Not mentioned | OCR + image analysis | **HIGH** |
| **Metadata Extraction** | Basic (filename, size) | Authors, dates, citations | **MEDIUM** |
| **Large File Handling** | Not specified | Streaming, progressive processing | **MEDIUM** |

### 2. Knowledge Tree Integration

| Feature | Current (PRD/ROADMAP) | Required | Gap |
|---------|----------------------|----------|-----|
| **Category Tree Editor** | Manual editing (from Genetico) | ✅ Available | None |
| **Automatic ToC Mapping** | Not mentioned | PDF ToC → Category Tree | **HIGH** |
| **Hierarchical Import** | Not mentioned | Structure-preserving import | **HIGH** |
| **Visual Tree Representation** | Basic tree view | Enhanced with PDF structure | **MEDIUM** |
| **Bulk Operations** | Basic CRUD | Batch import, reorganization | **LOW** |

### 3. Interactive Features

| Feature | Current (PRD/ROADMAP) | Required | Gap |
|---------|----------------------|----------|-----|
| **RAG Chat Interface** | Basic chat (Sprint 4) | ✅ Available | None |
| **Artifact Generation** | Not mentioned | Agent-generated content | **HIGH** |
| **Artifact Panel** | Not mentioned | Right-side slide-out panel | **HIGH** |
| **Chapter-Level Queries** | Not mentioned | "Summarize chapter X" commands | **HIGH** |
| **Context-Aware Chat** | Citations only | Chapter/section awareness | **MEDIUM** |
| **Streaming Responses** | ✅ Planned (Sprint 4) | ✅ Available | None |

### 4. UX/UI Design

| Feature | Current (PRD/ROADMAP) | Required | Gap |
|---------|----------------------|----------|-----|
| **Design System** | ✅ TailwindCSS + shadcn/ui | ✅ Available | None |
| **PDF Structure View** | Not mentioned | Visual hierarchy display | **HIGH** |
| **Split-Panel Layout** | Not mentioned | Tree + Chat + Artifacts | **MEDIUM** |
| **Responsive Design** | ✅ Planned | ✅ Available | None |
| **Dark Mode** | ✅ Implemented | ✅ Available | None |

---

## Priority Matrix

### P0 - Critical (MVP Blockers)
1. **Intelligent PDF Structure Extraction** - Core use case enabler
2. **ToC → Category Tree Mapping** - Automatic structuring requirement
3. **Artifact Panel UI** - Key differentiator for interaction

### P1 - High Priority (Enhanced MVP)
4. **Table Extraction** - Common in technical/academic documents
5. **Formula Extraction** - Essential for scientific content
6. **Chapter-Level Chat Commands** - Core interaction pattern
7. **PDF Structure Visualization** - UX requirement

### P2 - Medium Priority (Post-MVP)
8. **Chart/Diagram Extraction** - Nice-to-have enhancement
9. **Advanced Metadata Extraction** - Search/organization improvement
10. **Large File Streaming** - Performance optimization

### P3 - Low Priority (Future Enhancements)
11. **Batch Import Operations** - Efficiency improvement
12. **Custom Chunking Strategies** - Advanced configuration

---

## Technology Assessment

### Docling Capabilities (Verified)

**Current Usage**: Basic text extraction with markdown export

**Advanced Features Available**:
1. ✅ **Structure Detection**: `DocumentConverter` with layout analysis
2. ✅ **Table Extraction**: `TableFormer` model for table detection
3. ✅ **Formula Detection**: LaTeX conversion support
4. ⚠️ **ToC Extraction**: Requires custom parsing of document structure
5. ⚠️ **Chart Extraction**: Limited - may need supplementary tools

**Enhancement Path**:
```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

# Enhanced Docling configuration
pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True  # Enable table extraction
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

### Supplementary Tools Needed

1. **PyPDF2/pypdf** - PDF structure analysis, ToC extraction
2. **pdfplumber** - Enhanced table extraction (backup for Docling)
3. **SymPy/latex2mathml** - Formula conversion
4. **pytesseract** - OCR for charts/diagrams (if needed)
5. **Pillow** - Image processing for extracted charts

---

## Updated Sprint Plans

### Sprint 2: PDF Upload & Advanced Processing (Week 5-6) 🔄 UPDATED

**Original Scope**:
- Basic PDF upload
- Text extraction (Docling/PyMuPDF)
- Simple chunking (1000/200)

**Enhanced Scope**:
1. **Advanced PDF Extraction** (3 days)
   - Configure Docling with table/formula extraction
   - Implement PyPDF2 ToC extraction
   - Add structure detection pipeline
   - Extract metadata (authors, dates, sections)

2. **Intelligent Chunking** (2 days)
   - Structure-aware chunking (by chapters/sections)
   - Preserve document hierarchy in chunks
   - Add ToC-based chunk metadata
   - Implement adaptive chunk sizing

3. **ToC → Category Tree Mapping** (3 days)
   - Parse PDF ToC structure
   - Automatic category tree generation
   - Hierarchical import with validation
   - UI for reviewing/editing imported structure

4. **Enhanced Content Extraction** (2 days)
   - Table extraction with structure preservation
   - Formula extraction (LaTeX conversion)
   - Image/chart extraction (basic)
   - Store extracted elements with references

**Deliverables**:
- ✅ Advanced PDF processing pipeline
- ✅ Automatic ToC-based structuring
- ✅ Enhanced content extraction (tables, formulas)
- ✅ Intelligent chunking system

**Estimated Duration**: 10 days (was 5 days) → Week 5-7

---

### Sprint 3: PDF Structure Visualization + Basic Search (Week 8-9) 🔄 UPDATED

**Original Scope**:
- Semantic search (basic)
- Export functionality

**Enhanced Scope**:
1. **PDF Structure Visualization** (3 days)
   - Visual tree representation of PDF hierarchy
   - Chapter/section navigation
   - Collapsible tree with icons
   - Document structure overview panel

2. **Enhanced Category Tree UI** (2 days)
   - Adapt Genetico tree editor
   - Add PDF-specific metadata display
   - Show chunk count per section
   - Visual indicators for processed content

3. **Semantic Search (Basic)** (3 days)
   - Dense search with BGE-M3
   - Basic filters (project, category)
   - Result highlighting
   - Citation links to source chunks

4. **Export Functionality** (2 days)
   - Export processed documents (JSON, Markdown)
   - Export category trees
   - Export search results

**Deliverables**:
- ✅ Visual PDF structure representation
- ✅ Enhanced category tree UI
- ✅ Basic semantic search
- ✅ Export functionality

**Estimated Duration**: 10 days → Week 8-10

---

### Sprint 4: Interactive Artifacts + Advanced RAG Chat (Week 11-13) 🆕 NEW SPRINT

**Enhanced Scope**:
1. **Artifact System** (4 days)
   - Artifact data model (type, content, metadata)
   - Artifact generation service (summaries, articles, extracts)
   - Artifact storage and versioning
   - API endpoints for artifact CRUD

2. **Artifact Panel UI** (3 days)
   - Right-side slide-out panel component
   - Artifact viewer (Markdown, rich text)
   - Artifact history/versions
   - Download/export artifacts

3. **Chapter-Level Chat Commands** (3 days)
   - Parse chapter/section references in queries
   - Context retrieval by chapter
   - Special commands ("summarize chapter X")
   - Multi-chapter operations

4. **Enhanced RAG Chat** (3 days)
   - Integrate TIER 1+2 RAG pipeline
   - Streaming responses with citations
   - Chapter-aware context retrieval
   - Artifact generation triggers

**Deliverables**:
- ✅ Artifact system (backend + UI)
- ✅ Interactive artifact panel
- ✅ Chapter-level chat commands
- ✅ Production-ready RAG chat

**Estimated Duration**: 13 days → Week 11-13

---

### Sprint 5: Hybrid Search + Advanced Filters (Week 14-15) 🔄 UPDATED

**Original**: Sprint 3 content moved here

**Enhanced Scope**:
1. **Hybrid Search (TIER 1)** (3 days)
   - Dense + Sparse (BM25) retrieval
   - RRF fusion
   - Cross-encoder reranking

2. **TIER 2 Features** (2 days)
   - Conditional reranking (already implemented)
   - Query expansion (already implemented)
   - CRAG (already implemented)
   - Explainability (already implemented)

3. **Advanced Filters** (3 days)
   - Filter by category/chapter
   - Date range filters
   - Content type filters (text, tables, formulas)
   - Custom metadata filters

4. **Search Analytics** (2 days)
   - Search performance metrics
   - Result quality tracking
   - User feedback collection

**Deliverables**:
- ✅ Full TIER 1+2 RAG pipeline (already done)
- ✅ Advanced search filters
- ✅ Search analytics

**Estimated Duration**: 10 days → Week 14-16

---

## Timeline Adjustment Summary

| Sprint | Original Timeline | Updated Timeline | Duration Change |
|--------|------------------|------------------|-----------------|
| Sprint 0 | Week 1-2 | Week 1-2 | ✅ No change |
| Sprint 1 | Week 3-4 | Week 3-4 | ✅ No change |
| Sprint 2 | Week 5-6 | Week 5-7 | +1 week |
| Sprint 3 | Week 7-8 | Week 8-10 | +1 week (reordered) |
| Sprint 4 | Week 9-10 | Week 11-13 | +2 weeks (major enhancement) |
| Sprint 5 | Week 11-12 | Week 14-16 | 0 (content shifted from Sprint 3) |

**Total Timeline Impact**: +4 weeks for advanced PDF features

**Original MVP**: Week 8 (Free Tier Beta)
**Updated MVP**: Week 13 (with advanced PDF features)

---

## Current Implementation Status

### ✅ Completed (Sprint 0 + TIER 1+2 RAG)

**Sprint 0 Foundation** (100%):
- PostgreSQL 16 + pgvector 0.8.0 database
- 9 database models with migrations
- JWT authentication system
- TailwindCSS + shadcn/ui design system
- i18n (Polish/English)
- Docker containerization

**TIER 1 Advanced RAG** (100%):
- BGE-M3 embeddings (1024 dims)
- BM25 sparse retrieval
- Hybrid search with RRF
- Cross-encoder reranking (mmarco-mMiniLMv2)
- Contextual embeddings

**TIER 2 Enhanced RAG** (100%):
- Phase 1: Conditional reranking optimizer (30-50% latency reduction)
- Phase 2: Explainability service (full transparency)
- Phase 3: Query expansion (90+ synonyms, +5-10% recall)
- Phase 4: CRAG service (self-reflection, +10-15% robustness)

**PDF Processing** (60%):
- Basic PDFProcessor with Docling integration
- PyMuPDF fallback
- TextChunker with overlap
- Page-aware chunking
- Contextual chunk information

### 🚧 In Progress (Sprint 1-2)

**Sprint 1** (Status Unknown):
- Project management UI
- Category tree editor (from Genetico)
- Document library

**Sprint 2** (Needs Enhancement):
- PDF upload endpoint (basic)
- Document processing pipeline (basic)
- Needs: Advanced extraction, ToC mapping, intelligent chunking

### ⏳ Not Started (Sprint 3-9)

**Sprint 3+**: All remaining features from original roadmap
**New Features**: Artifact system, chapter-level chat, PDF visualization

---

## What Needs Completion (Priority Order)

### Phase 1: Enhanced PDF Processing (P0 - Weeks 5-7)
1. **Advanced Docling Configuration**
   - Enable table structure extraction
   - Configure formula detection
   - Set up layout analysis

2. **ToC Extraction Pipeline**
   - Implement PyPDF2 ToC parser
   - Extract document outline/bookmarks
   - Build hierarchical structure representation

3. **Automatic Tree Generation**
   - Map ToC → Category Tree
   - Create categories from chapters/sections
   - Preserve hierarchy depth (max 10 levels)
   - Add validation and review UI

4. **Intelligent Chunking**
   - Replace fixed-size chunking with structure-aware
   - Chunk by sections/subsections
   - Add ToC metadata to chunks
   - Implement adaptive sizing based on content type

### Phase 2: Content Extraction Enhancement (P1 - Weeks 5-7)
5. **Table Extraction**
   - Configure Docling TableFormer
   - Implement pdfplumber backup
   - Store tables with structure (JSON)
   - Link tables to source chunks

6. **Formula Extraction**
   - Detect LaTeX formulas in Docling output
   - Convert to MathML for rendering
   - Store formulas with metadata
   - Link to source chunks

7. **Chart/Diagram Detection** (P2 - Post-MVP)
   - Extract images from PDFs
   - Basic image classification
   - OCR for chart text
   - Store as separate artifacts

### Phase 3: Visualization & UX (P0 - Weeks 8-10)
8. **PDF Structure Visualization**
   - Design tree component for PDF hierarchy
   - Show chapters, sections, subsections
   - Add icons for content types (text, table, formula, chart)
   - Implement navigation to specific sections

9. **Enhanced Category Tree**
   - Adapt Genetico tree editor
   - Add PDF metadata display
   - Show processing status
   - Add chunk count indicators

### Phase 4: Interactive Artifacts (P0 - Weeks 11-13)
10. **Artifact System Backend**
    - Design artifact data model
    - Create artifact generation service
    - Implement storage and versioning
    - Build API endpoints

11. **Artifact Panel UI**
    - Create right-side slide-out component
    - Build artifact viewer (Markdown/rich text)
    - Add history/versioning UI
    - Implement download/export

12. **Chapter-Level Chat**
    - Parse chapter references in queries
    - Implement context retrieval by chapter
    - Add special commands parser
    - Integrate with RAG pipeline

### Phase 5: Integration & Testing (Weeks 13-16)
13. **End-to-End Testing**
    - Test full PDF → Tree → Chat → Artifact workflow
    - Validate large file handling
    - Performance testing (100+ page PDFs)
    - UX testing and refinement

14. **Documentation & Polish**
    - Update user guides
    - Create demo videos
    - Polish UI/UX based on feedback
    - Prepare for beta release

---

## Risk Assessment

### High Risk
- **Docling Performance**: Large PDFs may have slow processing times
  - Mitigation: Implement background jobs, progress indicators
- **ToC Extraction Accuracy**: Not all PDFs have proper ToC structures
  - Mitigation: Fallback to heading detection, manual review UI

### Medium Risk
- **Formula Extraction Quality**: Complex formulas may not convert correctly
  - Mitigation: Store original LaTeX, implement manual correction UI
- **UI Complexity**: Three-panel layout may be challenging on mobile
  - Mitigation: Progressive enhancement, mobile-first design

### Low Risk
- **Table Structure Preservation**: Docling may miss complex tables
  - Mitigation: pdfplumber backup, validation UI

---

## Success Metrics

### Technical Metrics
- PDF processing success rate: >95%
- ToC extraction accuracy: >90%
- Table extraction accuracy: >85%
- Formula detection rate: >80%
- Processing time: <30s for 100-page PDF

### User Experience Metrics
- Time to import PDF book: <2 minutes
- Tree navigation efficiency: <3 clicks to any chapter
- Artifact generation time: <10s
- User satisfaction: >4.5/5

### Business Metrics
- MVP completion: Week 13 (vs. Week 8 original)
- Feature completeness: 100% of user requirements
- Technical debt: <10% of codebase

---

## Recommendations

### Immediate Actions (This Week)
1. ✅ Review and approve updated sprint plans
2. ✅ Prioritize P0 features for Sprint 2 enhancement
3. ✅ Begin Docling advanced configuration research
4. ✅ Design artifact system architecture
5. ✅ Create UI mockups for PDF structure visualization

### Short-Term (Next 2 Weeks)
6. Implement advanced PDF extraction pipeline
7. Build ToC → Category Tree mapping
8. Start artifact system backend
9. Design artifact panel UI component

### Long-Term (Next Month)
10. Complete interactive artifacts system
11. Finish PDF visualization UI
12. Conduct end-to-end testing
13. Prepare for beta release

---

## Conclusion

**Gap Analysis Summary**: Current roadmap covers basic PDF processing but lacks advanced features critical for the core use case (book-to-knowledge-tree transformation with interactive artifacts).

**Updated Plan**: 4 additional weeks added to incorporate advanced PDF structure extraction, intelligent chunking, ToC mapping, and interactive artifact system.

**Current Status**: Sprint 0 complete (100%), TIER 1+2 RAG complete (100%), Sprint 1-2 in progress (~40% estimated).

**Next Steps**: Enhance Sprint 2 with advanced PDF features, design artifact system, update Sprint 3-4 with visualization and interaction capabilities.

**Timeline Impact**: MVP moves from Week 8 → Week 13, but delivers significantly more sophisticated functionality aligned with user requirements.

**Technical Feasibility**: High - All required technologies (Docling, PyPDF2, pdfplumber) are mature and well-documented. Risks are manageable with proper mitigation strategies.

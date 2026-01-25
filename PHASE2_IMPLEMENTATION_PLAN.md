# Phase 2 Implementation Plan: Table & Formula Extraction
**Date**: January 21, 2026
**Phase**: Professional Tier - Advanced Content Extraction
**Duration**: 1-2 weeks
**Status**: 📋 Planning

---

## 📋 Executive Summary

Phase 2 builds on the successful Phase 1 (ToC Extraction) to add advanced content extraction capabilities:
- **Table Extraction**: Structure-preserving table extraction with Docling TableFormer
- **Formula Extraction**: LaTeX conversion and math symbol recognition
- **Intelligent Chunking**: Structure-aware text chunking using document hierarchy
- **Enhanced Metadata**: Preserve relationships between tables, formulas, and content

**Priority**: HIGH (P1) - Core value proposition for Professional Tier
**Dependencies**: Phase 1 (✅ Complete)

---

## 🎯 Phase 2 Goals

### Primary Objectives
1. ✅ Extract tables from PDFs with structure preservation
2. ✅ Extract mathematical formulas and convert to LaTeX
3. ✅ Implement structure-aware text chunking
4. ✅ Link extracted elements to document chunks
5. ✅ Store structured data in database
6. ✅ Integrate with existing RAG pipeline

### Success Criteria
- Extract tables from 90%+ of PDFs with tables
- Formula extraction accuracy >85%
- Chunks respect chapter/section boundaries
- Table/formula metadata preserved
- Performance: <5 minutes for 100-page PDF

---

## 🏗️ Architecture Overview

### Database Schema Changes

**New Tables**:
```sql
-- Extracted tables from documents
CREATE TABLE document_tables (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    table_index INTEGER NOT NULL,
    page_number INTEGER,
    chunk_id INTEGER REFERENCES chunks(id),

    -- Table structure (JSON)
    table_data JSONB NOT NULL,  -- {headers: [], rows: [[]], caption: ""}
    row_count INTEGER,
    col_count INTEGER,

    -- Extraction metadata
    extraction_method VARCHAR(50),  -- "docling", "pdfplumber"
    confidence_score FLOAT,

    -- Positioning
    bbox JSONB,  -- {x: float, y: float, width: float, height: float}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extracted formulas from documents
CREATE TABLE document_formulas (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    formula_index INTEGER NOT NULL,
    page_number INTEGER,
    chunk_id INTEGER REFERENCES chunks(id),

    -- Formula content
    latex_content TEXT NOT NULL,
    rendered_image_path VARCHAR(500),  -- Optional: rendered formula image

    -- Context
    context_before TEXT,  -- Text before formula
    context_after TEXT,   -- Text after formula

    -- Extraction metadata
    extraction_method VARCHAR(50),  -- "docling", "mathpix"
    confidence_score FLOAT,

    -- Positioning
    bbox JSONB,  -- {x: float, y: float, width: float, height: float}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update chunks table to reference tables/formulas
ALTER TABLE chunks ADD COLUMN has_tables BOOLEAN DEFAULT FALSE;
ALTER TABLE chunks ADD COLUMN has_formulas BOOLEAN DEFAULT FALSE;
ALTER TABLE chunks ADD COLUMN element_references JSONB;  -- {tables: [ids], formulas: [ids]}
```

### Service Architecture

```
PDF Document
    │
    ├─> PDFProcessor (enhanced)
    │   ├─> TocExtractor (Phase 1) ✅
    │   ├─> TableExtractor (NEW)
    │   │   ├─> Docling TableFormer (primary)
    │   │   └─> pdfplumber (fallback)
    │   ├─> FormulaExtractor (NEW)
    │   │   ├─> Docling formula detection
    │   │   └─> latex2mathml conversion
    │   └─> StructureAwareChunker (ENHANCED)
    │       ├─> Use ToC structure
    │       ├─> Respect boundaries
    │       └─> Link elements
    │
    └─> Database
        ├─> documents table
        ├─> categories table (from ToC)
        ├─> chunks table (enhanced)
        ├─> document_tables table (new)
        └─> document_formulas table (new)
```

---

## 📅 Implementation Timeline

### Week 1: Core Extraction Services

**Days 1-2: Table Extraction Service**
```python
# File: backend/services/table_extractor.py

class TableExtractionMethod(str, Enum):
    DOCLING = "docling"
    PDFPLUMBER = "pdfplumber"
    NONE = "none"

@dataclass
class ExtractedTable:
    table_index: int
    page_number: int
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str]
    bbox: Dict[str, float]
    confidence: float
    method: TableExtractionMethod

class TableExtractor:
    def __init__(self):
        self.docling_available = self._check_docling()
        self.pdfplumber_available = self._check_pdfplumber()

    async def extract_tables(
        self,
        pdf_path: str,
        max_tables: int = 100
    ) -> List[ExtractedTable]:
        """
        Extract tables from PDF using waterfall approach:
        1. Docling TableFormer (primary)
        2. pdfplumber (fallback)
        """
        # Implementation
        pass
```

**Tasks**:
- [ ] Create `table_extractor.py` service
- [ ] Configure Docling with TableFormer
- [ ] Implement pdfplumber fallback
- [ ] Add table structure validation
- [ ] Test with sample PDFs

**Days 3-4: Formula Extraction Service**
```python
# File: backend/services/formula_extractor.py

class FormulaExtractionMethod(str, Enum):
    DOCLING = "docling"
    REGEX = "regex"
    NONE = "none"

@dataclass
class ExtractedFormula:
    formula_index: int
    page_number: int
    latex_content: str
    context_before: str
    context_after: str
    bbox: Dict[str, float]
    confidence: float
    method: FormulaExtractionMethod

class FormulaExtractor:
    def __init__(self):
        self.docling_available = self._check_docling()
        self.latex2mathml_available = self._check_latex2mathml()

    async def extract_formulas(
        self,
        pdf_path: str,
        max_formulas: int = 200
    ) -> List[ExtractedFormula]:
        """
        Extract mathematical formulas from PDF:
        1. Detect formula regions with Docling
        2. Extract LaTeX representation
        3. Validate and convert
        """
        # Implementation
        pass
```

**Tasks**:
- [ ] Create `formula_extractor.py` service
- [ ] Configure Docling formula detection
- [ ] Implement LaTeX extraction
- [ ] Add latex2mathml conversion
- [ ] Test with scientific PDFs

**Days 5-6: Enhanced PDF Processor Integration**
```python
# File: backend/services/pdf_processor.py (ENHANCED)

class PDFProcessor:
    def __init__(self):
        self.toc_extractor = TocExtractor()
        self.table_extractor = TableExtractor()  # NEW
        self.formula_extractor = FormulaExtractor()  # NEW
        self.text_chunker = TextChunker()

    async def process_document(
        self,
        pdf_path: str,
        extract_tables: bool = True,
        extract_formulas: bool = True
    ) -> ProcessingResult:
        """
        Enhanced PDF processing with table/formula extraction
        """
        # 1. Extract ToC (Phase 1)
        toc_result = await self.toc_extractor.extract_toc(pdf_path)

        # 2. Extract tables (Phase 2)
        tables = []
        if extract_tables:
            tables = await self.table_extractor.extract_tables(pdf_path)

        # 3. Extract formulas (Phase 2)
        formulas = []
        if extract_formulas:
            formulas = await self.formula_extractor.extract_formulas(pdf_path)

        # 4. Structure-aware chunking
        chunks = await self.text_chunker.chunk_with_structure(
            pdf_path,
            toc_structure=toc_result,
            tables=tables,
            formulas=formulas
        )

        return ProcessingResult(
            toc=toc_result,
            tables=tables,
            formulas=formulas,
            chunks=chunks
        )
```

**Tasks**:
- [ ] Enhance `PDFProcessor` with table/formula extraction
- [ ] Coordinate extraction methods
- [ ] Handle extraction failures gracefully
- [ ] Add progress tracking

**Day 7: Database Migrations & Models**
```python
# File: backend/alembic/versions/xxx_add_tables_formulas.py

def upgrade():
    # Create document_tables table
    op.create_table(
        'document_tables',
        sa.Column('id', sa.Integer(), primary_key=True),
        # ... columns
    )

    # Create document_formulas table
    op.create_table(
        'document_formulas',
        sa.Column('id', sa.Integer(), primary_key=True),
        # ... columns
    )

    # Update chunks table
    op.add_column('chunks', sa.Column('has_tables', sa.Boolean(), default=False))
    op.add_column('chunks', sa.Column('has_formulas', sa.Boolean(), default=False))
    op.add_column('chunks', sa.Column('element_references', JSONB(), nullable=True))
```

**Tasks**:
- [ ] Create Alembic migration
- [ ] Add SQLAlchemy models for tables/formulas
- [ ] Add relationships to documents/chunks
- [ ] Update Pydantic schemas
- [ ] Test migrations

### Week 2: Intelligent Chunking & Integration

**Days 1-3: Structure-Aware Chunking**
```python
# File: backend/services/text_chunker.py (ENHANCED)

class StructureAwareChunker:
    def __init__(self):
        self.base_chunk_size = 1000  # characters
        self.overlap = 200

    async def chunk_with_structure(
        self,
        pdf_path: str,
        toc_structure: TocExtractionResult,
        tables: List[ExtractedTable],
        formulas: List[ExtractedFormula]
    ) -> List[EnhancedChunk]:
        """
        Create chunks that respect document structure:
        - Don't split across chapter boundaries
        - Keep tables within single chunks
        - Preserve formula context
        - Link chunks to categories (from ToC)
        """
        # Implementation
        pass
```

**Tasks**:
- [ ] Implement structure-aware chunking algorithm
- [ ] Respect ToC boundaries (chapter/section)
- [ ] Handle table preservation
- [ ] Handle formula context preservation
- [ ] Link chunks to categories
- [ ] Test with various PDF structures

**Days 4-5: API Endpoints**
```python
# File: backend/api/routes/documents.py (NEW ENDPOINTS)

@router.get("/{document_id}/tables", response_model=TablesResponse)
async def get_document_tables(
    document_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tables extracted from a document"""
    pass

@router.get("/{document_id}/formulas", response_model=FormulasResponse)
async def get_document_formulas(
    document_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all formulas extracted from a document"""
    pass

@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    extract_tables: bool = True,
    extract_formulas: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Reprocess document with enhanced extraction"""
    pass
```

**Tasks**:
- [ ] Add endpoint to list tables
- [ ] Add endpoint to list formulas
- [ ] Add endpoint to get single table/formula
- [ ] Add reprocess endpoint for existing documents
- [ ] Update document processing endpoint

**Days 6-7: Testing & Documentation**

**Tasks**:
- [ ] Unit tests for table extraction
- [ ] Unit tests for formula extraction
- [ ] Integration tests for enhanced processing
- [ ] Test with various PDF types:
  - Scientific papers (formulas)
  - Technical manuals (tables)
  - Mixed content documents
- [ ] Performance tests (100+ page PDFs)
- [ ] Update API documentation
- [ ] Create user guide for table/formula features

---

## 🔧 Technology Stack

### Python Libraries

**Required**:
```bash
# Already installed:
- docling>=1.0.0  # TableFormer, formula detection
- PyMuPDF>=1.23.0  # PDF processing

# To install:
- pdfplumber>=0.10.0  # Table extraction backup
- latex2mathml>=3.0.0  # Formula conversion
```

**Installation**:
```bash
pip install pdfplumber latex2mathml
```

### Docling Configuration

**TableFormer Setup**:
```python
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter

# Configure Docling for table extraction
pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True  # Enable TableFormer
pipeline_options.table_structure_options.do_cell_matching = True

converter = DocumentConverter(
    pipeline_options=pipeline_options
)
```

**Formula Detection Setup**:
```python
# Docling automatically detects formulas in PDF structure
# Extract formula regions and convert to LaTeX
```

---

## 📊 Performance Targets

### Extraction Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Table Extraction Rate | >90% | For PDFs with structured tables |
| Formula Extraction Rate | >85% | For PDFs with LaTeX-compatible formulas |
| Processing Time | <5 min | For 100-page PDF with 50 tables |
| Memory Usage | <2GB | Peak memory during processing |
| Chunk Quality | >95% | Chunks respect structure boundaries |

### Quality Metrics

| Feature | Metric | Target |
|---------|--------|--------|
| Table Structure | Cell accuracy | >95% |
| Formula Conversion | LaTeX validity | >90% |
| Chunking | Boundary respect | 100% |
| Element Linking | Correct references | >98% |

---

## 🚨 Risk Assessment

### High Priority Risks

**Risk 1: Complex Table Structures**
- **Impact**: Medium - Some tables may not extract correctly
- **Mitigation**: Dual extraction method (Docling + pdfplumber)
- **Fallback**: Manual table definition UI (Phase 3)

**Risk 2: Formula Recognition**
- **Impact**: Medium - Not all formulas are in standard format
- **Mitigation**: Multiple detection methods, confidence scoring
- **Fallback**: Display formula as image instead of LaTeX

**Risk 3: Performance with Large PDFs**
- **Impact**: Medium - Processing time may exceed targets
- **Mitigation**: Async processing, progress tracking, chunk processing
- **Fallback**: Process in background, notify user when complete

### Medium Priority Risks

**Risk 4: Memory Usage**
- **Impact**: Low - Large PDFs may consume significant memory
- **Mitigation**: Stream processing, garbage collection
- **Fallback**: Process page-by-page instead of full document

**Risk 5: Library Compatibility**
- **Impact**: Low - Dependencies may conflict
- **Mitigation**: Version pinning, virtual environment testing
- **Fallback**: Use alternative libraries

---

## ✅ Acceptance Criteria

### Phase 2 Complete When:

**Core Functionality**:
- [ ] Table extraction working for 3+ test PDFs
- [ ] Formula extraction working for 2+ scientific PDFs
- [ ] Structure-aware chunking respects ToC boundaries
- [ ] Tables and formulas stored in database
- [ ] API endpoints functional and tested

**Quality**:
- [ ] Table extraction accuracy >90%
- [ ] Formula extraction accuracy >85%
- [ ] Processing time <5 min for 100-page PDF
- [ ] No memory leaks or crashes

**Integration**:
- [ ] Tables linked to chunks correctly
- [ ] Formulas linked to chunks correctly
- [ ] RAG pipeline includes table/formula content
- [ ] Search returns relevant tables/formulas

**Testing**:
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] End-to-end test with real PDFs
- [ ] Performance benchmarks met

**Documentation**:
- [ ] API endpoints documented
- [ ] User guide created
- [ ] Developer guide updated
- [ ] Migration guide for existing documents

---

## 🔄 Integration with Existing System

### RAG Pipeline Enhancement

**Current Flow**:
```
User Query → Vector Search → Retrieve Chunks → Generate Response
```

**Enhanced Flow (Phase 2)**:
```
User Query → Vector Search → Retrieve Chunks + Tables + Formulas → Generate Response
```

**Implementation**:
```python
# Enhanced RAG service
class RAGService:
    async def retrieve_context(
        self,
        query: str,
        project_id: int,
        include_tables: bool = True,
        include_formulas: bool = True
    ) -> RetrievedContext:
        # 1. Vector search for chunks
        chunks = await self.search_chunks(query, project_id)

        # 2. Get linked tables
        tables = []
        if include_tables:
            for chunk in chunks:
                if chunk.has_tables:
                    tables.extend(await self.get_chunk_tables(chunk.id))

        # 3. Get linked formulas
        formulas = []
        if include_formulas:
            for chunk in chunks:
                if chunk.has_formulas:
                    formulas.extend(await self.get_chunk_formulas(chunk.id))

        return RetrievedContext(
            chunks=chunks,
            tables=tables,
            formulas=formulas
        )
```

### Artifact Generation Enhancement

**Update artifact generator to use tables/formulas**:
```python
# When generating summaries/articles, include tables and formulas
context_text = self._format_context_with_elements(
    chunks=chunks,
    tables=tables,
    formulas=formulas
)
```

---

## 📝 Next Steps After Phase 2

### Phase 3 Options (Professional Tier Completion)

**Option A: Chart/Diagram Extraction**
- Extract images from PDF
- Basic OCR for chart text
- Store with metadata
- **Timeline**: 1 week

**Option B: Enhanced Metadata**
- Extract authors, dates, citations
- Parse document properties
- Add to search index
- **Timeline**: 3-5 days

**Option C: Frontend Visualization**
- Visual tree view of document structure
- Interactive table browser
- Formula renderer
- **Timeline**: 1-2 weeks

---

## 🎯 Success Definition

**Phase 2 is successful when**:
1. ✅ Users can upload PDFs and automatically extract tables
2. ✅ Formulas are detected and converted to LaTeX
3. ✅ Document chunks respect structural boundaries
4. ✅ RAG responses include table and formula content
5. ✅ System performance meets targets
6. ✅ All tests passing
7. ✅ Documentation complete

---

**Plan Created**: 2026-01-21
**Created By**: Claude Sonnet 4.5
**Status**: Ready for Implementation
**Estimated Duration**: 1-2 weeks

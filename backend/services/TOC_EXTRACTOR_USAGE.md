# TocExtractor Service - Usage Guide

Quick reference for using the TocExtractor service in KnowledgeTree.

---

## 📚 Overview

The `TocExtractor` service extracts Table of Contents (ToC) from PDF documents using a hybrid waterfall approach:

1. **pypdf** (fast, accurate for PDFs with outline)
2. **PyMuPDF** (reliable fallback)
3. **Docling** (structure analysis for PDFs without explicit ToC)

---

## 🚀 Quick Start

### Standalone Usage

```python
from pathlib import Path
from services.toc_extractor import TocExtractor

# Create extractor
extractor = TocExtractor(max_depth=10)

# Extract ToC
pdf_path = Path("document.pdf")
result = extractor.extract(pdf_path)

# Check results
if result.success:
    print(f"✅ Found {result.total_entries} ToC entries")
    print(f"   Max depth: {result.max_depth}")
    print(f"   Method: {result.method.value}")

    # Iterate over entries
    for entry in result.entries:
        indent = "  " * entry.level
        print(f"{indent}{entry.title} (page {entry.page})")
else:
    print(f"❌ Extraction failed: {result.error}")
```

### Convenience Function

```python
from pathlib import Path
from services import extract_toc

# Quick extraction with default settings
result = extract_toc(Path("document.pdf"), max_depth=10)
```

### Integration with PDFProcessor

```python
from pathlib import Path
from services import PDFProcessor

# Create processor
processor = PDFProcessor(toc_max_depth=10)

# Extract ToC only
toc_result = processor.extract_toc(Path("document.pdf"))

# Or full processing (text + ToC)
full_results = processor.process_pdf_full(
    Path("document.pdf"),
    extract_text=True,
    extract_toc=True,
    prefer_docling=True
)

print(f"Text: {len(full_results['text'])} characters")
print(f"Pages: {full_results['page_count']}")
print(f"ToC entries: {full_results['toc'].total_entries}")
```

---

## 📊 Data Structures

### TocEntry

Represents a single ToC entry with hierarchical structure:

```python
@dataclass
class TocEntry:
    title: str              # Chapter/section title
    level: int              # Hierarchy depth (0-based)
    page: Optional[int]     # Source page number (1-based)
    children: List[TocEntry]  # Nested entries
    metadata: Optional[Dict]  # Additional info
```

**Methods**:
- `to_dict()` - Convert to dictionary
- `from_dict(data)` - Create from dictionary
- `flatten()` - Get flat list of all entries
- `count_entries()` - Count total entries (including children)
- `max_depth()` - Calculate maximum hierarchy depth

**Example**:
```python
entry = TocEntry(
    title="Chapter 1: Introduction",
    level=0,
    page=1,
    children=[
        TocEntry(title="1.1 Background", level=1, page=2),
        TocEntry(title="1.2 Objectives", level=1, page=5)
    ]
)

# Flatten hierarchy
flat_list = entry.flatten()  # [Chapter 1, 1.1, 1.2]

# Count entries
total = entry.count_entries()  # 3

# Get max depth
depth = entry.max_depth()  # 1
```

### TocExtractionResult

Results from ToC extraction:

```python
@dataclass
class TocExtractionResult:
    method: ExtractionMethod     # Method used
    success: bool                # Extraction succeeded?
    entries: List[TocEntry]      # ToC entries
    total_entries: int           # Total count (auto-calculated)
    max_depth: int               # Maximum depth (auto-calculated)
    error: Optional[str]         # Error message if failed
    metadata: Optional[Dict]     # Additional info
```

**Methods**:
- `to_dict()` - Convert to dictionary
- `flatten_entries()` - Get flat list of all entries

**Example**:
```python
result = TocExtractionResult(
    method=ExtractionMethod.PYPDF,
    success=True,
    entries=[...],
    metadata={'page_count': 100}
)

# Convert to dict (for JSON serialization)
data = result.to_dict()

# Get flat list
flat = result.flatten_entries()
```

### ExtractionMethod (Enum)

```python
class ExtractionMethod(str, Enum):
    PYPDF = "pypdf"
    PYMUPDF = "pymupdf"
    DOCLING = "docling"
    NONE = "none"
```

---

## 🎯 Method Selection

### Automatic (Hybrid Waterfall)

```python
# Default - tries all methods in order
result = extractor.extract(pdf_path)
```

Priority:
1. pypdf (fastest, 80-85% PDFs)
2. PyMuPDF (fallback, 80-85% PDFs)
3. Docling (structure analysis, 15-20% PDFs)

### Manual Method Selection

```python
from services.toc_extractor import ExtractionMethod

# Force specific method
result = extractor.extract(pdf_path, method=ExtractionMethod.PYPDF)
```

---

## 🔄 Processing Workflow

### Example: Full PDF Processing Pipeline

```python
from pathlib import Path
from services import PDFProcessor, TextChunker

# 1. Initialize
processor = PDFProcessor(toc_max_depth=10)
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)

# 2. Process PDF
pdf_path = Path("uploads/documents/book.pdf")
results = processor.process_pdf_full(pdf_path)

# 3. Handle ToC
toc_result = results['toc']
if toc_result.success:
    print(f"✅ ToC extracted: {toc_result.total_entries} entries")

    # Convert to category tree (future implementation)
    # categories = toc_to_category_tree(toc_result.entries, project_id)

else:
    print(f"⚠️ No ToC found: {toc_result.error}")
    # Fallback to manual structure definition

# 4. Chunk text
text = results['text']
chunks = chunker.chunk_text(text, preserve_sentences=True)

print(f"Created {len(chunks)} chunks")
```

---

## 🧪 Error Handling

### Common Errors

**1. File Not Found**:
```python
result = extractor.extract(Path("/nonexistent/file.pdf"))
# result.success = False
# result.error = "PDF file not found: /nonexistent/file.pdf"
```

**2. Invalid PDF**:
```python
result = extractor.extract(Path("document.txt"))
# result.success = False
# result.error = "File is not a PDF: document.txt"
```

**3. No ToC Found**:
```python
result = extractor.extract(Path("scan.pdf"))
# result.success = False
# result.method = ExtractionMethod.NONE
# result.error = "No ToC found - PDF may not have embedded outline"
```

### Handling Failures

```python
result = extractor.extract(pdf_path)

if not result.success:
    if "not found" in result.error:
        # File doesn't exist
        logger.error(f"File not found: {pdf_path}")
    elif "No ToC found" in result.error:
        # PDF has no outline - fallback to manual
        logger.warning("No ToC found, using manual structure")
        # Prompt user to define structure manually
    else:
        # Other error
        logger.error(f"Extraction failed: {result.error}")
```

---

## 📈 Performance Expectations

| Method | Speed | Success Rate | Use Case |
|--------|-------|--------------|----------|
| **pypdf** | ⚡ 50-200ms | 80-85% PDFs | PDFs with outline |
| **PyMuPDF** | ⚡ 50-200ms | 80-85% PDFs | Fallback |
| **Docling** | 🐢 2-10s | 15-20% PDFs | Structure inference |

**Typical Performance**:
- Small PDF (<50 pages): ~100ms
- Medium PDF (100-200 pages): ~200-500ms
- Large PDF (500+ pages): ~1-2s

---

## 🔍 Advanced Usage

### Custom Max Depth

```python
# Limit hierarchy depth
extractor = TocExtractor(max_depth=5)

result = extractor.extract(pdf_path)
# Entries with level > 5 will be skipped with warning
```

### Analyzing Results

```python
result = extractor.extract(pdf_path)

if result.success:
    # Get statistics
    total = result.total_entries
    depth = result.max_depth
    method = result.method.value

    # Flatten hierarchy
    flat_entries = result.flatten_entries()

    # Filter by level
    chapters = [e for e in flat_entries if e.level == 0]
    sections = [e for e in flat_entries if e.level == 1]

    # Find specific entry
    intro = next((e for e in flat_entries if "introduction" in e.title.lower()), None)

    # Export to JSON
    import json
    json_data = json.dumps(result.to_dict(), indent=2)
```

### Metadata Analysis

```python
result = extractor.extract(pdf_path)

if result.metadata:
    page_count = result.metadata.get('page_count')
    encrypted = result.metadata.get('encrypted', False)

    print(f"Document: {page_count} pages")
    if encrypted:
        print("⚠️ Document is encrypted")
```

---

## 🧩 Integration Examples

### API Endpoint

```python
from fastapi import APIRouter, HTTPException
from pathlib import Path
from services import PDFProcessor

router = APIRouter()

@router.post("/documents/{document_id}/extract-toc")
async def extract_document_toc(document_id: int):
    """Extract ToC from uploaded document"""
    try:
        # Get document from DB
        document = await get_document(document_id)
        pdf_path = Path(document.file_path)

        # Extract ToC
        processor = PDFProcessor()
        result = processor.extract_toc(pdf_path)

        if result.success:
            return {
                "success": True,
                "method": result.method.value,
                "total_entries": result.total_entries,
                "max_depth": result.max_depth,
                "entries": [e.to_dict() for e in result.entries]
            }
        else:
            return {
                "success": False,
                "error": result.error
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Background Job

```python
from celery import shared_task
from services import PDFProcessor

@shared_task
def process_document_async(document_id: int):
    """Process document in background"""
    document = Document.query.get(document_id)

    processor = PDFProcessor()
    results = processor.process_pdf_full(
        Path(document.file_path),
        extract_text=True,
        extract_toc=True
    )

    # Update document
    document.page_count = results['page_count']
    document.processing_status = "completed"

    # Store ToC
    if results['toc'].success:
        document.toc_data = results['toc'].to_dict()
        # Generate category tree
        # ...

    db.session.commit()
```

---

## 🧪 Testing

### Unit Tests

```python
from services.toc_extractor import TocEntry, TocExtractor

def test_toc_entry_creation():
    entry = TocEntry(
        title="Chapter 1",
        level=0,
        page=1
    )
    assert entry.title == "Chapter 1"
    assert entry.level == 0
```

### Integration Tests

```python
from pathlib import Path
from services import extract_toc

def test_extract_from_real_pdf():
    """Test with actual PDF file"""
    pdf_path = Path("tests/fixtures/sample.pdf")
    result = extract_toc(pdf_path)

    assert result.success is True
    assert result.total_entries > 0
    assert result.max_depth >= 0
```

---

## 📚 See Also

- **[TOC_EXTRACTION_RESEARCH.md](../research/TOC_EXTRACTION_RESEARCH.md)** - Research findings
- **[README.md](../research/README.md)** - Research script usage
- **[TIER2_PHASE5_GAP_ANALYSIS.md](../../TIER2_PHASE5_GAP_ANALYSIS.md)** - Gap analysis

---

## 💡 Tips & Best Practices

1. **Always check `result.success`** before accessing entries
2. **Use hybrid approach** (default) for best results
3. **Handle failures gracefully** with fallback to manual structure
4. **Validate depth** if working with very deep hierarchies
5. **Cache results** for repeated access to same PDF
6. **Log method used** for analytics and debugging
7. **Test with various PDFs** to understand success rates

---

## 🚀 Future Enhancements

Planned improvements (Phase 2+):

- [ ] Heading detection fallback (Docling font-based)
- [ ] ToC → Category Tree automatic mapping
- [ ] Manual ToC editor UI
- [ ] OCR integration for scanned PDFs
- [ ] Page range calculation
- [ ] Section content extraction
- [ ] Multi-level validation

---

**Version**: 1.0
**Date**: 2026-01-20
**Status**: Production Ready

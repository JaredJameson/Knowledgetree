# CategoryTreeGenerator Service - Usage Guide

Quick reference for using the CategoryTreeGenerator service in KnowledgeTree.

---

## 📚 Overview

The `CategoryTreeGenerator` service converts Table of Contents (ToC) from PDFs into hierarchical Category tree structures for the KnowledgeTree application.

**Key Features**:
- Automatic TocEntry → Category mapping
- Color and icon assignment
- Title cleaning and slug generation
- Depth validation (max 10 levels)
- Parent support (append to existing trees)

---

## 🚀 Quick Start

### Standalone Usage

```python
from pathlib import Path
from services import PDFProcessor, generate_category_tree

# 1. Extract ToC from PDF
processor = PDFProcessor()
toc_result = processor.extract_toc(Path("book.pdf"))

# 2. Generate category tree
categories, stats = generate_category_tree(
    toc_result=toc_result,
    project_id=1
)

# 3. Check results
print(f"✅ Generated {stats['total_created']} categories")
print(f"   Max depth: {stats['max_depth']}")
print(f"   Skipped: {stats['skipped_depth']}")

# 4. Insert into database
for category in categories:
    db.add(category)
db.commit()
```

### With CategoryTreeGenerator Class

```python
from services import CategoryTreeGenerator

# Create generator
generator = CategoryTreeGenerator()

# Generate tree with custom options
categories, stats = generator.generate_tree(
    toc_result=toc_result,
    project_id=1,
    parent_id=None,          # Optional parent category
    validate_depth=True      # Enforce max depth
)
```

---

## 📊 Data Structures

### Input: TocExtractionResult

From Phase 1 (ToC extraction):

```python
@dataclass
class TocExtractionResult:
    method: ExtractionMethod
    success: bool
    entries: List[TocEntry]        # Hierarchical ToC entries
    total_entries: int
    max_depth: int
    error: Optional[str]
    metadata: Optional[Dict]
```

### Output: Categories List

```python
categories: List[Category] = [
    Category(
        name="Introduction",           # Cleaned title
        description="Page 1",          # Page reference
        color="#E6E6FA",               # Auto-assigned
        icon="Book",                   # Depth-based
        depth=0,                       # 0-based level
        order=0,                       # Sequential
        parent_id=None,                # Root
        project_id=1
    ),
    # ... more categories
]
```

### Output: Statistics Dict

```python
stats: Dict[str, int] = {
    "total_entries": 15,      # From ToC
    "total_created": 15,      # Categories created
    "skipped_depth": 0,       # Entries beyond max depth
    "max_depth": 3            # Maximum depth in tree
}
```

---

## 🎯 Features

### 1. Title Cleaning

Removes chapter numbers and normalizes whitespace:

```python
generator = CategoryTreeGenerator()

# Examples
generator._clean_title("1.2.3 Section Title")  # → "Section Title"
generator._clean_title("Chapter 1: Intro")     # → "Chapter 1: Intro"
generator._clean_title("  Multiple   Spaces ") # → "Multiple Spaces"
```

### 2. Slug Generation

Creates URL-friendly slugs with duplicate handling:

```python
generator = CategoryTreeGenerator()

slug1 = generator.generate_slug("Chapter 1: Introduction")
# → "chapter-1-introduction"

slug2 = generator.generate_slug("Chapter 1: Introduction")  # duplicate
# → "chapter-1-introduction-2"

slug3 = generator.generate_slug("Section 1.2.3: A/B Testing!")
# → "section-1-2-3-a-b-testing"
```

### 3. Color Assignment

8 pastel colors in round-robin:

```python
PASTEL_COLORS = [
    "#E6E6FA",  # Lavender
    "#FFE4E1",  # Misty Rose
    "#E0FFE0",  # Light Green
    "#FFE4B5",  # Moccasin
    "#E0F4FF",  # Light Blue
    "#FFE4FF",  # Light Pink
    "#FFEAA7",  # Light Yellow
    "#DCD0FF",  # Light Purple
]
```

### 4. Icon Assignment

Depth-based Lucide icons:

```python
DEPTH_ICONS = {
    0: "Book",           # Chapters
    1: "BookOpen",       # Sections
    2: "FileText",       # Subsections
    3: "File",           # Level 3
    4: "FileCode",       # Level 4
    5: "FileJson",       # Level 5
}
# depth > 5 → "Folder"
```

### 5. Description Generation

Includes page numbers and metadata:

```python
# With page number
entry = TocEntry(title="Chapter 1", level=0, page=5)
# → description: "Page 5"

# With page range
entry = TocEntry(
    title="Chapter 1",
    level=0,
    page=5,
    metadata={"page_range": "5-15"}
)
# → description: "Page 5 | Pages 5-15"
```

---

## 🔄 Processing Workflow

### Complete Pipeline

```python
from pathlib import Path
from services import PDFProcessor, generate_category_tree
from models.category import Category
from sqlalchemy import select

# 1. Upload and process PDF
pdf_path = Path("uploads/documents/1_book.pdf")
processor = PDFProcessor()

# 2. Extract ToC
toc_result = processor.extract_toc(pdf_path)

if not toc_result.success:
    print(f"❌ ToC extraction failed: {toc_result.error}")
    # Fallback: Manual category creation
else:
    print(f"✅ Extracted {toc_result.total_entries} ToC entries")

    # 3. Generate category tree
    categories, stats = generate_category_tree(
        toc_result=toc_result,
        project_id=1
    )

    print(f"✅ Generated {stats['total_created']} categories")

    # 4. Insert into database (hierarchical order)
    # Note: Must insert parents before children
    # Use _insert_categories_hierarchical() helper

    # 5. Assign document to root category
    root_category = categories[0]  # First category
    document.category_id = root_category.id
    db.commit()
```

---

## 🧪 Error Handling

### Common Errors

**1. ToC Extraction Failed**:
```python
try:
    categories, stats = generate_category_tree(toc_result, project_id=1)
except ValueError as e:
    if "ToC extraction failed" in str(e):
        # ToC extraction didn't succeed
        print(f"Error: {e}")
        # Fallback: Manual category creation or retry
```

**2. No ToC Entries**:
```python
try:
    categories, stats = generate_category_tree(toc_result, project_id=1)
except ValueError as e:
    if "No ToC entries found" in str(e):
        # ToC was empty
        print("PDF has no ToC - using manual structure")
        # Fallback: Create default category
```

**3. Depth Limit Exceeded**:
```python
categories, stats = generate_category_tree(
    toc_result=toc_result,
    project_id=1,
    validate_depth=True
)

if stats['skipped_depth'] > 0:
    print(f"⚠️ Skipped {stats['skipped_depth']} deep entries (>10 levels)")
    # Categories beyond depth 10 were excluded
```

### Handling Failures

```python
toc_result = processor.extract_toc(pdf_path)

if not toc_result.success:
    # Log error
    logger.warning(f"ToC extraction failed: {toc_result.error}")

    # Fallback strategies:
    # 1. Create default category from document title
    default_category = Category(
        name=document.title,
        color="#E6E6FA",
        icon="Book",
        depth=0,
        order=0,
        project_id=document.project_id
    )
    db.add(default_category)
    db.commit()

    # 2. Or prompt user to define structure manually
else:
    # Generate tree from ToC
    categories, stats = generate_category_tree(toc_result, document.project_id)
```

---

## 📈 Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| **Processing Time** | <1s (100-entry ToC) |
| **Memory Usage** | ~10MB (1000 categories) |
| **Success Rate** | 100% (when ToC extracted) |
| **Max Entries** | ~1000 (typical book) |

**Typical Performance**:
- Small ToC (<20 entries): ~100ms
- Medium ToC (20-100 entries): ~200-500ms
- Large ToC (100-500 entries): ~500ms-1s

---

## 🔍 Advanced Usage

### Appending to Existing Tree

```python
# Get existing parent category
parent_result = await db.execute(
    select(Category).where(Category.id == 5)
)
parent = parent_result.scalar_one()

# Generate tree as subtree
categories, stats = generator.generate_tree(
    toc_result=toc_result,
    project_id=1,
    parent_id=parent.id  # Append under this parent
)

# Categories will have depth offset
# If parent.depth = 2, children will start at depth 3
```

### Custom Validation

```python
# Disable depth validation (allow deep trees)
categories, stats = generator.generate_tree(
    toc_result=toc_result,
    project_id=1,
    validate_depth=False  # No depth limit
)

# Check depth manually
if stats['max_depth'] > 15:
    logger.warning(f"Very deep tree: {stats['max_depth']} levels")
```

### Analyzing Results

```python
categories, stats = generate_category_tree(toc_result, project_id=1)

# Get statistics
total_created = stats['total_created']
max_depth = stats['max_depth']
skipped = stats['skipped_depth']

# Filter by depth
root_categories = [c for c in categories if c.depth == 0]
leaf_categories = [c for c in categories if c.depth == max_depth]

# Get color distribution
from collections import Counter
color_counts = Counter(c.color for c in categories)

print(f"Color distribution: {color_counts}")
```

---

## 🧩 Integration Examples

### With API Endpoint

See `api/routes/documents.py` for complete implementation:

```python
@router.post("/{document_id}/generate-tree")
async def generate_category_tree_from_toc(
    document_id: int,
    request: GenerateTreeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Get document
    document = await get_document_or_404(document_id, current_user, db)

    # 2. Extract ToC
    toc_result = pdf_processor.extract_toc(Path(document.file_path))

    # 3. Generate tree
    categories, stats = generate_category_tree(
        toc_result=toc_result,
        project_id=document.project_id
    )

    # 4. Insert into database (hierarchical)
    inserted = await _insert_categories_hierarchical(db, ...)

    # 5. Return response
    return GenerateTreeResponse(
        success=True,
        message=f"Generated {len(inserted)} categories",
        categories=[CategoryResponse.model_validate(c) for c in inserted],
        stats=stats
    )
```

### With Background Job

```python
from celery import shared_task

@shared_task
def process_document_with_tree(document_id: int):
    """Process document and generate category tree"""
    document = Document.query.get(document_id)

    # Extract ToC
    processor = PDFProcessor()
    toc_result = processor.extract_toc(Path(document.file_path))

    if toc_result.success:
        # Generate tree
        categories, stats = generate_category_tree(
            toc_result=toc_result,
            project_id=document.project_id
        )

        # Insert categories
        for category in categories:
            db.session.add(category)
        db.session.commit()

        # Update document
        document.category_id = categories[0].id
        db.session.commit()
```

---

## 💡 Tips & Best Practices

1. **Always check ToC extraction success** before generating tree
2. **Use hierarchical insertion** to maintain parent-child relationships
3. **Handle depth limits gracefully** with user feedback
4. **Cache generator instance** if generating multiple trees (reuses state)
5. **Validate project_id** before insertion to ensure proper isolation
6. **Log statistics** for monitoring and debugging
7. **Test with various PDFs** to understand success rates

---

## 🚀 Future Enhancements

Planned improvements (Phase 3+):

- [ ] **AI-Enhanced Naming**: Improve category names with LLM
- [ ] **Batch Operations**: Process multiple PDFs at once
- [ ] **Tree Validation**: Check for inconsistencies
- [ ] **Template Support**: Pre-defined category structures
- [ ] **Import/Export**: JSON format for tree backup/restore

---

## 📚 See Also

- **[CATEGORY_TREE_GENERATOR_IMPLEMENTATION.md](../../CATEGORY_TREE_GENERATOR_IMPLEMENTATION.md)** - Implementation details
- **[TOC_EXTRACTOR_USAGE.md](./TOC_EXTRACTOR_USAGE.md)** - ToC extraction guide
- **[backend/api/routes/documents.py](../api/routes/documents.py)** - API endpoint implementation

---

**Version**: 1.0
**Date**: 2026-01-20
**Status**: Production Ready

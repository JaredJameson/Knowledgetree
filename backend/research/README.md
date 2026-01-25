# KnowledgeTree - ToC Extraction Research

Research scripts and documentation for Table of Contents extraction from PDF documents.

---

## 📁 Files

### Research Scripts

- **`toc_extraction_research.py`** - Main research script for testing ToC extraction methods
- **`TOC_EXTRACTION_RESEARCH.md`** - Comprehensive research findings and recommendations

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/jarek/projects/knowledgetree/backend
pip install -r requirements.txt
```

**Required packages**:
- `pypdf>=4.0.0` - PDF outline extraction
- `pdfplumber>=0.11.0` - Table extraction backup
- `docling>=2.0.0` - Advanced document understanding (already installed)
- `PyMuPDF>=1.23.0` - PDF processing (already installed)

### 2. Run Research Script

```bash
python research/toc_extraction_research.py <path_to_pdf> [--output results.json]
```

**Example**:
```bash
# Test with academic paper
python research/toc_extraction_research.py ~/Documents/sample_paper.pdf

# Save results to custom file
python research/toc_extraction_research.py ~/Documents/book.pdf --output book_toc_results.json
```

---

## 📊 What the Script Does

### Methods Tested

1. **Docling** - Advanced document understanding
   - Structure analysis
   - Heading detection
   - Section hierarchy inference

2. **pypdf** - Direct PDF outline extraction
   - Fast and accurate
   - Requires embedded outline/bookmarks
   - Hierarchical structure preserved

3. **PyMuPDF (fitz)** - Fallback outline extraction
   - Already in use in project
   - Simple API
   - Good reliability

### Output

The script will:
- ✅ Test all 3 methods on your PDF
- ✅ Show extraction results (entries, hierarchy depth)
- ✅ Compare methods and recommend best approach
- ✅ Save detailed results to JSON
- ✅ Display first 5 ToC entries for preview

**Example Output**:
```
============================================================
🔬 ToC EXTRACTION RESEARCH
============================================================
📄 PDF: academic_paper.pdf
📍 Path: /home/user/documents/academic_paper.pdf
============================================================

🔍 Method 1: Docling
============================================================
📄 Processing: academic_paper.pdf
✅ Document converted successfully
   Pages: 25
   ⚠️  No ToC structure found

🔍 Method 2: pypdf
============================================================
📄 PDF Info:
   Pages: 25
   Encrypted: False
   ✅ Outline found!

📊 Results:
   Total entries: 15
   Max depth: 2

📋 First 5 entries:
   [L0] 1. Introduction (page 1)
     [L1] 1.1 Background (page 2)
     [L1] 1.2 Objectives (page 3)
   [L0] 2. Methods (page 5)
     [L1] 2.1 Experimental Setup (page 6)

🔍 Method 3: PyMuPDF (fitz)
============================================================
📄 PDF Info:
   Pages: 25
   Encrypted: False
   ✅ ToC found!

📊 Results:
   Total entries: 15
   Max depth: 2

============================================================
📊 SUMMARY
============================================================

PYPDF: ✅ SUCCESS
   Entries: 15
   Max depth: 2

PYMUPDF: ✅ SUCCESS
   Entries: 15
   Max depth: 2

DOCLING: ❌ FAILED
   Error: No ToC structure found

============================================================
💡 RECOMMENDATION
============================================================
✅ Best method: PYPDF
   Reason: Most entries (15)

💾 Results saved to: toc_research_results.json
```

---

## 📝 Results JSON Format

```json
{
  "pdf_path": "/path/to/document.pdf",
  "pdf_name": "document.pdf",
  "methods": {
    "pypdf": {
      "method": "pypdf",
      "success": true,
      "entries": [
        {
          "title": "Chapter 1: Introduction",
          "level": 0,
          "page": 1,
          "children": [
            {
              "title": "1.1 Background",
              "level": 1,
              "page": 2,
              "children": []
            }
          ]
        }
      ],
      "total_entries": 15,
      "max_depth": 2,
      "error": null,
      "metadata": {
        "page_count": 25,
        "encrypted": false
      }
    }
  }
}
```

---

## 🧪 Sample PDFs for Testing

### Where to Find Test PDFs

1. **Academic Papers**: arXiv.org, IEEE, ACM Digital Library
2. **Technical Books**: O'Reilly, Manning (preview chapters)
3. **Open-Source Books**: GitHub repos with documentation
4. **Government Reports**: Often have detailed ToC

### Good Test Cases

**Simple Structure** (2-3 levels):
- Academic papers
- Short reports
- Magazine articles

**Complex Structure** (4-6 levels):
- Technical books (100+ pages)
- Textbooks
- Reference manuals

**Edge Cases**:
- Scanned PDFs (no embedded text)
- PDFs without ToC/outline
- Encrypted PDFs
- Very large files (500+ pages)

---

## 📊 Expected Results

### Success Scenarios

**Scenario 1**: PDF with embedded outline
- ✅ pypdf: SUCCESS (15+ entries, fast)
- ✅ PyMuPDF: SUCCESS (15+ entries, fast)
- ⚠️ Docling: May or may not find structure

**Scenario 2**: PDF without outline but structured content
- ❌ pypdf: FAILED (no outline)
- ❌ PyMuPDF: FAILED (no outline)
- ⚠️ Docling: May infer structure (slower, less accurate)

**Scenario 3**: Scanned PDF (no text layer)
- ❌ All methods: FAILED
- 💡 Recommendation: Enable OCR in Docling

### Interpretation

- **Total entries = 0**: PDF has no embedded ToC
  - **Solution**: Manual structure definition or heading detection

- **Max depth > 6**: Very complex hierarchy
  - **Solution**: May need depth limit or simplification

- **Multiple methods succeed**: High confidence
  - **Solution**: Use fastest method (pypdf)

- **Only one method succeeds**: Moderate confidence
  - **Solution**: Validate results manually

---

## 🛠️ Troubleshooting

### Issue: "ImportError: No module named 'pypdf'"

**Solution**:
```bash
pip install pypdf>=4.0.0
```

### Issue: "Docling not installed"

**Solution**:
```bash
pip install docling>=2.0.0
```

### Issue: "No ToC found in PDF"

**Possible Causes**:
1. PDF doesn't have embedded outline/bookmarks
2. Scanned PDF without text layer
3. Poorly structured PDF

**Solutions**:
1. Try with Docling (structure inference)
2. Enable OCR for scanned PDFs
3. Manual structure definition in UI
4. Contact PDF author for proper ToC

### Issue: "Script crashes or hangs"

**Possible Causes**:
1. Very large PDF (500+ pages)
2. Corrupted PDF
3. Memory issues

**Solutions**:
1. Test with smaller PDF first
2. Validate PDF with `pdfinfo` or Adobe Reader
3. Increase memory allocation

---

## 🔗 Related Documentation

- **[TOC_EXTRACTION_RESEARCH.md](./TOC_EXTRACTION_RESEARCH.md)** - Full research findings
- **[TIER2_PHASE5_GAP_ANALYSIS.md](../../TIER2_PHASE5_GAP_ANALYSIS.md)** - Gap analysis
- **[STATUS_REPORT_2026_01_20.md](../../STATUS_REPORT_2026_01_20.md)** - Project status

---

## 📞 Next Steps

After testing with sample PDFs:

1. ✅ Analyze results
2. ✅ Validate accuracy of extracted ToC
3. ✅ Decide on implementation approach
4. ✅ Implement `TocExtractor` service
5. ✅ Integrate with `PDFProcessor`
6. ✅ Build UI for reviewing/editing generated trees

---

## 📄 License

Part of KnowledgeTree project.

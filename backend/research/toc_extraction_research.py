"""
KnowledgeTree - ToC Extraction Research Script
===============================================

Purpose: Research and test different methods for extracting Table of Contents (ToC)
from PDF documents to enable automatic category tree generation.

Methods tested:
1. Docling - Advanced document understanding
2. pypdf - PDF outline/bookmarks extraction
3. PyMuPDF (fitz) - Outline extraction

Author: KnowledgeTree Team
Date: 2026-01-20
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    print("⚠️  Docling not installed. Install with: pip install docling>=2.0.0")
    DOCLING_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    print("⚠️  pypdf not installed. Install with: pip install pypdf>=4.0.0")
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️  PyMuPDF not installed. Install with: pip install PyMuPDF>=1.23.0")
    PYMUPDF_AVAILABLE = False


@dataclass
class TocEntry:
    """Represents a single ToC entry"""
    title: str
    level: int
    page: Optional[int] = None
    children: List['TocEntry'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'title': self.title,
            'level': self.level,
            'page': self.page,
        }
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        return result


@dataclass
class TocExtractionResult:
    """Results from ToC extraction"""
    method: str
    success: bool
    entries: List[TocEntry]
    total_entries: int
    max_depth: int
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'method': self.method,
            'success': self.success,
            'entries': [entry.to_dict() for entry in self.entries],
            'total_entries': self.total_entries,
            'max_depth': self.max_depth,
            'error': self.error,
            'metadata': self.metadata or {}
        }


class TocExtractor:
    """ToC extraction using multiple methods"""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if not self.pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"Not a PDF file: {pdf_path}")

    def extract_with_docling(self) -> TocExtractionResult:
        """
        Extract ToC using Docling

        Docling provides advanced document understanding including:
        - Document structure analysis
        - Heading detection
        - Section hierarchy
        """
        if not DOCLING_AVAILABLE:
            return TocExtractionResult(
                method="docling",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error="Docling not installed"
            )

        try:
            print("\n🔍 Method 1: Docling")
            print("=" * 60)

            # Configure Docling with advanced options
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.do_ocr = False  # OCR not needed for ToC

            converter = DocumentConverter(
                format_options={
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            # Convert document
            print(f"📄 Processing: {self.pdf_path.name}")
            result = converter.convert(str(self.pdf_path))

            # Explore document structure
            doc = result.document
            print(f"✅ Document converted successfully")
            print(f"   Pages: {len(doc.pages) if hasattr(doc, 'pages') else 'N/A'}")

            # Check available attributes
            print(f"\n📋 Available attributes:")
            attrs = [attr for attr in dir(doc) if not attr.startswith('_')]
            for attr in attrs[:20]:  # Show first 20
                print(f"   - {attr}")

            # Try to extract structure
            entries = []
            metadata = {
                'has_pages': hasattr(doc, 'pages'),
                'has_sections': hasattr(doc, 'sections'),
                'has_headings': hasattr(doc, 'headings'),
                'has_outline': hasattr(doc, 'outline'),
                'has_toc': hasattr(doc, 'toc'),
                'attributes': attrs
            }

            # Try different methods to extract ToC
            if hasattr(doc, 'outline') and doc.outline:
                print(f"   ✅ Found 'outline' attribute")
                entries = self._parse_docling_outline(doc.outline)
            elif hasattr(doc, 'toc') and doc.toc:
                print(f"   ✅ Found 'toc' attribute")
                entries = self._parse_docling_toc(doc.toc)
            elif hasattr(doc, 'sections') and doc.sections:
                print(f"   ✅ Found 'sections' attribute")
                entries = self._parse_docling_sections(doc.sections)
            else:
                print(f"   ⚠️  No ToC structure found")

            max_depth = max([e.level for e in entries], default=0)

            return TocExtractionResult(
                method="docling",
                success=len(entries) > 0,
                entries=entries,
                total_entries=len(entries),
                max_depth=max_depth,
                metadata=metadata
            )

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return TocExtractionResult(
                method="docling",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error=str(e)
            )

    def _parse_docling_outline(self, outline) -> List[TocEntry]:
        """Parse Docling outline structure"""
        # TODO: Implement based on actual structure
        return []

    def _parse_docling_toc(self, toc) -> List[TocEntry]:
        """Parse Docling ToC structure"""
        # TODO: Implement based on actual structure
        return []

    def _parse_docling_sections(self, sections) -> List[TocEntry]:
        """Parse Docling sections structure"""
        # TODO: Implement based on actual structure
        return []

    def extract_with_pypdf(self) -> TocExtractionResult:
        """
        Extract ToC using pypdf

        pypdf can extract PDF outline/bookmarks which typically represent
        the document's table of contents.
        """
        if not PYPDF_AVAILABLE:
            return TocExtractionResult(
                method="pypdf",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error="pypdf not installed"
            )

        try:
            print("\n🔍 Method 2: pypdf")
            print("=" * 60)

            with open(self.pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)

                print(f"📄 PDF Info:")
                print(f"   Pages: {len(reader.pages)}")
                print(f"   Encrypted: {reader.is_encrypted}")

                # Extract outline (bookmarks/ToC)
                outline = reader.outline

                if not outline:
                    print(f"   ⚠️  No outline/bookmarks found")
                    return TocExtractionResult(
                        method="pypdf",
                        success=False,
                        entries=[],
                        total_entries=0,
                        max_depth=0,
                        error="No outline found in PDF"
                    )

                print(f"   ✅ Outline found!")

                # Parse outline recursively
                entries = self._parse_pypdf_outline(outline, reader)
                max_depth = max([e.level for e in entries], default=0)

                print(f"\n📊 Results:")
                print(f"   Total entries: {len(entries)}")
                print(f"   Max depth: {max_depth}")

                # Show first few entries
                print(f"\n📋 First 5 entries:")
                for entry in entries[:5]:
                    indent = "  " * entry.level
                    print(f"   {indent}[L{entry.level}] {entry.title} (page {entry.page})")

                return TocExtractionResult(
                    method="pypdf",
                    success=True,
                    entries=entries,
                    total_entries=len(entries),
                    max_depth=max_depth,
                    metadata={
                        'page_count': len(reader.pages),
                        'encrypted': reader.is_encrypted
                    }
                )

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return TocExtractionResult(
                method="pypdf",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error=str(e)
            )

    def _parse_pypdf_outline(
        self,
        outline: List,
        reader: pypdf.PdfReader,
        level: int = 0
    ) -> List[TocEntry]:
        """
        Recursively parse pypdf outline structure

        pypdf outline is a list that can contain:
        - Destination objects (bookmarks)
        - Nested lists (sub-bookmarks)
        """
        entries = []

        for item in outline:
            if isinstance(item, list):
                # Nested outline - recurse with increased level
                entries.extend(self._parse_pypdf_outline(item, reader, level + 1))
            else:
                # Bookmark destination
                try:
                    title = item.title if hasattr(item, 'title') else str(item)

                    # Get page number
                    page_num = None
                    if hasattr(item, 'page'):
                        try:
                            # Get page index from destination
                            page_obj = item.page
                            if page_obj:
                                page_num = reader.pages.index(page_obj) + 1  # 1-based
                        except:
                            pass

                    entry = TocEntry(
                        title=title,
                        level=level,
                        page=page_num
                    )
                    entries.append(entry)

                except Exception as e:
                    print(f"   ⚠️  Failed to parse outline item: {e}")

        return entries

    def extract_with_pymupdf(self) -> TocExtractionResult:
        """
        Extract ToC using PyMuPDF (fitz)

        PyMuPDF provides get_toc() method which extracts the document
        outline/table of contents.
        """
        if not PYMUPDF_AVAILABLE:
            return TocExtractionResult(
                method="pymupdf",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error="PyMuPDF not installed"
            )

        try:
            print("\n🔍 Method 3: PyMuPDF (fitz)")
            print("=" * 60)

            doc = fitz.open(self.pdf_path)

            print(f"📄 PDF Info:")
            print(f"   Pages: {len(doc)}")
            print(f"   Encrypted: {doc.is_encrypted}")

            # Get ToC
            toc = doc.get_toc()

            if not toc:
                print(f"   ⚠️  No ToC found")
                doc.close()
                return TocExtractionResult(
                    method="pymupdf",
                    success=False,
                    entries=[],
                    total_entries=0,
                    max_depth=0,
                    error="No ToC found in PDF"
                )

            print(f"   ✅ ToC found!")

            # Parse ToC
            # PyMuPDF ToC format: [[level, title, page], ...]
            entries = []
            for item in toc:
                level, title, page = item
                entry = TocEntry(
                    title=title,
                    level=level - 1,  # PyMuPDF uses 1-based levels, we use 0-based
                    page=page
                )
                entries.append(entry)

            max_depth = max([e.level for e in entries], default=0)

            print(f"\n📊 Results:")
            print(f"   Total entries: {len(entries)}")
            print(f"   Max depth: {max_depth}")

            # Show first few entries
            print(f"\n📋 First 5 entries:")
            for entry in entries[:5]:
                indent = "  " * entry.level
                print(f"   {indent}[L{entry.level}] {entry.title} (page {entry.page})")

            doc.close()

            return TocExtractionResult(
                method="pymupdf",
                success=True,
                entries=entries,
                total_entries=len(entries),
                max_depth=max_depth,
                metadata={
                    'page_count': len(doc),
                    'encrypted': doc.is_encrypted
                }
            )

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return TocExtractionResult(
                method="pymupdf",
                success=False,
                entries=[],
                total_entries=0,
                max_depth=0,
                error=str(e)
            )

    def run_all_methods(self) -> Dict[str, TocExtractionResult]:
        """Run all extraction methods and compare results"""
        print("\n" + "=" * 60)
        print("🔬 ToC EXTRACTION RESEARCH")
        print("=" * 60)
        print(f"📄 PDF: {self.pdf_path.name}")
        print(f"📍 Path: {self.pdf_path}")
        print("=" * 60)

        results = {}

        # Method 1: Docling
        if DOCLING_AVAILABLE:
            results['docling'] = self.extract_with_docling()

        # Method 2: pypdf
        if PYPDF_AVAILABLE:
            results['pypdf'] = self.extract_with_pypdf()

        # Method 3: PyMuPDF
        if PYMUPDF_AVAILABLE:
            results['pymupdf'] = self.extract_with_pymupdf()

        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        for method, result in results.items():
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"\n{method.upper()}: {status}")
            if result.success:
                print(f"   Entries: {result.total_entries}")
                print(f"   Max depth: {result.max_depth}")
            else:
                print(f"   Error: {result.error}")

        # Recommendation
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATION")
        print("=" * 60)

        successful_methods = [m for m, r in results.items() if r.success]
        if successful_methods:
            best_method = max(
                successful_methods,
                key=lambda m: results[m].total_entries
            )
            print(f"✅ Best method: {best_method.upper()}")
            print(f"   Reason: Most entries ({results[best_method].total_entries})")
        else:
            print("⚠️  No method successfully extracted ToC")
            print("   PDF may not have embedded ToC/outline")
            print("   Consider fallback: heading detection based on font size/style")

        return results

    def save_results(self, results: Dict[str, TocExtractionResult], output_file: str):
        """Save results to JSON file"""
        output_path = Path(output_file)

        json_results = {
            'pdf_path': str(self.pdf_path),
            'pdf_name': self.pdf_path.name,
            'methods': {
                method: result.to_dict()
                for method, result in results.items()
            }
        }

        output_path.write_text(json.dumps(json_results, indent=2, ensure_ascii=False))
        print(f"\n💾 Results saved to: {output_path}")


def main():
    """Main research script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Research ToC extraction methods from PDF"
    )
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to PDF file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='toc_research_results.json',
        help='Output JSON file for results (default: toc_research_results.json)'
    )

    args = parser.parse_args()

    try:
        extractor = TocExtractor(args.pdf_path)
        results = extractor.run_all_methods()
        extractor.save_results(results, args.output)

        print("\n✅ Research complete!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

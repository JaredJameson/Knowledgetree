# Test Coverage Gap Analysis
**Data**: 2026-01-24
**Status**: Analiza brakujących testów

## 📊 Podsumowanie Pokrycia Testami

### Istniejące Testy ✅

| Moduł | Testy | Status | Pliki |
|-------|-------|--------|-------|
| **Projects API** | ✅ Kompletne | 100% | `tests/api/test_projects_integration.py` |
| **Categories API** | ✅ Kompletne | 100% | `tests/api/test_categories.py`, `test_categories_integration.py` |
| **Workflows** | ✅ Kompletne | 90% | `tests/workflow_tests/test_*.py` |
| **Services** | ⚠️ Częściowe | 30% | `tests/services/test_toc_extractor.py`, `test_category_tree_generator.py` |

### Brakujące Testy ❌

| Moduł | Priorytet | Endpointy | Status |
|-------|-----------|-----------|--------|
| **Auth API** | 🔴 CRITICAL | 5 endpoints | ❌ BRAK |
| **Documents API** | 🔴 CRITICAL | 7 endpoints | ❌ BRAK |
| **Search API** | 🔴 CRITICAL | 5 endpoints | ❌ BRAK |
| **Chat API** | 🔴 CRITICAL | 8 endpoints | ❌ BRAK |
| **Insights API** | 🟡 HIGH | 4 endpoints | ❌ BRAK |
| **Export API** | 🟡 HIGH | 3 endpoints | ❌ BRAK |
| **Crawl API** | 🟢 MEDIUM | 5 endpoints | ❌ BRAK |
| **Artifacts API** | 🟢 MEDIUM | 4 endpoints | ❌ BRAK |
| **Usage API** | 🟢 LOW | 2 endpoints | ❌ BRAK |
| **Subscriptions API** | 🟢 LOW | 5 endpoints | ❌ BRAK |
| **API Keys API** | 🟢 LOW | 5 endpoints | ❌ BRAK |
| **YouTube API** | 🟢 LOW | 3 endpoints | ❌ BRAK |

---

## 🔴 CRITICAL Priority - Testy do Utworzenia Najpierw

### 1. Auth API Tests
**Plik**: `tests/api/test_auth.py`

**Endpointy do przetestowania**:
- `POST /auth/register` - Rejestracja użytkownika
- `POST /auth/login` - Logowanie (JSON)
- `POST /auth/token` - Logowanie (OAuth2 form)
- `POST /auth/refresh` - Odświeżanie tokenu
- `GET /auth/me` - Informacje o zalogowanym użytkowniku

**Scenariusze testowe**:
- ✅ Successful registration
- ✅ Registration with existing email (409 conflict)
- ✅ Registration with invalid email format (422)
- ✅ Login with valid credentials
- ✅ Login with invalid credentials (401)
- ✅ Login with non-existent user (401)
- ✅ Token refresh with valid token
- ✅ Token refresh with expired token (401)
- ✅ Get current user info with valid token
- ✅ Get current user info without token (401)
- ✅ Password validation (min length, special chars)

**Oszacowanie**: ~200 linii kodu, 1-2 godziny

---

### 2. Documents API Tests
**Plik**: `tests/api/test_documents.py`

**Endpointy do przetestowania**:
- `POST /documents/upload` - Upload PDF
- `GET /documents/` - Lista dokumentów
- `GET /documents/{id}` - Pojedynczy dokument
- `PATCH /documents/{id}` - Aktualizacja dokumentu
- `DELETE /documents/{id}` - Usunięcie dokumentu
- `POST /documents/{id}/process` - Przetwarzanie dokumentu (vectorization)
- `POST /documents/{id}/generate-categories` - Generowanie kategorii z TOC

**Scenariusze testowe**:
- ✅ Upload valid PDF file
- ✅ Upload non-PDF file (415 unsupported media type)
- ✅ Upload file too large (413 payload too large)
- ✅ Upload without authentication (401)
- ✅ List documents with pagination
- ✅ List documents filtered by project
- ✅ Get document by ID
- ✅ Get document from another user's project (404)
- ✅ Update document metadata (title, category)
- ✅ Delete document and verify cascade deletion
- ✅ Process document (mock embedding generation)
- ✅ Generate categories from TOC
- ✅ Upload with project not owned by user (404)

**Oszacowanie**: ~400 linii kodu, 3-4 godziny

**Dodatkowe wymagania**:
- Mock dla `pdf_processor.process_pdf()`
- Mock dla `embedding_generator.generate_embeddings()`
- Test PDF fixture file

---

### 3. Search API Tests
**Plik**: `tests/api/test_search.py`

**Endpointy do przetestowania**:
- `POST /search/` - Vector search
- `POST /search/sparse` - BM25 sparse search
- `POST /search/hybrid` - Hybrid search (vector + BM25)
- `POST /search/rerank` - Search with cross-encoder reranking
- `GET /search/stats` - Search statistics

**Scenariusze testowe**:
- ✅ Vector search with valid query
- ✅ Vector search with empty query (422)
- ✅ Vector search with filters (project_id, category_id)
- ✅ Vector search pagination (top_k parameter)
- ✅ Sparse search (BM25) with valid query
- ✅ Hybrid search combining vector + sparse
- ✅ Reranking search with cross-encoder
- ✅ Search without authentication (401)
- ✅ Search in project not owned by user (404)
- ✅ Search statistics retrieval
- ✅ Search with min_score threshold
- ✅ Empty results handling

**Oszacowanie**: ~300 linii kodu, 2-3 godziny

**Dodatkowe wymagania**:
- Test document chunks with embeddings
- Mock dla BM25 service
- Mock dla cross-encoder service

---

### 4. Chat API Tests
**Plik**: `tests/api/test_chat.py`

**Endpointy do przetestowania**:
- `POST /chat/` - Chat with RAG (non-streaming)
- `POST /chat/stream` - Streaming chat
- `GET /chat/conversations` - Lista konwersacji
- `GET /chat/conversations/{id}` - Pojedyncza konwersacja
- `PATCH /chat/conversations/{id}` - Aktualizacja konwersacji
- `DELETE /chat/conversations/{id}` - Usunięcie konwersacji
- `POST /chat/categories/generate` - Generowanie kategorii z contentu
- `POST /chat/agent` - Agent mode with web search

**Scenariusze testowe**:
- ✅ Chat with valid question and context
- ✅ Chat without context (no RAG)
- ✅ Chat with project_id filter
- ✅ Chat with invalid project_id (404)
- ✅ Streaming chat endpoint
- ✅ List conversations for user
- ✅ Get single conversation
- ✅ Get conversation from another user (404)
- ✅ Update conversation title
- ✅ Delete conversation
- ✅ Generate categories from content
- ✅ Agent mode with web search (mock)
- ✅ Chat without authentication (401)
- ✅ Empty question handling (422)

**Oszacowanie**: ~350 linii kodu, 3-4 godziny

**Dodatkowe wymagania**:
- Mock dla Anthropic API (Claude)
- Mock dla RAG service
- Mock dla web crawler
- Test conversation fixtures

---

## 🟡 HIGH Priority - Testy Drugorzędne

### 5. Insights API Tests
**Plik**: `tests/api/test_insights.py`

**Endpointy**:
- `GET /insights/availability` - Sprawdzenie dostępności
- `POST /insights/document/{id}` - Wnioski dla dokumentu
- `POST /insights/project` - Wnioski dla projektu
- `GET /insights/project/recent` - Ostatnie wnioski

**Oszacowanie**: ~250 linii kodu, 2 godziny

---

### 6. Export API Tests
**Plik**: `tests/api/test_export.py`

**Endpointy**:
- `POST /export/markdown` - Export do Markdown
- `POST /export/pdf` - Export do PDF
- `GET /export/status/{job_id}` - Status zadania exportu

**Oszacowanie**: ~200 linii kodu, 2 godziny

---

## 🟢 MEDIUM/LOW Priority - Testy Opcjonalne

### 7. Crawl API Tests
**Oszacowanie**: ~200 linii kodu, 2 godziny

### 8. Artifacts API Tests
**Oszacowanie**: ~150 linii kodu, 1-2 godziny

### 9. Pozostałe API Tests
- Usage API
- Subscriptions API
- API Keys API
- YouTube API

**Oszacowanie łącznie**: ~400 linii kodu, 3-4 godziny

---

## 🧪 Testy Serwisów (Unit Tests)

### Istniejące ✅
- `test_toc_extractor.py` - TOC extraction z PDF
- `test_category_tree_generator.py` - Generowanie drzewa kategorii

### Brakujące ❌

**Krytyczne serwisy do przetestowania**:

1. **RAG Service** (`services/rag_service.py`)
   - Retrieval z dokumentów
   - Context building
   - Query processing

2. **Embedding Generator** (`services/embedding_generator.py`)
   - BGE-M3 embedding generation
   - Batch processing
   - Error handling

3. **PDF Processor** (`services/pdf_processor.py`)
   - PDF extraction (PyMuPDF, docling, pdfplumber)
   - Fallback chain
   - Metadata extraction

4. **BM25 Service** (`services/bm25_service.py`)
   - Index building
   - Sparse retrieval
   - Ranking

5. **Cross-Encoder Service** (`services/cross_encoder_service.py`)
   - Reranking
   - Score calculation

6. **Search Service** (`services/search_service.py`)
   - Vector search
   - Hybrid search
   - Filtering

**Oszacowanie**: ~1000 linii kodu, 8-10 godzin

---

## 🎯 Testy E2E (End-to-End)

**Plik**: `tests/e2e/test_full_workflow.py`

### Scenariusze E2E do przetestowania:

1. **Complete RAG Workflow**
   ```
   Register → Login → Create Project → Upload PDF →
   Process Document (vectorize) → Search → Chat with RAG →
   Export results
   ```

2. **Category Management Workflow**
   ```
   Create Project → Upload PDF → Generate Categories from TOC →
   Create Manual Category → Assign Documents → Search by Category
   ```

3. **AI Insights Workflow**
   ```
   Create Project → Upload Multiple PDFs →
   Generate Document Insights → Generate Project Insights
   ```

4. **Web Crawling Workflow**
   ```
   Create Project → Crawl URL → Extract Content →
   Vectorize → Chat with web content
   ```

5. **Multi-User Access Control**
   ```
   User A creates project → User B tries to access → 404
   User A shares project → User B can access
   ```

**Oszacowanie**: ~600 linii kodu, 5-6 godzin

---

## 📊 Podsumowanie Czasu i Nakładu Pracy

### Faza 1: CRITICAL Tests (Must Have)
| Moduł | Linie | Czas |
|-------|-------|------|
| Auth API | 200 | 1-2h |
| Documents API | 400 | 3-4h |
| Search API | 300 | 2-3h |
| Chat API | 350 | 3-4h |
| **TOTAL** | **1250** | **9-13h** |

### Faza 2: HIGH Priority Tests (Should Have)
| Moduł | Linie | Czas |
|-------|-------|------|
| Insights API | 250 | 2h |
| Export API | 200 | 2h |
| **TOTAL** | **450** | **4h** |

### Faza 3: Service Unit Tests
| Moduł | Linie | Czas |
|-------|-------|------|
| RAG Service | 200 | 2h |
| Embedding Generator | 150 | 1-2h |
| PDF Processor | 200 | 2h |
| BM25 Service | 150 | 1-2h |
| Cross-Encoder | 150 | 1-2h |
| Search Service | 150 | 1-2h |
| **TOTAL** | **1000** | **8-10h** |

### Faza 4: E2E Tests
| Scenariusz | Linie | Czas |
|------------|-------|------|
| Complete RAG Workflow | 150 | 1-2h |
| Category Management | 100 | 1h |
| AI Insights | 100 | 1h |
| Web Crawling | 100 | 1h |
| Access Control | 150 | 1-2h |
| **TOTAL** | **600** | **5-6h** |

---

## 🎯 Rekomendowany Plan Działania

### PRIORYTET 1: CRITICAL API Tests (dzisiaj)
1. ✅ **Auth API** - Najpierw, bo wszystkie inne zależą od auth
2. ✅ **Documents API** - Kluczowa funkcjonalność upload & processing
3. ✅ **Search API** - Podstawa RAG
4. ✅ **Chat API** - Main user-facing feature

**Czas**: 9-13 godzin
**Rezultat**: Pokrycie krytycznych endpointów testami

### PRIORYTET 2: HIGH Priority Tests (jutro)
5. ✅ **Insights API**
6. ✅ **Export API**

**Czas**: 4 godziny
**Rezultat**: Wszystkie główne funkcje przetestowane

### PRIORYTET 3: Unit Tests (2-3 dni)
7. ✅ RAG Service
8. ✅ Embedding Generator
9. ✅ PDF Processor
10. ✅ Search-related services

**Czas**: 8-10 godzin
**Rezultat**: Pokrycie logiki biznesowej

### PRIORYTET 4: E2E Tests (3-4 dni)
11. ✅ Complete workflow tests

**Czas**: 5-6 godzin
**Rezultat**: Confidence w całym systemie

---

## 🎯 Cel Coverage

**Target Coverage**:
- **API Endpoints**: 90%+ (wszystkie CRITICAL + HIGH)
- **Services**: 70%+ (kluczowe serwisy RAG)
- **Models**: 60%+ (podstawowe operacje CRUD)
- **Overall**: 75%+

**Tools**:
```bash
# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Coverage threshold enforcement
pytest --cov=. --cov-fail-under=75
```

---

## 📝 Notatki Implementacyjne

### Test Fixtures Needed

**Nowe fixtures do utworzenia** (w `conftest.py`):

```python
@pytest.fixture
async def test_document(db_session, test_project):
    """Test document with chunks and embeddings"""

@pytest.fixture
async def test_pdf_file():
    """Mock PDF file for upload tests"""

@pytest.fixture
async def mock_anthropic_response():
    """Mock Claude API response"""

@pytest.fixture
async def mock_embeddings():
    """Mock BGE-M3 embeddings (1024 dimensions)"""

@pytest.fixture
async def test_conversation(db_session, test_user, test_project):
    """Test conversation with messages"""
```

### Mocking Strategy

**Zewnętrzne serwisy do mockowania**:
- Anthropic API (Claude) - `unittest.mock.patch`
- Embedding models (BGE-M3) - Mock numpy arrays
- PDF processing - Mock extracted text
- Web crawling - Mock HTTP responses
- File system operations - Mock file writes

### Continuous Integration

**GitHub Actions** (`.github/workflows/tests.yml`):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=. --cov-fail-under=75
```

---

**Status**: Gap analysis kompletna
**Next Step**: Rozpocząć implementację testów od Auth API

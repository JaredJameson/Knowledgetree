# Crawling Agentowy z Inteligentnym Wyborem Silnika

## Przegląd

**Agentic Crawl** to zaawansowana funkcja KnowledgeTree, która pozwala na automatyczne pobieranie i ekstrakcję informacji ze stron internetowych z wykorzystaniem sztucznej inteligencji. System automatycznie wybiera optymalny silnik crawlingu na podstawie analizy URLi i zadania.

## 🎯 Kluczowe Funkcjonalności

### 1. **Inteligentny Wybór Silnika**

System automatycznie wybiera najbardziej odpowiedni silnik crawlingu:

- **HTTP Scraper** (80% przypadków)
  - Najszybszy silnik
  - Ideally dla statycznych stron HTML
  - Blogs, dokumentacja, Wikipedia, prosty e-commerce

- **Playwright** (15% przypadków)
  - Renderowanie JavaScript w rzeczywistej przeglądarce
  - Social media, SPA (Single Page Applications)
  - Strony z dynamiczną treścią

- **Firecrawl** (5% przypadków - opcjonalny)
  - Premium API dla trudnych stron
  - Anti-bot protection, heavy JavaScript
  - Wymaga klucza API (opcjonalny)

### 2. **Ekstrakcja Kierowana Promptem**

Użytkownik podaje naturalny prompt w języku polskim lub angielskim, a AI ekstrauje dokładnie te informacje, których potrzeba.

**Przykładowe Prompty:**
```
"wyciągnij wszystkie firmy z nazwą, adresem i danymi kontaktowymi"

"znajdź wszystkie informacje o metodykach konserwacji drewna"

"wejdź na film YouTube, wyciągnij transkrypcję i zbuduj artykuł"

"zbierz wszystkie produkty z cenami i opisami"
```

### 3. **Obsługa Wielu URLi**

- Jednorazowe przetwarzanie do 20 URLi
- Automatyczne łączenie wyników w hierarchiczne drzewo kategorii
- Równoległe przetwarzanie dla lepszej wydajności

## 🚀 Jak Używać

### Przez Interfejs Webowy

1. **Przejdź do sekcji Dokumenty**
2. **Wybierz projekt**
3. **Kliknij "Crawling Agentowy" z ikoną AI**
4. **Dodaj URLe**:
   - Wpisz jeden lub więcej URLi (max 20)
   - Możesz dodawać kolejne URLe przyciskiem "Dodaj URL"
   - Usuń niepotrzebne URLe klikając (X)

5. **Napisz Prompt AI**:
   - Opisz co chcesz wyekstrahować (min. 10 znaków)
   - Używaj języka naturalnego (polski lub angielski)
   - Bądź konkretny - lepsze prompty = lepsze wyniki

6. **Rozpocznij Crawling**:
   - System automatycznie wybierze optymalny silnik
   - Przetwarzanie odbywa się w tle (Celery)
   - Otrzymasz Job ID do śledzenia postępu

### Przez API

```bash
curl -X POST "http://localhost:8765/api/v1/crawl/agentic" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/company-list",
      "https://example.com/company-details"
    ],
    "agent_prompt": "wyciągnij wszystkie firmy z nazwą, adresem, danymi kontaktowymi i stroną internetową"
  }'
```

**Odpowiedź:**
```json
{
  "success": true,
  "job_id": 42,
  "message": "Agentic extraction started for 2 URLs with custom prompt",
  "agent_prompt": "wyciągnij wszystkie firmy...",
  "urls_count": 2,
  "note": "AI agents will extract structured information according to your prompt"
}
```

## 🔧 Architektura Techniczna

### Backend (Python/FastAPI)

#### 1. **Endpoint API** (`backend/api/routes/crawl.py`)
```python
@router.post("/agentic")
async def crawl_with_agent_prompt(
    request: AgenticCrawlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agentic Crawl with intelligent engine selection
    - Analyzes URLs and prompt
    - Automatically selects optimal engine
    - Creates CrawlJob and launches Celery task
    """
```

#### 2. **Celery Task** (`backend/services/document_tasks.py`)
```python
@celery_app.task(name="services.document_tasks.process_agentic_crawl_task")
def process_agentic_crawl_task(
    self,
    crawl_job_id: int,
    urls: List[str],
    agent_prompt: str,
    project_id: int,
    engine: Optional[str] = None,
    category_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Background task processing:
    1. Intelligent engine selection
    2. URL scraping
    3. AI-guided extraction
    4. Knowledge tree generation
    5. Document + chunks persistence
    """
```

#### 3. **Intelligent Engine Selector** (`backend/services/intelligent_crawler_selector.py`)
```python
class IntelligentCrawlerSelector:
    """
    Analyzes URLs and task prompt to automatically select
    optimal scraping engine (HTTP, Playwright, or Firecrawl)

    Decision factors:
    - URL patterns (domain, path, extensions)
    - Content type predictions
    - Prompt analysis (complexity, requirements)
    - Historical success rates
    """

    def select_engine(
        self,
        urls: List[str],
        prompt: str
    ) -> CrawlEngine:
        """Returns optimal engine with confidence score"""
```

### Frontend (React/TypeScript)

#### **AgenticCrawlDialog Component** (`frontend/src/components/AgenticCrawlDialog.tsx`)
```typescript
interface AgenticCrawlDialogProps {
  projectId: number;
  onSuccess?: (jobId: number) => void;
}

export function AgenticCrawlDialog({ projectId, onSuccess }: AgenticCrawlDialogProps) {
  // State management for URLs, prompt, loading
  // Form validation
  // API call to /crawl/agentic
  // Success feedback with Job ID
}
```

## 📊 Przepływ Danych

```
┌─────────────────┐
│   User Input    │
│  URLs + Prompt  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Intelligent Engine Selector            │
│  - Analyze URLs (patterns, domains)     │
│  - Parse prompt (complexity, keywords)  │
│  - Confidence scoring                   │
│  - Engine recommendation                │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Selected Engine│
│  HTTP/Playwright│
│  /Firecrawl     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Content Scraping       │
│  - Multiple URLs        │
│  - Parallel processing  │
│  - Error handling       │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│  AI-Guided Extraction    │
│  - Claude/OpenAI API     │
│  - Custom prompt         │
│  - Structured output     │
└────────┬─────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Knowledge Organization        │
│  - Hierarchical categories     │
│  - Document creation           │
│  - Chunk generation            │
│  - Vector embeddings           │
└────────┬───────────────────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL DB  │
│  + pgvector     │
└─────────────────┘
```

## 🎓 Przykłady Użycia

### Przykład 1: Ekstrakcja Firm z Katalogu

**URLs:**
```
https://firmy.example.com/listing/page-1
https://firmy.example.com/listing/page-2
https://firmy.example.com/listing/page-3
```

**Prompt:**
```
Wyciągnij wszystkie firmy z następującymi danymi:
- Nazwa firmy
- Adres (ulica, miasto, kod pocztowy)
- Telefon kontaktowy
- Email
- Strona internetowa
- Opis działalności

Zignoruj reklamy i nawigację.
```

**Wynik:**
- System użyje **HTTP scraper** (szybki, statyczne listy)
- AI wyekstrauje strukturalne dane zgodnie z promptem
- Powstanie dokument z hierarchicznym drzewem kategorii

### Przykład 2: Analiza Konkurencji z SPA

**URLs:**
```
https://competitor-spa.com/products
https://competitor-spa.com/pricing
```

**Prompt:**
```
Zbierz informacje o:
- Wszystkie produkty z cenami i opisami
- Plany cenowe i ich funkcjonalności
- Unikalne punkty sprzedaży (USP)

Porównaj ceny i funkcje.
```

**Wynik:**
- System użyje **Playwright** (JavaScript-heavy SPA)
- Renderowanie w prawdziwej przeglądarce
- Kompletna ekstrakcja dynamicznej treści

### Przykład 3: Transkrypcja YouTube

**URLs:**
```
https://youtube.com/watch?v=XYZ123
https://youtube.com/watch?v=ABC456
```

**Prompt:**
```
Wyciągnij transkrypcję filmów i stwórz artykuł podsumowujący:
- Główne punkty i wnioski
- Kluczowe cytaty
- Praktyczne wskazówki

Struktura: wstęp, główne tematy, podsumowanie.
```

**Wynik:**
- System rozpozna YouTube URLs
- YouTube transcriber API
- AI summary według promptu

## ⚙️ Konfiguracja

### Zmienne Środowiskowe

```bash
# Backend (.env)
ANTHROPIC_API_KEY=sk-ant-xxx  # Claude API (rekomendowane dla AI extraction)
OPENAI_API_KEY=sk-xxx         # OpenAI gpt-4o-mini (primary LLM)
FIRECRAWL_API_KEY=fc-xxx      # Opcjonalny, premium scraping
```

### Limity i Ustawienia

```python
# backend/api/routes/crawl.py
MAX_URLS_AGENTIC_CRAWL = 20        # Max URLs per request
PROMPT_MIN_LENGTH = 10              # Min prompt characters
PROMPT_MAX_LENGTH = 1000            # Max prompt characters
CELERY_TASK_PRIORITY = 7            # Higher priority for agentic tasks
```

## 🔍 Monitorowanie i Debugowanie

### Sprawdzanie Statusu Zadania

```bash
curl -X GET "http://localhost:8765/api/v1/crawl/jobs/42" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Odpowiedź:**
```json
{
  "job_id": 42,
  "project_id": 1,
  "status": "in_progress",
  "total_urls": 3,
  "completed_urls": 2,
  "failed_urls": 0,
  "created_at": "2026-01-29T12:00:00Z",
  "updated_at": "2026-01-29T12:05:00Z"
}
```

### Logi Celery Worker

```bash
# Sprawdzenie wyboru silnika i przetwarzania
docker logs knowledgetree-celery-worker -f | grep -E "crawl|engine|agentic"
```

**Przykładowe Logi:**
```
[2026-01-29 12:05:00] INFO: Auto-selected engine: http
[2026-01-29 12:05:00] INFO: Intelligent selection for: wyciągnij wszystkie firmy...
[2026-01-29 12:05:01] INFO: Scraping 3 URLs with engine=http
[2026-01-29 12:05:03] INFO: Scraping complete: 3 succeeded, 0 failed
[2026-01-29 12:05:03] INFO: Extracting with custom prompt: wyciągnij wszystkie...
```

## 🚨 Obsługa Błędów

### Typowe Błędy i Rozwiązania

**1. "Engine selection failed"**
- Sprawdź dostępność Playwright lub Firecrawl
- Fallback na HTTP scraper automatyczny

**2. "AI extraction failed"**
- Sprawdź ANTHROPIC_API_KEY / OPENAI_API_KEY
- Prompt może być zbyt skomplikowany - uprość

**3. "URL scraping timeout"**
- Zwiększ timeout w ustawieniach
- Niektóre strony mogą blokować boty

**4. "Event loop error" (fixed w v1.1)**
- Update do najnowszej wersji
- Fix: używamy `asyncio.run()` zamiast `new_event_loop()`

## 📈 Wydajność

### Benchmarki

| Scenariusz | URLs | Czas | Silnik |
|------------|------|------|--------|
| Proste listy HTML | 10 | ~15s | HTTP |
| SPA z JS | 5 | ~45s | Playwright |
| YouTube | 3 | ~30s | YouTube API |
| Mix stron | 20 | ~2min | Auto |

### Optymalizacja

- **Równoległe przetwarzanie**: Do 5 URLs jednocześnie
- **Caching**: Ponowne zapytania wykorzystują cache
- **Inteligentny fallback**: Automatyczne przełączanie silników przy błędach

## 🔐 Bezpieczeństwo

- **Autentykacja**: Bearer token wymagany
- **Rate limiting**: Zapobieganie nadużyciom
- **URL validation**: Walidacja formatów i domen
- **Sandbox execution**: Izolowane środowisko crawlingu

## 📝 Changelog

### v1.1.0 (2026-01-29)
- ✨ Dodano inteligentny wybór silnika
- ✨ Agentic crawl z custom AI prompts
- 🐛 Fix: Event loop error w Celery tasks
- 📚 Dokumentacja w języku polskim

### v1.0.0 (2026-01-20)
- 🎉 Podstawowy crawling HTTP/Playwright
- 🎉 Single URL i batch crawling

## 🤝 Wsparcie

- **GitHub Issues**: https://github.com/yourusername/knowledgetree/issues
- **Dokumentacja API**: http://localhost:8765/docs
- **Email**: support@knowledgetree.com

---

**Stworzone z ❤️ dla KnowledgeTree**

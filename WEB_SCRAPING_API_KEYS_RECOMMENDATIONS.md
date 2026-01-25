# KnowledgeTree - Web Scraping & API Keys Rekomendacje
**Data:** 2026-01-23
**Status:** REKOMENDACJE IMPLEMENTACJI

---

## 📋 Wymagane Klucze API

### 🔴 KLUCZOWE (niezbędne do pełnej funkcjonalności)

| API Key | Cel | Priorytet | Koszt | Source |
|---------|-----|-----------|-------|--------|
| **ANTHROPIC_API_KEY** | Claude AI (RAG chat) | WYSOKI | $3-15/1M tokens | https://console.anthropic.com/ |
| **OPENAI_API_KEY** | GPT-4o-mini (alt model) | WYSOKI | $0.15-1/1M tokens | https://platform.openai.com/ |
| **FIRECRAWL_API_KEY** | Web scraping (AI-native) | WYSOKI | $49-249/miesiąc | https://www.firecrawl.dev/ |

### 🟡 WARTO MIEĆ (ulepszają funkcjonalność)

| API Key | Cel | Priorytet | Koszt | Source |
|---------|-----|-----------|-------|--------|
| **SERPER_API_KEY** | Google Search API | ŚREDNI | $2.5/1000 searches | https://serper.dev/ |
| **GOOGLE_CSE_API_KEY** | Google Custom Search | ŚREDNI | $5/1000 queries | https://programmablesearchengine.google.com/ |

### 🟢 OPCJONALNE (dodatkowe features)

| API Key | Cel | Priorytet | Koszt | Source |
|---------|-----|-----------|-------|--------|
| **STRIPE_API_KEY** | Payments production | NISKI | zależy od obrotu | https://stripe.com/ |
| **SENDGRID_API_KEY** | Email sending (production) | NISKI | darmowy tier | https://sendgrid.com/ |

---

## 🕷️ Web Scraping - Rekomendowany Stack

### OPÇÃO 1: Firecrawl (REKOMENDOWANE dla RAG) ✅

**Dlaczego Firecrawl?**
- 🤖 **AI-Native**: Zaprojektowany specjalnie dla aplikacji RAG/AI
- 📄 **Markdown Output**: Automatycznie konwertuje HTML na czytelny markdown
- 🌐 **JavaScript Support**: Obsługuje SPA, React, Vue, dynamic content
- 🎯 **Clean Extraction**: Usuwa navbars, footers, ads - zostawia tylko content
- 📦 **Batch Processing**: Crawling całych stron z jednego API call
- 🔒 **Reliable**: Proxy rotation, CAPTCHA handling, rate limiting

**Cennik:**
```
FREE TIER (perfect dla start):
- 500 credits/miesiąc (darmowe)
- 1 credit = 1 scrape
- Idealne do testów i development

HOBBY ($49/miesiąc):
- 5,000 credits
- ~$0.01 per scrape
- Adequate dla small business

STARTUP ($149/miesiąc):
- 30,000 credits
- ~$0.005 per scrape
- Good dla growing apps

ENTERPRISE ($249+/miesiąc):
- Unlimited
- Priority support
- Custom rate limits
```

**Integracja:**
```bash
# .env
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxx
ENABLE_WEB_CRAWLING=true
```

**Kod już istnieje:**
- ✅ `backend/services/firecrawl_scraper.py` - zaimplementowany
- ✅ `backend/api/routes/crawl.py` - endpoint ready
- ✅ `backend/services/crawler_orchestrator.py` - orchestrator gotowy

**Należy dodać:**
- Frontend UI dla web crawling (może być osobna strona `/crawl`)
- Integracja z projects (crawl → save documents → generate chunks)

---

### OPÇÃO 2: Open-Source Stack (dla budżetowych)

**Crawl4AI + Playwright (FREE)**

**Dlaczego Crawl4AI?**
- 💰 **Darmowy**: Open-source, bez opłat
- 🎯 **AI-Optimized**: Specjalnie dla RAG/LLM apps
- 🔧 **Full Control**: Pełna kontrola nad procesem
- 📦 **Self-Hosted**: Żadnych zależności zewnętrznych

**Cena:** $0 (tylko serwer)

**Wady:**
- ❌ Wymaga utrzymania własnego serwera
- ❌ Trzeba obsłużyć proxy rotation
- ❌ CAPTCHA solving samodzielnie

**Alternatywa:**
- **Browserless.io** ($49/miesiąc) - managed Puppeteer/Playwright
- **Scrapfly** ($49/miesiąc) - proxy + anti-bot

---

### OPÇÃO 3: Enterprise Scraping (dla dużych projektów)

**Apify + Oxylabs**

**Apify:**
- 🏪 **Store**: Gotowe scrapers (Amazon, Google Maps, Instagram, itd.)
- 🔧 **Custom**: Możliwość budowy własnych crawlerów
- 📊 **Monitoring**: Built-in dashboard i logging
- 💰 **Cena**: $49-499/miesiąc

**Oxylabs:**
- 🌐 **Residential Proxies**: 100M+ IPs
- 🤖 **AI-powered**: Auto-bypass anti-bot
- 💰 **Cena**: $300+/miesiąc (enterprise)

---

## 🎯 Moja Rekomendacja

### DLA TWOJEGO PROJEKTU: **Firecrawl Hobby Plan** ($49/miesiąc)

**Argumenty:**
1. ✅ **Kod już gotowy** - wystarczy API key
2. ✅ **Idealne dla RAG** - markdown output, clean content
3. ✅ **Obsługuje JS** - React/Vue/Angular sites
4. ✅ **Zero maintenance** - nie musisz zarządzać proxy/captcha
5. ✅ **Skalowalne** - łatwy upgrade do wyższego planu
6. ✅ **Reliable** - 99.9% uptime SLA

**Alternatywa Budget:**
- **Firecrawl Free Tier** (500 scrapów/miesiąc) - do testów
- **Crawl4AI** (self-hosted) - $0 ale wymaga pracy

---

## 📝 Lista Danych Od Ciebie

### 1. KLUCZE API DO ZAKUPIENIA:

**Minimalne (dla startu):**
```
✅ ANTHROPIC_API_KEY - masz już
✅ OPENAI_API_KEY - masz już
❌ FIRECRAWL_API_KEY - DO ZAKUPIENIA ($49-149/miesiąc)
```

**Dodatkowe (opcjonalnie):**
```
❌ SERPER_API_KEY - DO ZAKUPIENIA ($2.5/1000 searches)
❌ STRIPE_API_KEY - tylko dla produkcji (płatności)
❌ SENDGRID_API_KEY - tylko dla produkcji (email)
```

### 2. INNE DANE:

```
✅ SMTP settings - masz już ( Gmail SMTP )
❌ Stripe account - tylko dla produkcji
❌ VPS hosting - tylko dla produkcji (DigitalOcean, Hetzner, itd.)
```

---

## 🚀 Plan Implementacji Web Scraping

### ETAP 1: Konfiguracja (5 minut)

1. **Zarejestruj się na Firecrawl:**
   - https://www.firecrawl.dev/
   - Zdobądź API key
   - Wybierz plan (Hobby = $49/miesiąc)

2. **Dodaj do .env:**
   ```bash
   FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxx
   ENABLE_WEB_CRAWLING=true
   ```

3. **Restart Docker:**
   ```bash
   docker-compose restart backend
   ```

### ETAP 2: Testy (10 minut)

```bash
# Test endpoint
curl -X POST "http://localhost:8765/api/v1/crawl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "project_id": 1
  }'
```

### ETAP 3: Frontend UI (2-3 godziny)

**Strona `/crawl` z:**
- Input na URL (lub listę URLs)
- Project selector
- "Crawl Now" button
- Progress tracking
- Results preview (markdown)
- "Save to Project" button

### ETAP 4: Integracja z Projects (1 godzina)

- Crawl → Create Document → Auto-chunking → Embedding
- Categories generation z crawled content
- Search w crawled documents

---

## 💰 Szacunkowe Koszty Miesięczne

### Development (DEMO_MODE):
```
$0 - wszystko darmowe (DEMO_MODE)
```

### Production (mały deployment):
```
ANTHROPIC_API_KEY:   $15-50/miesiąc (zależy od użycia)
OPENAI_API_KEY:      $5-20/miesiąc (zależy od użycia)
FIRECRAWL_API_KEY:   $49/miesiąc (Hobby plan)
VPS (Hetzner/DG):    $10-20/miesiąc (CX22/CPU4)
-------------------------------------------
TOTAL:               ~$80-140/miesiąc
```

### Production (duży deployment):
```
ANTHROPIC_API_KEY:   $100-500/miesiąc
OPENAI_API_KEY:      $50-200/miesiąc
FIRECRAWL_API_KEY:   $149/miesiąc (Startup plan)
SERPER_API_KEY:      $25-50/miesiąc
VPS:                 $40-80/miesiąc (CX31/CPU6)
PostgreSQL:          $15/miesiąc (managed)
-------------------------------------------
TOTAL:               ~$380-1000/miesiąc
```

---

## ✅ Checklist - Czego Potrzebujesz

### PILNE (dla demo):
- [ ] **Firecrawl API Key** ($49/miesiąc) - Web Scraping
- [ ] Test web crawling endpoint
- [ ] Stworzyć prosty frontend UI dla crawl

### OPCIJONALNE (dla pełnej produkcji):
- [ ] **Serper API Key** ($2.5/1000) - Google Search
- [ ] **Stripe Account** - Płatności
- [ ] **SendGrid Account** - Email sending
- [ ] **VPS Hosting** - Deployment

### DARMOWE (ale warto):
- [ ] **GitHub** - Code hosting
- [ ] **Railway/Render** - Alternatywne deployment (free tier)

---

## 🎯 Następne Kroki

### 1. NATYCHMIAST (dziś):
- [ ] Zarejestruj się na Firecrawl
- [ ] Dodaj FIRECRAWL_API_KEY do .env
- [ ] Przetestuj backend endpoint

### 2. KRÓTKO TERMINOWO (tydzień):
- [ ] Stwórz `/crawl` frontend page
- [ ] Integracja z Projects
- [ ] Testy E2E

### 3. DŁUGO TERMINOWO (miesiąc):
- [ ] Pełna dokumentacja web crawling
- [ ] Monitoring i logging
- [ ] Rate limiting dla API

---

## 📚 Dodatkowe Zasoby

**Firecrawl Documentation:**
- https://docs.firecrawl.dev/
- https://github.com/mendableai/firecrawl

**Alternatives:**
- Crawl4AI: https://github.com/unclecode/crawl4ai
- Apify: https://docs.apify.com/
- Browserless: https://docs.browserless.io/

**Web Scraping Best Practices:**
- Respect robots.txt
- Rate limiting (1 req/sec)
- User-Agent rotation
- Proxy rotation
- CAPTCHA handling

---

## 🤝 Wnioski

**MASZ:**
- ✅ Kod backend gotowy (firecrawl_scraper.py)
- ✅ ANTHROPIC_API_KEY
- ✅ OPENAI_API_KEY

**BRAKUJE:**
- ❌ FIRECRAWL_API_KEY ($49-149/miesiąc)
- ❌ Frontend UI dla web crawling
- ❌ Integracja z projects (automatyczne zapisywanie)

**REKOMENDACJA:**
Zacznij od **Firecrawl Free Tier** (500 scrapów) do testów, potem upgrade do **Hobby** ($49/miesiąc) dla produkcji.

**CZAS IMPLEMENTACJI:**
- Backend: ✅ GOTOWY
- Frontend: 2-3 godziny
- Testy: 1 godzina
- **TOTAL: 1 dzień**

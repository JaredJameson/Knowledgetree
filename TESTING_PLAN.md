# KnowledgeTree - Plan Testowania Funkcji

## Cel: Walidacja wartości produktu przed monetyzacją

**Filozofia testowania:**
- Skupiamy się na tym CZY działa i JAK DOBRZE działa
- Nie testujemy limitów i płatności (to później)
- Budujemy bazy wiedzy na różne tematy i sprawdzamy jakość
- Szukamy co trzeba poprawić/rozwinąć

---

## Test 1: PDF Upload & Text Extraction ⏳

**Co testujemy:**
- Czy PDF jest poprawnie uploadowany
- Czy tekst jest dobrze ekstrahowany (PyMuPDF, docling, pdfplumber)
- Czy chunking zachowuje kontekst
- Czy embeddingi są generowane

**Test case:**
1. Upload prostego PDF (tekst + formatowanie)
2. Upload złożonego PDF (tabele, formuły, obrazy)
3. Upload dużego PDF (100+ stron)

**Metryki sukcesu:**
- ✅ Wszystkie strony zeskanowane
- ✅ Tekst poprawnie wyekstrahowany (bez artefaktów)
- ✅ Chunki mają sensowny rozmiar (800-1200 znaków)
- ✅ Embeddingi wygenerowane dla wszystkich chunków

**Przykładowe pliki do testu:**
- Simple: Artykuł naukowy (10-20 stron)
- Complex: Raport finansowy z tabelami
- Large: Książka lub długi raport (100+ stron)

---

## Test 2: Automatic Categorization ⏳

**Co testujemy:**
- Czy auto-generowanie kategorii działa
- Czy kategorie są sensowne i pomocne
- Czy hierarchia kategorii jest logiczna
- Czy TOC extraction działa dla PDF z table of contents

**Test case:**
1. Upload PDF z jasną strukturą rozdziałów
2. Wygeneruj kategorie automatycznie
3. Sprawdź czy kategorie odpowiadają strukturze dokumentu

**Metryki sukcesu:**
- ✅ Kategorie są tematycznie spójne
- ✅ Hierarchia odzwierciedla strukturę dokumentu
- ✅ Można łatwo nawigować po kategoriach
- ✅ TOC jest poprawnie wyciągnięty z PDF

---

## Test 3: Vector Search Quality ⏳

**Co testujemy:**
- Czy wyszukiwanie semantyczne znajduje właściwe fragmenty
- Czy hybrid search (vector + BM25) działa lepiej niż samo vector
- Czy reranking poprawia wyniki
- Czy similarity scores są sensowne

**Test case:**
1. Zapytaj o konkretny fakt z dokumentu
2. Zapytaj o koncepcję wyrażoną innymi słowami
3. Zapytaj po polsku o treść w angielskim dokumencie (multilingual)

**Metryki sukcesu:**
- ✅ Top 3 wyniki zawierają odpowiedź
- ✅ Similarity score >0.7 dla dobrych wyników
- ✅ Hybrid search > pure vector search
- ✅ Cross-lingual search działa (BGE-M3)

---

## Test 4: RAG Chat Responses ⏳

**Co testujemy:**
- Czy chat odpowiada na podstawie dokumentów (nie halucynuje)
- Czy cytuje źródła
- Czy pamięta kontekst konwersacji
- Czy używa retrieved chunks do odpowiedzi

**Test case:**
1. Zadaj pytanie o fakt z dokumentu
2. Zadaj pytanie follow-up (context retention)
3. Zadaj pytanie o coś czego NIE MA w dokumentach (test halucynacji)

**Metryki sukcesu:**
- ✅ Odpowiedzi bazują na dokumentach (nie generic knowledge)
- ✅ Pokazuje źródła (retrieved chunks)
- ✅ Pamięta kontekst poprzednich wiadomości
- ✅ Mówi "nie wiem" gdy nie ma informacji w dokumentach

---

## Test 5: Artifact Generation (Charts, Summaries) ⏳

**Co testujemy:**
- Czy artifacts są generowane poprawnie
- Czy charts są czytelne i sensowne
- Czy summaries są zwięzłe i dokładne
- Czy timelines są chronologicznie poprawne

**Test case:**
1. Wygeneruj summary z długiego dokumentu
2. Wygeneruj chart z danych numerycznych
3. Wygeneruj timeline z dokumentu z datami

**Metryki sukcesu:**
- ✅ Artifacts są używalne i wartościowe
- ✅ Charts wizualizują dane poprawnie
- ✅ Summaries zachowują kluczowe informacje
- ✅ Timelines są chronologicznie spójne

**Komendy do testu:**
- `/summary` - podsumowanie dokumentu
- `/chart` - wykres z danych
- `/timeline` - oś czasu
- `/table` - tabela

---

## Test 6: Export Functions (JSON, MD, CSV) ⏳

**Co testujemy:**
- Czy export do różnych formatów działa
- Czy eksportowane dane są kompletne
- Czy formatowanie jest zachowane
- Czy można zaimportować z powrotem

**Test case:**
1. Export projektu do JSON
2. Export dokumentu do Markdown
3. Export search results do CSV

**Metryki sukcesu:**
- ✅ Wszystkie formaty exportują poprawnie
- ✅ Dane są kompletne (żadnych strat)
- ✅ Formatowanie zachowane w Markdown
- ✅ CSV jest czytelny w Excel/Sheets

---

## Test 7: Web Crawling & Scraping ⏳

**Co testujemy:**
- Czy crawler pobiera strony www
- Czy ekstrahuje czysty tekst (bez HTML)
- Czy radzi sobie z JavaScript (Playwright)
- Czy respektuje robots.txt

**Test case:**
1. Crawl prostej strony HTML
2. Crawl SPA z JavaScriptem
3. Crawl strony z wieloma podstronami (follow links)

**Metryki sukcesu:**
- ✅ Tekst jest czysty (bez tagów HTML)
- ✅ JavaScript content jest renderowany
- ✅ Links są followowane do określonej głębokości
- ✅ Respektuje robots.txt

**API Keys needed:**
- FIRECRAWL_API_KEY (optional, paid)
- SERPER_API_KEY (for search results crawling)

---

## Test 8: YouTube Transcriptions ⏳

**Co testujemy:**
- Czy transkrypcje są pobierane poprawnie
- Czy są searchable w RAG
- Czy timestampy są zachowane
- Czy działa dla różnych języków

**Test case:**
1. Dodaj YouTube video URL
2. Pobierz transkrypcję
3. Szukaj w transkrypcji
4. Chat o treści video

**Metryki sukcesu:**
- ✅ Transkrypcja pobrana poprawnie
- ✅ Searchable jak zwykły dokument
- ✅ Timestampy pozwalają wrócić do miejsca w video
- ✅ Działa dla PL i EN

---

## Test 9: AI Insights ⏳

**Co testujemy:**
- Czy insights są wartościowe
- Czy identyfikują kluczowe tematy
- Czy znajdują związki między dokumentami
- Czy sugestie są użyteczne

**Test case:**
1. Wygeneruj insights dla projektu z wieloma dokumentami
2. Sprawdź key topics
3. Sprawdź document relationships
4. Sprawdź recommendations

**Metryki sukcesu:**
- ✅ Insights są nietrywialne (nie oczywiste)
- ✅ Key topics są trafne
- ✅ Relationships mają sens
- ✅ Recommendations są użyteczne

---

## Test 10: Multi-project Isolation ⏳

**Co testujemy:**
- Czy projekty są izolowane od siebie
- Czy search nie przeskakuje między projektami
- Czy chat ma kontekst tylko z jednego projektu
- Czy usunięcie projektu nie wpływa na inne

**Test case:**
1. Stwórz 2 projekty z różnymi tematami
2. Upload dokumenty do obu
3. Search w projekcie A - czy znajduje tylko z A
4. Chat w projekcie B - czy używa tylko dokumentów z B

**Metryki sukcesu:**
- ✅ Search jest ograniczony do projektu
- ✅ Chat nie miesza kontekstów
- ✅ Delete projektu A nie wpływa na B
- ✅ Statystyki są per-project

---

## Kolejność testowania (rekomendowana):

### Faza 1: Core RAG Pipeline (najpierw!)
1. PDF Upload & Text Extraction
2. Vector Search Quality
3. RAG Chat Responses
4. Automatic Categorization

### Faza 2: Advanced Features
5. Artifact Generation
6. Export Functions
7. Multi-project Isolation

### Faza 3: External Integrations (wymagają API keys)
8. Web Crawling
9. YouTube Transcriptions
10. AI Insights

---

## Narzędzia do testowania:

### 1. Frontend UI (http://localhost:3555)
- Manualnie przez przeglądarkę
- Najłatwiejsze dla większości testów

### 2. API Testing (curl/Postman)
- Backend API: http://localhost:8765
- Swagger docs: http://localhost:8765/docs
- Przydatne do automatycznych testów

### 3. Database Inspection
```bash
docker exec -it knowledgetree-db psql -U knowledgetree -d knowledgetree
```

### 4. Log Monitoring
```bash
docker logs -f knowledgetree-backend
```

---

## Przygotowanie środowiska testowego:

### 1. Sprawdź czy wszystko działa:
```bash
docker ps  # wszystkie kontenery UP
curl http://localhost:8765/health
curl http://localhost:3555
```

### 2. Zresetuj bazę (jeśli potrzeba fresh start):
```bash
docker-compose down -v
docker-compose up -d
# Poczekaj 30s na inicjalizację
```

### 3. Utwórz użytkownika testowego:
- Email: test@knowledgetree.com
- Password: testpassword123
- Przez frontend: http://localhost:3555

### 4. Przygotuj przykładowe pliki:
- PDF 1: Prosty artykuł (10-20 stron)
- PDF 2: Z tabelami i grafikami
- PDF 3: Długi dokument (100+ stron)
- YouTube URL: np. prezentacja edukacyjna
- Website URL: np. dokumentacja techniczna

---

## Metryki wartości produktu (co mierzymy):

### 1. Dokładność (Accuracy)
- % pytań na które RAG daje poprawną odpowiedź
- Cel: >85%

### 2. Przydatność (Utility)
- Czy odpowiedzi są użyteczne dla użytkownika
- Subiektywna ocena 1-5
- Cel: średnia >4

### 3. Szybkość (Performance)
- Czas uploadu i processingu dokumentu
- Czas odpowiedzi chat (<3s)
- Czas search (<1s)

### 4. Jakość kategoryzacji
- Czy auto-kategorie są lepsze niż random
- Czy oszczędzają czas vs manualna kategoryzacja

### 5. User Experience
- Czy UI jest intuicyjny
- Czy łatwo znaleźć to czego potrzebuję
- Czy są frustrujące momenty

---

## Po testach: Pytania do odpowiedzi

1. **Czy to rozwiązuje realny problem?**
   - Dla jakiego use case to jest najbardziej przydatne?
   - Kto by z tego korzystał?

2. **Co działa najlepiej?**
   - Które feature'y są najbardziej wartościowe?
   - Co użytkownicy używaliby najczęściej?

3. **Co wymaga poprawy?**
   - Które feature'y są buggy/niestabilne?
   - Co jest trudne w użyciu?
   - Gdzie są gaps w funkcjonalności?

4. **Jakie są najpilniejsze potrzeby?**
   - Czego brakuje najbardziej?
   - Co by znacząco zwiększyło wartość?

5. **Czy warto to rozwijać?**
   - Czy widzisz use case dla siebie/innych?
   - Czy to tworzy wartość większą niż koszt utrzymania?

---

## Notatki z testów (wypełnij podczas testowania):

### Test 1: PDF Upload
- Data: _____
- Pliki: _____
- Wyniki: _____
- Problemy: _____

### Test 2: Categorization
- Data: _____
- Dokumenty: _____
- Wyniki: _____
- Problemy: _____

(itd. dla każdego testu)

---

## Następne kroki po walidacji:

### Jeśli wartość jest potwierdzona:
1. Określ target users i use cases
2. Zdecyduj co dać za free, co płatnie
3. Określ pricing na podstawie kosztów i wartości
4. Marketing i dystrybucja

### Jeśli wartość jest wątpliwa:
1. Zidentyfikuj główne problemy
2. Pivot lub iteracja na core value proposition
3. Może to narzędzie wewnętrzne dla Ciebie, nie biznes

---

**Pamiętaj:** Najpierw produkt, potem biznes. Build something people want! 🎯

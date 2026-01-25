# Plan Implementacji Zaawansowanego RAG dla KnowledgeTree

## Podsumowanie Executive

KnowledgeTree obecnie posiada podstawowy RAG (tylko dense retrieval). Plan zakłada implementację kompletnego, zaawansowanego systemu RAG zgodnego z najlepszymi praktykami 2025, bazując na sprawdzonych technikach z projektu ALURON.

**Cel**: Zwiększenie accuracy RAG z ~60-70% (podstawowy) do ~85-95% (zaawansowany)

---

## 1. Analiza Obecnego Stanu

### KnowledgeTree RAG - Stan Obecny (BASIC)

**✅ Co już mamy:**
- Dense retrieval z BGE-M3 embeddings (1024 wymiarów)
- PostgreSQL + pgvector z cosine similarity
- Podstawowy chunking dokumentów (fixed size)
- Claude 3.5 Sonnet jako LLM
- FastAPI async backend

**❌ Czego brakuje:**
- ❌ Sparse retrieval (BM25 keyword matching)
- ❌ Hybrid search (dense + sparse fusion)
- ❌ Reciprocal Rank Fusion (RRF)
- ❌ Cross-encoder reranking
- ❌ Contextual embeddings
- ❌ CRAG (self-reflection, query evaluation)
- ❌ Query expansion
- ❌ Explainability (dlaczego wybrano chunk?)
- ❌ Metadata filtering
- ❌ Conditional reranking optimization
- ❌ Dual-source retrieval

---

## 2. Reference: ALURON RAG (ADVANCED)

### Techniki zaimplementowane w ALURON:

**1. Hybrid Contextual RAG**
```python
# 3-way hybrid search
Dense (pgvector, multilingual-e5-large) → weight 0.5
Sparse (BM25Okapi, rank-bm25) → weight 0.3
Knowledge Graph (Neo4j) → weight 0.2
↓
Reciprocal Rank Fusion (RRF k=60)
↓
Cross-Encoder Reranking (ms-marco-MiniLM-L-12-v2)
```

**2. Contextual Embeddings**
```python
# Include surrounding context in embeddings
context = f"{context_before} [MAIN] {content} [/MAIN] {context_after}"
metadata_str = f"[META] {json.dumps(metadata)} [/META]"
full_context = f"{metadata_str} {context}"
embedding = embedder.encode(full_context)
```

**3. Enhanced Reranking**
- Domain-specific keyword boosting (+0.05 to +0.15)
- Document type preference boosting (+0.1)
- Category-based boosting (+0.05 to +0.20)
- Conditional reranking (skip if not needed)

**4. Dual-Source Retrieval**
- Parallel pipelines (Docling + PyMuPDF)
- Weighted RRF fusion (0.55 Docling, 0.45 PyMuPDF)

**5. Explainability**
- Generate explanation for each ranking decision
- Show contribution from each retrieval method

---

## 3. RAG 2025 Best Practices (Research)

### Trendy RAG 2025:

**A. CRAG (Corrective RAG)** ⭐⭐⭐
- **Self-reflection**: Lightweight retrieval evaluator ocenia quality retrieved docs
- **Query evaluation**: Assess whether query is ambiguous/needs refinement
- **Corrective actions**:
  - If docs quality LOW → trigger web search fallback
  - If docs quality MEDIUM → knowledge refinement
  - If docs quality HIGH → use as-is
- **Sources**: [LangChain CRAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/), [Meilisearch CRAG](https://www.meilisearch.com/blog/corrective-rag), [DataCamp CRAG](https://www.datacamp.com/tutorial/corrective-rag-crag)

**B. Self-RAG** ⭐⭐
- Model learns WHEN to retrieve (not always needed)
- Self-critique of outputs → improve factuality
- Reflection tokens flag inconsistencies
- **Sources**: [Self-RAG Article](https://www.analyticsvidhya.com/blog/2025/01/self-rag/), [LangChain Self-Reflective RAG](https://blog.langchain.com/agentic-rag-with-langgraph/)

**C. Agentic RAG** ⭐⭐
- Autonomous agents plan multiple retrieval steps
- Iterative reasoning and adaptive strategies
- Choose tools dynamically (search, calculator, code exec)
- **Sources**: [Agentic RAG Survey](https://arxiv.org/html/2501.09136v1), [Lyzr Agentic RAG](https://www.lyzr.ai/blog/agentic-rag), [Data Nucleus RAG Guide](https://datanucleus.dev/rag-and-agentic-ai/what-is-rag-enterprise-guide-2025)

**D. Graph RAG** ⭐
- Entity-centric graphs from retrieved passages
- Community summarization for large corpora
- Improves multi-hop QA recall by 6.4 points
- **Sources**: [RAG Trends 2025](https://www.signitysolutions.com/blog/trends-in-active-retrieval-augmented-generation)

**E. Hybrid Search + Reranking (Standard)** ⭐⭐⭐
- Dense + Sparse with RRF fusion (k=60 universal)
- Late interaction reranking (ColBERT recommended)
- **Performance**: +300ms latency but worth it for accuracy
- **Sources**: [Dense vs Sparse vs Hybrid](https://medium.com/@robertdennyson/dense-vs-sparse-vs-hybrid-rrf-which-rag-technique-actually-works-1228c0ae3f69), [Hybrid Search Best Practices](https://infiniflow.org/blog/best-hybrid-search-solution), [RAG Retrieval Strategies](https://rajnandan.medium.com/rag-retrieval-strategies-sparse-dense-and-hybrid-how-to-choose-and-implement-7eaec4e65da9)

**F. HyDE (Hypothetical Document Embeddings)** ⭐
- Generate hypothetical answer → embed → retrieve similar real docs
- Improves recall for niche/underspecified queries

**G. Query Decomposition** ⭐⭐
- Break complex queries into sub-queries
- Retrieve separately → aggregate results

**H. Contextual Re-ranking** ⭐⭐
- Real-time context-aware scoring
- Adaptive weights based on query type

---

## 4. Priorytetyzacja Implementacji

### TIER 1: CORE (Must-Have) - Priority HIGH

**1.1 BM25 Sparse Retrieval**
- Library: `rank-bm25` (pip install rank-bm25)
- Index ALL chunks at startup
- Tokenization: Polish-aware (simple split dla MVP)
- **Impact**: +10-15% recall
- **Complexity**: Medium
- **Time**: 2-3 dni

**1.2 Hybrid Search with RRF**
- Combine dense + sparse results
- Weights: 0.6 dense, 0.4 sparse (default)
- RRF constant k=60
- **Impact**: +15-20% overall accuracy
- **Complexity**: Low (straightforward algorithm)
- **Time**: 1-2 dni

**1.3 Cross-Encoder Reranking**
- Model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual, Polish support)
- Retrieve top-20 → rerank → return top-5
- **Impact**: +10-15% precision
- **Complexity**: Medium
- **Time**: 2-3 dni

**1.4 Contextual Embeddings**
- Include chunk_before + chunk_after in embeddings
- Add metadata tags `[META]` `[MAIN]`
- Re-embed ALL existing chunks
- **Impact**: +5-10% context awareness
- **Complexity**: Medium-High (requires re-embedding)
- **Time**: 3-4 dni (including migration)

### TIER 2: ENHANCED (Should-Have) - Priority MEDIUM

**2.1 CRAG (Corrective RAG) - Self-Reflection**
- Retrieval evaluator model (classifier)
- Quality scores: HIGH/MEDIUM/LOW
- Fallback strategies:
  - LOW → web search with Tavily/SerpAPI
  - MEDIUM → query refinement + re-retrieve
  - HIGH → proceed to generation
- **Impact**: +10-15% robustness (fewer hallucinations)
- **Complexity**: High
- **Time**: 5-7 dni

**2.2 Query Expansion**
- Synonym expansion (Polish thesaurus)
- Entity extraction (NER)
- Related terms lookup
- **Impact**: +5-10% recall for complex queries
- **Complexity**: Medium
- **Time**: 3-4 dni

**2.3 Conditional Reranking Optimization**
- Skip reranking if:
  - Top score gap > 0.10 (clear winner)
  - Top score > 0.30 (high confidence)
  - Score variance < 0.02 (well-separated)
- **Impact**: -30-50% latency on simple queries
- **Complexity**: Low
- **Time**: 1 dzień

**2.4 Explainability**
- Generate explanation for each result:
  - "Dense match: 0.85 (semantic similarity)"
  - "Sparse match: 0.72 (keyword: 'API', 'authentication')"
  - "Reranker boost: +0.10 (cross-encoder score)"
- **Impact**: User trust, debugging
- **Complexity**: Low
- **Time**: 1-2 dni

### TIER 3: ADVANCED (Nice-to-Have) - Priority LOW

**3.1 Self-RAG**
- Decide when to retrieve (not always needed)
- Reflection tokens for inconsistencies
- **Impact**: +5-10% efficiency
- **Complexity**: Very High
- **Time**: 10-14 dni

**3.2 Agentic RAG**
- Multi-step reasoning
- Tool selection (search, calculator, code)
- **Impact**: +20-30% on complex tasks
- **Complexity**: Very High
- **Time**: 14-21 dni

**3.3 Graph RAG**
- Neo4j integration
- Entity extraction + relationship mapping
- **Impact**: +10-15% on multi-hop QA
- **Complexity**: Very High
- **Time**: 14-21 dni

**3.4 HyDE**
- Generate hypothetical answer
- Embed + retrieve similar real docs
- **Impact**: +5-10% on niche queries
- **Complexity**: Medium
- **Time**: 3-4 dni

---

## 5. Architecture Docelowa

### Before (Current - BASIC RAG):
```
User Query
    ↓
BGE-M3 Embedding
    ↓
PostgreSQL pgvector (cosine similarity, top 5)
    ↓
Claude 3.5 Sonnet (generate answer)
    ↓
Response
```

### After (Advanced RAG - TIER 1):
```
User Query
    ↓
┌─────────────────────────────┐
│   PARALLEL RETRIEVAL        │
├─────────────────────────────┤
│ Dense (BGE-M3, top 20)      │ → weight 0.6
│ Sparse (BM25, top 20)       │ → weight 0.4
└─────────────────────────────┘
    ↓
Reciprocal Rank Fusion (RRF k=60, top 20)
    ↓
Cross-Encoder Reranking (mmarco-mMiniLMv2, top 5)
    ↓
Claude 3.5 Sonnet (generate answer with explanations)
    ↓
Response + Source Explanations
```

### After (Advanced RAG - TIER 1 + TIER 2):
```
User Query
    ↓
Query Expansion (synonyms, entities)
    ↓
┌─────────────────────────────┐
│   PARALLEL RETRIEVAL        │
├─────────────────────────────┤
│ Dense (BGE-M3, top 20)      │ → weight 0.6
│ Sparse (BM25, top 20)       │ → weight 0.4
└─────────────────────────────┘
    ↓
Reciprocal Rank Fusion (RRF k=60, top 20)
    ↓
Conditional Reranking Check
    ├─ SKIP → Use RRF results (if clear winner)
    └─ APPLY → Cross-Encoder Reranking (top 5)
         ↓
CRAG Self-Reflection (evaluate quality)
    ├─ HIGH → Proceed to generation
    ├─ MEDIUM → Query refinement + re-retrieve
    └─ LOW → Web search fallback (Tavily/SerpAPI)
         ↓
Claude 3.5 Sonnet (generate answer with explanations)
    ↓
Response + Source Explanations + Quality Score
```

---

## 6. Implementation Plan - TIER 1 (Core)

### Phase 1: BM25 Sparse Retrieval (2-3 dni)

**Files to Create/Modify:**
1. `backend/services/bm25_service.py` (NEW)
   - BM25Okapi index initialization
   - Tokenization (Polish-aware)
   - Search method

2. `backend/services/search_service.py` (MODIFY)
   - Add `search_sparse()` method
   - Parallel execution with `search_dense()`

3. `backend/core/dependencies.py` (MODIFY)
   - Initialize BM25 index at startup
   - Load all chunks into memory

**Dependencies:**
```bash
pip install rank-bm25
```

**Code Pattern (from ALURON):**
```python
from rank_bm25 import BM25Okapi

class BM25Service:
    def __init__(self):
        self.bm25_index = None
        self.doc_ids = []
        self.documents = []

    async def initialize(self, chunks: List[DocumentChunk]):
        # Tokenize all chunks
        tokenized_corpus = [chunk.content.lower().split() for chunk in chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        self.doc_ids = [chunk.id for chunk in chunks]
        self.documents = chunks

    async def search(self, query: str, top_k: int = 20):
        query_tokens = query.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)

        # Get top-k indices
        import numpy as np
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            results.append({
                "id": self.doc_ids[idx],
                "content": self.documents[idx].content,
                "score": float(scores[idx]),
                "source": "sparse"
            })
        return results
```

**Testing:**
- Query: "jak skonfigurować autentykację JWT?"
- Expected: BM25 should catch exact keywords "autentykacja", "JWT"
- Verify: Sparse results complement dense results

---

### Phase 2: Hybrid Search with RRF (1-2 dni)

**Files to Create/Modify:**
1. `backend/services/hybrid_search_service.py` (NEW)
   - RRF fusion algorithm
   - Parallel execution coordinator

2. `backend/services/search_service.py` (MODIFY)
   - Replace `search()` with `hybrid_search()`

**Code Pattern (from ALURON):**
```python
class HybridSearchService:
    def __init__(self, dense_service, sparse_service):
        self.dense = dense_service
        self.sparse = sparse_service

    async def search(
        self,
        query: str,
        top_k: int = 20,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60
    ):
        # Parallel retrieval
        dense_results, sparse_results = await asyncio.gather(
            self.dense.search(query, top_k=top_k),
            self.sparse.search(query, top_k=top_k)
        )

        # Reciprocal Rank Fusion
        scores = {}
        item_data = {}

        # Dense scores
        for rank, item in enumerate(dense_results):
            item_id = item["id"]
            if item_id not in scores:
                scores[item_id] = 0
                item_data[item_id] = item
            scores[item_id] += dense_weight * (1 / (rrf_k + rank + 1))

        # Sparse scores
        for rank, item in enumerate(sparse_results):
            item_id = item["id"]
            if item_id not in item_data:
                item_data[item_id] = item
            if item_id not in scores:
                scores[item_id] = 0
            scores[item_id] += sparse_weight * (1 / (rrf_k + rank + 1))

        # Sort by RRF score
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build final results
        results = []
        for item_id, score in sorted_items[:top_k]:
            result = item_data[item_id].copy()
            result["rrf_score"] = score
            results.append(result)

        return results
```

**Testing:**
- Query with both semantic AND keyword importance
- Example: "różnica między OAuth2 a JWT w API REST"
  - Dense should catch: "różnica", "OAuth2", "JWT" (semantic)
  - Sparse should catch: "OAuth2", "JWT", "API", "REST" (exact keywords)
- Verify: RRF combines both effectively

---

### Phase 3: Cross-Encoder Reranking (2-3 dni)

**Files to Create/Modify:**
1. `backend/services/reranker_service.py` (NEW)
   - CrossEncoder initialization
   - Rerank method

2. `backend/services/search_service.py` (MODIFY)
   - Add reranking step after hybrid search

**Dependencies:**
```bash
pip install sentence-transformers
```

**Model Selection:**
```python
# Multilingual (Polish support) - RECOMMENDED
cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')

# Alternative (English-only, faster)
# cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
```

**Code Pattern (from ALURON):**
```python
from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self):
        self.model = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')

    async def rerank(
        self,
        query: str,
        chunks: List[dict],
        top_k: int = 5
    ):
        if not chunks or len(chunks) <= top_k:
            return chunks

        # Prepare pairs for reranking
        pairs = [[query, chunk["content"]] for chunk in chunks]

        # Get reranking scores
        scores = self.model.predict(pairs)

        # Attach scores and sort
        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])

        reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
```

**Testing:**
- Query: "jak zabezpieczyć API przed atakami CSRF?"
- Retrieve top-20 with hybrid search
- Verify: Reranker should promote chunks that actually ANSWER the question (not just mention keywords)

---

### Phase 4: Contextual Embeddings (3-4 dni)

**Files to Create/Modify:**
1. `backend/services/document_processing_service.py` (MODIFY)
   - Add contextual chunking with overlap
   - Store `chunk_before` and `chunk_after` in metadata

2. `backend/services/embedding_service.py` (MODIFY)
   - Modify embedding to include context + metadata tags

3. Database migration script (NEW)
   - Add `chunk_before` and `chunk_after` columns
   - Re-embed all existing chunks

**Code Pattern (from ALURON):**
```python
def contextual_chunk(text: str, chunk_size: int = 512, overlap: int = 50):
    sentences = text.split('. ')
    chunks = []

    for i in range(0, len(sentences), chunk_size):
        # Get context before
        context_before = '. '.join(sentences[max(0, i-2):i]) if i > 0 else ""

        # Main chunk
        main_chunk = '. '.join(sentences[i:i+chunk_size])

        # Get context after
        context_after = '. '.join(sentences[i+chunk_size:min(i+chunk_size+2, len(sentences))])

        chunks.append({
            "content": main_chunk,
            "context_before": context_before,
            "context_after": context_after
        })

    return chunks

def generate_contextual_embedding(chunk: dict, metadata: dict):
    # Build context
    context = f"{chunk['context_before']} [MAIN] {chunk['content']} [/MAIN] {chunk['context_after']}"

    # Add metadata
    metadata_str = f"[META] {json.dumps(metadata)} [/META]"
    full_context = f"{metadata_str} {context}"

    # Embed
    embedding = embedder.encode(full_context)
    return embedding
```

**Migration Plan:**
1. Add columns: `ALTER TABLE chunks ADD COLUMN chunk_before TEXT, ADD COLUMN chunk_after TEXT;`
2. Re-process all documents with contextual chunking
3. Re-embed all chunks with new context
4. Update pgvector index

**Testing:**
- Query: "jak działa middleware w FastAPI?"
- Old: Chunk with just "middleware" mention
- New: Chunk with context "FastAPI ma middleware system. Middleware to..."
- Verify: Better context understanding

---

## 7. Implementation Plan - TIER 2 (Enhanced)

### Phase 5: CRAG Self-Reflection (5-7 dni)

**Concept**: Add retrieval quality evaluator that decides if results are good enough or need correction.

**Files to Create:**
1. `backend/services/crag_service.py` (NEW)
   - Quality evaluator (classifier model or heuristic)
   - Fallback strategies (web search, query refinement)

**Code Pattern:**
```python
class CRAGService:
    def __init__(self):
        self.quality_thresholds = {
            "HIGH": 0.75,
            "MEDIUM": 0.50,
            "LOW": 0.0
        }

    async def evaluate_retrieval_quality(self, query: str, chunks: List[dict]):
        # Heuristic-based quality evaluation
        if not chunks:
            return "LOW"

        top_score = chunks[0].get("rerank_score", chunks[0].get("rrf_score", 0))
        avg_score = sum(c.get("rerank_score", c.get("rrf_score", 0)) for c in chunks) / len(chunks)

        if top_score > self.quality_thresholds["HIGH"]:
            return "HIGH"
        elif avg_score > self.quality_thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"

    async def corrective_action(self, query: str, quality: str, chunks: List[dict]):
        if quality == "HIGH":
            # Proceed with retrieved chunks
            return chunks

        elif quality == "MEDIUM":
            # Refine query and re-retrieve
            refined_query = await self.refine_query(query)
            # Re-run hybrid search with refined query
            return await self.hybrid_search.search(refined_query)

        else:  # LOW
            # Fallback to web search
            web_results = await self.web_search(query)
            return web_results

    async def refine_query(self, query: str):
        # Use LLM to refine query
        prompt = f"Refine this query for better search: {query}"
        refined = await llm.generate(prompt)
        return refined

    async def web_search(self, query: str):
        # Tavily API or SerpAPI
        # For MVP: return empty or use WebSearch tool
        return []
```

**Testing:**
- Query with HIGH quality results → proceed normally
- Query with LOW quality results → trigger web search fallback
- Measure: % of queries needing correction

---

### Phase 6: Query Expansion (3-4 dni)

**Files to Create:**
1. `backend/services/query_expansion_service.py` (NEW)
   - Synonym expansion (Polish thesaurus)
   - Entity extraction (spaCy PL model)

**Dependencies:**
```bash
pip install spacy
python -m spacy download pl_core_news_sm
```

**Code Pattern:**
```python
import spacy

class QueryExpansionService:
    def __init__(self):
        self.nlp = spacy.load("pl_core_news_sm")
        self.synonyms = {
            "API": ["REST API", "endpoint", "interfejs"],
            "autentykacja": ["uwierzytelnienie", "login", "logowanie"],
            "JWT": ["JSON Web Token", "token"],
            # ... more synonyms
        }

    async def expand_query(self, query: str):
        # Entity extraction
        doc = self.nlp(query)
        entities = [ent.text for ent in doc.ents]

        # Synonym expansion
        expanded_terms = []
        for word in query.split():
            if word in self.synonyms:
                expanded_terms.extend(self.synonyms[word])

        # Build expanded query
        expanded_query = f"{query} {' '.join(expanded_terms)}"
        return expanded_query
```

---

### Phase 7: Conditional Reranking + Explainability (2-3 dni)

**Conditional Reranking** (from ALURON):
```python
def should_rerank(chunks: List[dict]) -> tuple[bool, str]:
    if len(chunks) < 2:
        return (False, "Too few chunks")

    scores = [c["rrf_score"] for c in chunks]
    top_score = scores[0]
    second_score = scores[1]
    top_gap = top_score - second_score

    import statistics
    std_score = statistics.stdev(scores)

    # Skip reranking if clear winner
    if top_gap > 0.10:
        return (False, f"Clear winner (gap={top_gap:.3f})")

    # Skip if high confidence
    if top_score > 0.30:
        return (False, f"High confidence (score={top_score:.3f})")

    # Skip if low variance
    if std_score < 0.02:
        return (False, f"Low variance (std={std_score:.3f})")

    return (True, "Reranking beneficial")
```

**Explainability**:
```python
def generate_explanation(chunk: dict):
    explanation = []

    if "dense_score" in chunk:
        explanation.append(f"Semantic similarity: {chunk['dense_score']:.2f}")

    if "sparse_score" in chunk:
        explanation.append(f"Keyword match: {chunk['sparse_score']:.2f}")

    if "rrf_score" in chunk:
        explanation.append(f"Combined score (RRF): {chunk['rrf_score']:.2f}")

    if "rerank_score" in chunk:
        explanation.append(f"Relevance score (reranker): {chunk['rerank_score']:.2f}")

    return " | ".join(explanation)
```

---

## 8. Performance Benchmarks (Expected)

| Metric | Current (Basic) | TIER 1 | TIER 1 + TIER 2 |
|--------|----------------|--------|-----------------|
| **Accuracy** | 60-70% | 80-85% | 85-95% |
| **Precision@5** | 0.65 | 0.80 | 0.85 |
| **Recall@5** | 0.60 | 0.75 | 0.80 |
| **Latency** | ~200ms | ~500ms | ~700ms |
| **Hallucination Rate** | 15-20% | 8-12% | 3-5% |

---

## 9. Timeline Estimate

### TIER 1 (Core) - Total: ~8-12 dni
- Phase 1: BM25 Sparse Retrieval → 2-3 dni
- Phase 2: Hybrid Search with RRF → 1-2 dni
- Phase 3: Cross-Encoder Reranking → 2-3 dni
- Phase 4: Contextual Embeddings → 3-4 dni

### TIER 2 (Enhanced) - Total: ~11-17 dni
- Phase 5: CRAG Self-Reflection → 5-7 dni
- Phase 6: Query Expansion → 3-4 dni
- Phase 7: Conditional Reranking + Explainability → 2-3 dni
- Phase 8: Testing & Optimization → 1-3 dni

### TIER 3 (Advanced) - Total: ~40-60 dni (future)
- Self-RAG: 10-14 dni
- Agentic RAG: 14-21 dni
- Graph RAG: 14-21 dni
- HyDE: 3-4 dni

**TOTAL (TIER 1 + TIER 2): 19-29 dni roboczych (~4-6 tygodni)**

---

## 10. Testing Strategy

### Unit Tests
- Test każdej metody retrieval osobno (dense, sparse, hybrid)
- Test RRF fusion z różnymi wagami
- Test reranking z różnymi modelami
- Test CRAG quality evaluation logic

### Integration Tests
- End-to-end RAG pipeline
- Performance benchmarks (latency, throughput)
- Accuracy tests (golden dataset z known answers)

### Evaluation Dataset
Stworzyć 50-100 pytań z expected answers:
```json
[
  {
    "query": "Jak skonfigurować JWT authentication w FastAPI?",
    "expected_chunks": ["chunk_id_123", "chunk_id_456"],
    "expected_answer_contains": ["JWT", "FastAPI", "authentication", "oauth2"]
  },
  ...
]
```

Metryki:
- **Recall@K**: Czy expected chunks są w top-K?
- **MRR (Mean Reciprocal Rank)**: Pozycja pierwszego relevant chunk
- **NDCG (Normalized Discounted Cumulative Gain)**: Quality of ranking
- **Answer Quality**: LLM-as-judge (Claude ocenia answer quality 1-5)

---

## 11. Migration Plan (Contextual Embeddings)

### Database Migration
```sql
-- Add context columns
ALTER TABLE document_knowledge
ADD COLUMN chunk_before TEXT,
ADD COLUMN chunk_after TEXT;

-- Add metadata for CRAG
ALTER TABLE document_knowledge
ADD COLUMN retrieval_quality VARCHAR(10) DEFAULT 'UNKNOWN',
ADD COLUMN last_quality_check TIMESTAMP;
```

### Re-embedding Script
```python
async def migrate_to_contextual_embeddings():
    # 1. Fetch all documents
    documents = await get_all_documents()

    # 2. Re-process with contextual chunking
    for doc in documents:
        chunks = contextual_chunk(doc.content)

        # 3. Re-embed with context
        for chunk in chunks:
            embedding = generate_contextual_embedding(
                chunk,
                metadata={"doc_id": doc.id, "doc_type": doc.type}
            )

            # 4. Update database
            await update_chunk_embedding(chunk.id, embedding, chunk)

    print("Migration complete!")
```

---

## 12. Monitoring & Observability

### Metrics to Track
```python
# Latency breakdown
metrics = {
    "dense_retrieval_ms": 50,
    "sparse_retrieval_ms": 30,
    "rrf_fusion_ms": 5,
    "reranking_ms": 150,
    "llm_generation_ms": 800,
    "total_ms": 1035
}

# Quality metrics
quality = {
    "retrieval_quality": "HIGH",  # CRAG evaluation
    "top_chunk_score": 0.85,
    "avg_chunk_score": 0.72,
    "reranking_applied": True,
    "web_fallback_used": False
}

# Usage metrics
usage = {
    "queries_per_hour": 120,
    "avg_chunks_per_query": 5.2,
    "cache_hit_rate": 0.35
}
```

### Logging
```python
logger.info(f"[HYBRID_SEARCH] Query: {query[:50]}...")
logger.info(f"  Dense: {len(dense_results)} results, top_score={dense_results[0]['score']:.3f}")
logger.info(f"  Sparse: {len(sparse_results)} results, top_score={sparse_results[0]['score']:.3f}")
logger.info(f"  RRF: {len(fused_results)} results, top_score={fused_results[0]['rrf_score']:.3f}")
logger.info(f"  Reranking: {'APPLIED' if reranked else 'SKIPPED'}")
logger.info(f"  CRAG Quality: {quality}")
```

---

## 13. Sources & References

### CRAG (Corrective RAG)
- [LangChain CRAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)
- [Meilisearch CRAG Blog](https://www.meilisearch.com/blog/corrective-rag)
- [Chitika CRAG Implementation](https://www.chitika.com/corrective-rag-hallucinations/)
- [DataCamp CRAG Tutorial](https://www.datacamp.com/tutorial/corrective-rag-crag)
- [Cobus Greyling CRAG Article](https://cobusgreyling.medium.com/corrective-rag-crag-5e40467099f8)

### RAG 2025 Trends
- [Agentic RAG Survey (arXiv)](https://arxiv.org/html/2501.09136v1)
- [Lyzr Agentic RAG Guide](https://www.lyzr.ai/blog/agentic-rag)
- [Data Nucleus RAG 2025 Guide](https://datanucleus.dev/rag-and-agentic-ai/what-is-rag-enterprise-guide-2025)
- [Signity RAG Trends 2025](https://www.signitysolutions.com/blog/trends-in-active-retrieval-augmented-generation)
- [Self-RAG Article](https://www.analyticsvidhya.com/blog/2025/01/self-rag/)

### Hybrid Search Best Practices
- [Dense vs Sparse vs Hybrid (Medium)](https://medium.com/@robertdennyson/dense-vs-sparse-vs-hybrid-rrf-which-rag-technique-actually-works-1228c0ae3f69)
- [Infinity Hybrid Search](https://infiniflow.org/blog/best-hybrid-search-solution)
- [RAG Retrieval Strategies (Medium)](https://rajnandan.medium.com/rag-retrieval-strategies-sparse-dense-and-hybrid-how-to-choose-and-implement-7eaec4e65da9)
- [Superlinked Hybrid Search](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- [Meilisearch Hybrid Search RAG](https://www.meilisearch.com/blog/hybrid-search-rag)

---

## 14. Next Steps

1. **Review plan z zespołem** - ustalić priorytety
2. **Setup dev environment** - zainstalować dependencies
3. **Start TIER 1 Phase 1** - BM25 Sparse Retrieval
4. **Iterative testing** - test after każdej fazy
5. **Monitor performance** - track latency & accuracy improvements
6. **Iterate** - adjust weights, models based on results

**Pierwsza akcja**: Czy zaczynamy od TIER 1 Phase 1 (BM25)?

# SmartShop AI — Agentic E-Commerce Assistant
## System Design & Implementation Guide

---

## 1. Solution Overview

The problem statement maps cleanly onto a **multi-agent, RAG-augmented conversational system** sitting on top of three data sources (product catalog, reviews, FAQ/policies). A single "smart" chatbot cannot do this well — product discovery, price comparison, review synthesis, and policy Q&A require different retrieval strategies, different models, and different freshness guarantees. The right architecture is a **supervisor + specialist agents** pattern: one orchestrator agent interprets the user's intent and delegates to purpose-built sub-agents, each with its own tools, data access, and evaluation criteria.

```
                     ┌─────────────────────────┐
                     │   Conversational UI      │
                     │ (chat widget / voice)    │
                     └────────────┬─────────────┘
                                  │
                     ┌────────────▼─────────────┐
                     │   Orchestrator Agent      │
                     │ (intent routing, memory,  │
                     │  multi-intent decomposition)│
                     └──┬────────┬────────┬──────┘
          ┌─────────────┘        │        └─────────────┐
          ▼                      ▼                       ▼
 ┌──────────────────┐  ┌──────────────────┐   ┌──────────────────────┐
 │ Recommendation    │  │ Price Comparison  │   │ Review Summarization  │
 │ Agent             │  │ Agent             │   │ / Sentiment Agent     │
 └────────┬──────────┘  └────────┬──────────┘   └──────────┬────────────┘
          │                      │                          │
          ▼                      ▼                          ▼
 ┌──────────────────┐  ┌──────────────────┐   ┌──────────────────────┐
 │ Product Catalog   │  │ Live Price Feeds  │   │ Customer Reviews      │
 │ DB + Vector Index │  │ (APIs/scrapers)   │   │ DB + Vector Index     │
 └───────────────────┘  └────────────────────┘   └───────────────────────┘

                     ┌──────────────────────┐
                     │ FAQ / Policy Agent     │
                     │ (RAG over policies)    │
                     └──────────┬─────────────┘
                                ▼
                     ┌──────────────────────┐
                     │ FAQ & Policy Vector    │
                     │ Index                  │
                     └───────────────────────┘
```

---

## 2. Multi-Agent Architecture

| Agent | Responsibility | Key Tools |
|---|---|---|
| **Orchestrator (Supervisor)** | Classifies intent, decomposes compound queries ("find me a cheap phone with good reviews"), maintains conversation state, routes to one or more agents, merges responses | `route_intent()`, conversation memory store |
| **Recommendation Agent** | Personalized product discovery based on stated preferences + interaction history | `search_catalog()`, `get_user_profile()`, `rank_candidates()` |
| **Price Comparison Agent** | Cross-seller/brand price lookup, deal detection, price-history trend | `get_prices(product_id)`, `compare_prices()` |
| **Review Summarization Agent** | Aspect-based sentiment extraction and pros/cons summarization per product | `get_reviews(product_id)`, `summarize_sentiment()` |
| **FAQ/Policy Agent** | Answers return/refund/shipping questions strictly from store policy documents | `retrieve_policy(query)`, RAG generation with citation |
| **(Optional) Cart/Order Agent** | Adds items to cart, checks order status | `add_to_cart()`, `get_order_status()` |

**Why agents instead of one giant prompt:** each specialist has a narrow tool surface, its own retrieval index, and can be evaluated/tuned independently (e.g., you can swap the sentiment model without touching recommendation logic). It also lets you fail gracefully — if the price API is down, the orchestrator can still answer a review-summary question.

**Orchestration pattern:** implement as a stateful graph (LangGraph) or role-based crew (CrewAI/AutoGen). Recommended: LangGraph, because e-commerce conversations are inherently stateful (cart, filters, prior turns) and you need explicit control flow (e.g., "if price agent times out, fall back to cached prices") rather than fully autonomous agent chatter.

---

## 3. Data Layer

Each dataset needs **two representations**: a structured table for exact filtering (price range, brand, category) and a vector index for semantic search (natural-language queries, review text, policy text).

### 3.1 Product Catalog
```
products(
  product_id PK, name, brand, category, subcategory,
  price, currency, description, image_url,
  attributes JSONB,        -- color, size, specs
  embedding VECTOR(1536),  -- from name+description
  last_updated TIMESTAMP
)
```
Source ETL: normalize Amazon/Flipkart/Kaggle catalog dumps → dedupe by brand+name+category → generate embeddings from `name + description + category` → index in vector store, mirror scalar fields in Postgres for filtering.

### 3.2 Customer Reviews
```
reviews(
  review_id PK, product_id FK, rating, review_text,
  sentiment_label,       -- pos/neg/neutral (computed, not just Kaggle label)
  aspects JSONB,         -- {"battery":"positive","camera":"negative"}
  timestamp,
  embedding VECTOR(1536)
)
```
Precompute sentiment + aspect labels at ingestion time (batch job), not at query time — summarization should read from precomputed aggregates for latency, and only re-run the LLM summarizer when a product's review set changes materially (e.g., +20 new reviews or nightly batch).

### 3.3 FAQ & Store Policies
```
policy_docs(
  doc_id PK, category,   -- returns/shipping/refunds/etc.
  chunk_text, source_url, embedding VECTOR(1536)
)
```
Chunk by policy section (~200-400 tokens), embed, index. This is a classic RAG corpus — small and stable, so it can be fully re-indexed on every policy update rather than incrementally.

**Storage recommendation:** PostgreSQL with the `pgvector` extension is enough to start (one database, ACID guarantees, avoids running a separate vector DB cluster). Migrate to Pinecone/Weaviate/Milvus only if you need sub-50ms search at large scale or managed infra.

---

## 4. Component Deep Dives

### 4.1 Recommendation Engine
Use a **hybrid** approach — pure collaborative filtering suffers from cold start, pure content-based misses "people like you also liked" signal:

1. **Content-based retrieval:** embed the user's stated preferences/query, do vector similarity search over `products.embedding`, apply hard filters (price range, brand, in-stock) in SQL.
2. **Collaborative signal:** maintain an implicit-feedback matrix (views, clicks, add-to-cart, purchases) and run a lightweight model (ALS or a two-tower neural retrieval model) offline, nightly, to produce "similar users also bought" candidates.
3. **LLM re-ranking:** merge both candidate lists (~30-50 items), pass to the LLM with conversation context ("looking for a gift, budget $50, prefers durability over looks") to re-rank and justify the top 3-5 — this is where the "personalization" the problem statement asks for actually becomes visible to the user, since the LLM can explain *why* an item is recommended.
4. **Cold start:** fall back to category-popularity + explicit preference questions ("What's most important: price, brand, or reviews?") for new users.

### 4.2 Sentiment-Based Review Summarization
```
Reviews → Preprocess (dedupe, spam filter, language detect)
        → Sentiment classification (batch, cheap model)
        → Aspect-based sentiment extraction (ABSA)
        → Aggregate per product (% positive, top complaints, top praises)
        → LLM summarization → "3 pros / 3 cons + overall verdict"
        → Cache summary; invalidate on N new reviews or weekly refresh
```
Use a **fine-tuned lightweight classifier** (DistilBERT/RoBERTa, or the Kaggle sentiment labels as training data) for the classification step across potentially millions of reviews — an LLM call per review is not cost-effective at scale. Reserve the LLM for the final **summarization** step, which only runs once per product per refresh cycle, not per user query. At query time, the agent just retrieves the cached summary — this keeps response latency low.

### 4.3 Real-Time Price Comparison
The Kaggle/crawled catalog gives you a static snapshot, so "real-time" price comparison needs a live data source layered on top:
- **Option A (fastest to build):** scheduled scraping (Playwright/Scrapy) of competitor listings for the same product (matched by UPC/brand+model), refreshed every few hours, stored in a `price_history` table with `source, price, url, scraped_at`.
- **Option B (more robust):** third-party shopping/price-comparison APIs (e.g., SerpAPI Google Shopping, Rainforest API for Amazon) if budget allows — avoids scraper maintenance and ToS risk.
- The agent tool `compare_prices(product_id)` queries `price_history`, returns the cheapest current option plus a price-trend note ("15% below its 30-day average"), and always surfaces the data's timestamp so the user knows how fresh it is.

### 4.4 Store Policy Automation (FAQ Agent)
Straightforward RAG, but the **guardrails matter more than the retrieval** here — a wrong answer about refund policy is a liability, not just a bad UX:
- Retrieve top-k chunks from `policy_docs`, require a minimum similarity threshold.
- Generate the answer **only from retrieved text**, with an explicit instruction to say "I don't have that information — let me connect you with support" rather than guessing.
- Cite the policy section in the response so the user can verify.
- Log every policy-agent answer for periodic human audit (this is the highest-hallucination-risk agent in the system).

### 4.5 Conversational Orchestrator
- **Intent routing:** LLM function-calling classifies each turn into one or more of {recommend, compare_price, summarize_reviews, policy_qa, chit-chat}. Compound queries ("find a laptop under $800 with good battery reviews") should decompose into a recommendation call *plus* a review-summary call, then merge the results into one coherent reply.
- **Memory:** short-term (last N turns, in-session) for coreference ("compare that one with the second option"); long-term (user profile: preferred brands, past purchases, price sensitivity) persisted per user and fed into the recommendation agent as context.
- **Fallback/escalation:** if confidence is low or the query is out-of-scope (e.g., a complaint), route to human support rather than forcing an agent to answer.

---

## 5. Recommended Tech Stack

| Layer | Recommendation | Notes |
|---|---|---|
| LLM | Claude or GPT-4o class model for orchestration/generation; consider a smaller/open model (Llama 3.x) for high-volume classification tasks to control cost | Keep the "smart" model for reasoning/routing, cheap model for bulk sentiment tagging |
| Agent orchestration | LangGraph | Explicit state machine, good for stateful shopping sessions and fallback logic |
| Embeddings | OpenAI `text-embedding-3-small` or open-source Sentence-Transformers | Sentence-Transformers if data privacy/cost is a concern |
| Vector store | PostgreSQL + `pgvector` to start; Pinecone/Weaviate/Milvus if scale demands it | One DB simplifies ops early on |
| Structured DB | PostgreSQL | Also houses product/review/policy scalar fields |
| Backend | FastAPI (Python), async | Exposes REST + WebSocket/SSE for streaming chat responses |
| Frontend | React chat widget embedded in the storefront | Streams tokens for perceived responsiveness |
| Sentiment model | Fine-tuned DistilBERT/RoBERTa (HuggingFace) | Trained/validated on the Kaggle review labels |
| Price data | Scrapy/Playwright scheduled jobs, or SerpAPI/Rainforest API | Store with timestamps; never claim "real-time" without a freshness indicator |
| Observability | LangSmith or Langfuse for agent traces; Prometheus/Grafana for infra | Essential for debugging multi-agent handoffs |
| Guardrails | NeMo Guardrails or a custom validation layer on the Policy Agent | Prevents policy hallucination |
| Deployment | Docker + Kubernetes (or a simpler PaaS like Render/Fly.io for MVP) | Start simple, scale when traffic demands |

---

## 6. Implementation Roadmap

1. **Data engineering** — ingest and clean the three datasets, stand up Postgres + pgvector, build the ETL/embedding pipeline.
2. **Standalone agents** — build and unit-test each specialist agent in isolation (recommendation, sentiment/summarization, FAQ) against its own data, before any orchestration exists.
3. **Orchestration layer** — build the router/supervisor, wire agents together, add conversation memory.
4. **Price comparison** — integrate scraping or a shopping API, add the price agent, add freshness indicators.
5. **Conversational UI** — chat widget, streaming responses, basic feedback (thumbs up/down) to start collecting eval data.
6. **Evaluation & guardrails** — build an eval harness (see §7), add hallucination checks on the Policy Agent, load-test the orchestrator.
7. **Deployment & monitoring** — containerize, add tracing/observability, set up alerting on agent failure rates and latency.

---

## 7. Evaluation Metrics

| Component | Metric |
|---|---|
| Recommendation Agent | Precision@k / Recall@k against held-out interactions, click-through rate, downstream conversion lift |
| Sentiment classifier | Accuracy/F1 against labeled Kaggle test split |
| Review summarizer | Faithfulness (does the summary only state claims present in reviews?), human eval on usefulness |
| Price Comparison Agent | Data freshness (age of price at query time), accuracy vs. manual spot-check |
| FAQ/Policy Agent | Answer accuracy against a curated Q&A eval set, hallucination rate, appropriate-escalation rate |
| Orchestrator/overall | Task completion rate, end-to-end latency, session CSAT |

---

## 8. Mapping the Solution to the Stated Challenges

| Challenge | How the Design Addresses It |
|---|---|
| Limited personalization | Hybrid recommendation engine (content + collaborative + LLM re-ranking) driven by an evolving user profile, not static rules |
| Inefficient price comparison | Dedicated Price Comparison Agent with scheduled multi-source price ingestion and explicit freshness timestamps |
| Inefficient customer support | FAQ/Policy Agent grounded via RAG on the actual policy corpus, with escalation for out-of-scope queries — no more static FAQ pages |
| Review overload | Precomputed aspect-based sentiment + LLM summarization gives a 3-pro/3-con digest instead of hundreds of raw reviews |

---

## 9. Key Risks & Mitigations

- **Hallucinated policy answers** → strict RAG grounding, refusal-by-default, human audit logging.
- **Cold-start recommendations** → popularity/category fallback plus explicit preference elicitation for new users.
- **Stale price data mislabeled as "real-time"** → always show a "last checked" timestamp; set user expectations accurately.
- **Agent orchestration latency** → run independent agents in parallel where the query is compound (e.g., recommend + summarize simultaneously), cache aggressively (review summaries, price snapshots).
- **Cost at scale** → reserve expensive LLM calls for orchestration/generation; push high-volume classification (sentiment tagging) to a fine-tuned small model.

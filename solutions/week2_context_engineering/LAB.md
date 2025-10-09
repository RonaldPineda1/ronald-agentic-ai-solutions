# Week 2 Lab: Building a Mini RAG FAQ Agent

Level: Intro → Applied | Est. Time: 60–90 min core / +60 min stretch | Prereq: Completed Week 1 prompt comparisons

---
## 1. Objectives
By the end you will be able to:
1. Explain (Retrieve → Augment → Generate) using precise mental model language
2. Build a minimal Retrieval-Augmented Generation (RAG) pipeline locally (no hosted services)
3. Compare naive prompting vs RAG-augmented responses
4. Identify & log common RAG failure modes (irrelevant context, truncation, leakage)
5. Extend baseline with at least one improvement (better chunking, hybrid scoring, filtering)

---
## 2. Quick Start (TL;DR)
```bash
# 1. Ensure virtualenv from Week 1 is active
source .venv/bin/activate            # macOS/Linux
# or .venv\Scripts\activate         # Windows PowerShell

# 2. Install new deps (if not already)
pip install -r requirements.txt

# 3. Run baseline (will index if first run)
python rag_lab.py

# 4. Try modifying FAQ_DATA or top-k retrieval

# 5. Log observations in PROMPT_PLAYBOOK.md (Week 2 section)
```

---
## 3. Core Concepts Refresher
| Concept | What | Why It Matters in RAG |
|---------|------|-----------------------|
| Embedding | Vector numeric representation of text | Enables semantic similarity search |
| Vector Store (ChromaDB) | Stores (id, embedding, metadata, document) | Fast approximate nearest neighbor lookups |
| Retriever | Component that selects candidate documents | Reduces prompt token waste / hallucinations |
| Augmented Prompt | User query + selected context | Grounds generation on external facts |
| Top-k | Number of results kept | Trade-off: recall vs noise |
| Chunking | How source text is split | Affects embedding quality & relevance |

---
## 4. Architecture (Baseline)
```
User Query → Embed (Ollama) → Vector Store Query (Chroma) → Top-k Docs
      ↘------------------------------------↗
        Augmented Prompt → LLM (Ollama llama3) → Answer
```
Improvement Axis Examples: better embedding model, reranking stage, metadata filtering, caching repeated queries.

---
## 5. Baseline Walkthrough
The provided `rag_lab.py` already implements:
1. Static FAQ_DATA knowledge base
2. Chroma persistent collection initialization
3. Embedding of questions (index phase)
4. Query embedding + top-2 similarity search
5. Prompt assembly + llama3 generation

Run it once to build the index. Re-running skips indexing (checks `collection.count()`).

---
## 6. Required Enhancements (You Implement)
Add or modify code to explore and compare:
| Enhancement | Description | Acceptance Signal |
|-------------|-------------|-------------------|
| Adjustable k | Parameterize n_results (e.g. CLI arg `--k`) | Different answer quality when k=1 vs k=4 |
| Context delimiter | Wrap retrieved docs with clear separators | Model answer references sections cleanly |
| Source citation | Include which FAQ ids were used | Output contains `[faq3, faq7]` style list |
| No-context control | Allow generation without retrieval (`--no-context`) | You can diff raw vs augmented answer |

Stretch (pick 1+ later): multi-field metadata, simple rerank by answer length, duplicate suppression.

---
## 7. Step-by-Step Tasks
1. Run baseline & capture one example answer (copy into Playbook)
2. Add CLI parsing (argparse) for: `--k`, `--no-context`, `--query "..."`
3. Implement context delimiter block (e.g. `---CONTEXT BLOCK i---`)
4. Add citation list at end of answer (post-process append)
5. Compare 3 queries with and without context (log differences)
6. Increase `n_results` to 4; observe noise vs completeness
7. (Optional) Modify one FAQ answer to introduce subtle conflict → see if answer reflects stale vs updated content (cache invalidation thinking)

---
## 8. Evaluation & Logging
Track findings in `PROMPT_PLAYBOOK.md` (create Week 2 section):
| Query | Mode (raw/RAG) | k | Retrieved IDs | Strengths | Weaknesses | Failure Modes | Notes |
|-------|----------------|---|---------------|-----------|------------|---------------|-------|

### Scoring (suggested 1–5 each)
| Dimension | Definition | 1 | 5 |
|-----------|------------|---|---|
| Grounding | Uses factual retrieved content | Hallucinates | Fully cites sources |
| Relevance | Stays on user ask | Tangential | Direct & focused |
| Completeness | Covers key facts | Missing core | Fully addresses |
| Brevity | Concise & purposeful | Verbose fluff | Tight answer |
| Traceability | Clear which docs | Unclear | Explicit ids |

Failure Mode Tags: `no-hit`, `irrelevant`, `partial`, `verbose`, `leakage`, `stale`.

---
## 9. Troubleshooting
| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Empty retrieval | Index not built | Delete DB folder & re-run indexing |
| Identical answers raw vs RAG | Context unused / too small | Increase k or improve delimiter clarity |
| Slow indexing | Large FAQ or network | Reduce dataset size initially |
| Repeated docs | Duplicate IDs | Ensure unique ids on add |
| Stale answers after edit | Cached collection | Remove `chroma_db` directory |

---
## 10. Stretch Goals (Depth)
| Category | Idea | Hint |
|----------|------|------|
| Retrieval | Add simple max marginal relevance (MMR) | Penalize similarity to already selected docs |
| Hybrid | Combine lexical filter (keyword) + vector | Pre-filter by keyword before vector search |
| Chunking | Split longer text into overlaps | Use 300–500 char windows with 50 overlap |
| Rerank | Score answer length or embed answer → refine | Secondary pass selecting top 1 |
| Caching | Memoize embeddings for repeated queries | Dict keyed by text hash |
| Eval | Add latency timing per query | `time.time()` delta |

---
## 11. Deliverables
Minimum:
1. Updated `rag_lab.py` with adjustable k and no-context mode
2. Week 2 section added to `PROMPT_PLAYBOOK.md` (table + at least 3 logged query comparisons)
3. At least one citation-enabled answer example

Stretch (any 2 for extra credit): rerank attempt, hybrid filter, chunking prototype, latency metrics.

Commit Message Guideline: `week2: enhance rag_lab with k param and no-context mode`

---
## 12. Reflection Prompts
Answer (briefly) in Playbook:
- Where did additional context hurt answer quality?
- Which failure mode appeared most often?
- What is your next improvement priority & why?

---
## 13. Next Week Preview
We’ll shift from “retrieve the right text” to “invoke the right tool” using the Model Context Protocol (MCP). Start thinking about tasks requiring action, not just answers.

---
## 14. Appendix: Minimal Augmentation Snippet (Example)
```python
def format_context(docs):
    return "\n".join([f"---CONTEXT {i+1} (id={ids[i]})---\n{d}" for i, d in enumerate(docs)])

# After retrieval
ctx = format_context(results['documents'][0])
prompt = f"User: {user_query}\n\nContext:\n{ctx}\n\nAnswer (cite ids at end)."
```

---
*End of Week 2 Lab Instructions*

# Automate Internal Linking

NLP-powered engine that analyzes a set of URLs and suggests optimal internal linking opportunities between them. Uses local sentence-transformers embeddings, keyphrase extraction, entity recognition, and multi-signal scoring — no cloud LLM required.

## Architecture

```
URLs → Fetch & Extract → Profile (embed + terms + intent)
     → Candidate Graph (cosine top-K)
     → Anchor Discovery (NP + entity + keyphrase spans)
     → Score (0.35 lexical + 0.35 semantic + 0.15 context + 0.15 quality)
     → Filter (hard rules + soft penalties)
     → Select (MMR diversification, constraints)
     → Output (suggestions with insertion hints)
```

**Stack**: Python core (spaCy, sentence-transformers, BeautifulSoup) + FastAPI server + Node.js/Express API gateway

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### Install

```bash
# Python dependencies
cd python
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Node.js dependencies
cd ../node-api
npm install
```

### CLI Usage

```bash
# Analyze URLs from command line
cd python
python -m internal_linker analyze \
  --url https://example.com/page-1 \
  --url https://example.com/page-2 \
  --url https://example.com/page-3 \
  --output results.json

# From a file (one URL per line)
python -m internal_linker analyze --urls-file urls.txt --output results.json

# With options
python -m internal_linker analyze \
  --urls-file urls.txt \
  --max-links 3 \
  --format csv \
  --output results.csv \
  --verbose
```

### API Usage

```bash
# Start Python engine
cd python
uvicorn internal_linker.api.server:app --port 8000

# Start Node.js gateway (in another terminal)
cd node-api
npm run dev

# Submit analysis
curl -X POST http://localhost:3000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/a", "https://example.com/b", "https://example.com/c"]}'

# Poll for results
curl http://localhost:3000/api/results/{job_id}
```

## Configuration

Create a YAML config file:

```yaml
# config.yaml
fetch_timeout_seconds: 30
fetch_max_concurrent: 10
embedding_model: "all-MiniLM-L6-v2"
top_k_targets_per_source: 20
near_duplicate_threshold: 0.92
score_threshold: 0.62
max_suggestions_per_source: 5
mmr_lambda: 0.75
site_rules:
  max_links_per_source_page: 5
  max_links_per_target_page: 20
  anchor_length_min_words: 2
  anchor_length_max_words: 6
  avoid_sections:
    - "Related Posts"
    - "nav"
    - "footer"
  existing_link_policy: "skip"
```

```bash
python -m internal_linker analyze --urls-file urls.txt --config config.yaml
```

## Output Format

Each suggestion includes:

```json
{
  "source_url": "https://example.com/seo-guide",
  "target_url": "https://example.com/keyword-research",
  "anchor_text": "keyword research strategy",
  "anchor_variants": [],
  "context_snippet": "A solid [keyword research strategy] helps you identify...",
  "match_reason": "strong lexical match, high semantic similarity",
  "confidence_score": 0.78,
  "risk_flags": [],
  "scores": {
    "lexical": 0.82,
    "semantic": 0.75,
    "context": 0.70,
    "quality": 0.85
  },
  "insertion_hint": {
    "paragraph_index": 3,
    "sentence_index": 1,
    "anchor_start": 8,
    "anchor_end": 35,
    "dom_path": "article.post-content > p"
  }
}
```

## Pipeline Steps

| Step | Module | Description |
|------|--------|-------------|
| A | `fetcher.py` | Fetch HTML, extract clean content (readability), parse paragraphs/sentences/links |
| B | `profiler.py` | Compute embeddings, extract target terms (RAKE + NP + NER + n-grams), classify intent |
| C | `candidate_graph.py` | Build doc-to-doc similarity graph, top-K targets per source |
| D | `anchor_discovery.py` | Find linkable phrases in source, score against each target |
| E | `selector.py` | MMR diversification, apply constraints (max links, uniqueness, orphan boost) |
| F+G | `filters.py` | Hard rejection rules + soft scoring penalties |
| H | `pointer.py` | Generate insertion hints with DOM paths and context snippets |

## Scoring Formula

```
combined = 0.35 * lexical + 0.35 * semantic + 0.15 * context + 0.15 * quality
```

- **Lexical**: BM25 + Jaccard + token overlap against target terms/title/headings
- **Semantic**: Cosine similarity between anchor context embedding and target doc embedding
- **Context**: Position quality (mid-body preferred), sentence length, boilerplate detection
- **Quality**: Anchor text length (2-6 words sweet spot), genericness, punctuation ratio

## Project Structure

```
automate-internal-linking/
├── python/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── src/internal_linker/
│       ├── cli.py                  # Click CLI
│       ├── config.py               # Pydantic config models
│       ├── types.py                # Core data types
│       ├── pipeline/
│       │   ├── orchestrator.py     # Runs Steps A→H
│       │   ├── fetcher.py          # Step A
│       │   ├── profiler.py         # Step B
│       │   ├── candidate_graph.py  # Step C
│       │   ├── anchor_discovery.py # Step D
│       │   ├── selector.py         # Step E
│       │   ├── filters.py          # Steps F+G
│       │   └── pointer.py          # Step H
│       ├── nlp/
│       │   ├── embeddings.py       # sentence-transformers
│       │   ├── keyphrase.py        # RAKE extraction
│       │   ├── entities.py         # spaCy NER
│       │   ├── noun_phrases.py     # spaCy NP chunking
│       │   └── intent.py           # Rule-based intent classification
│       ├── scoring/
│       │   ├── lexical.py          # BM25 + Jaccard
│       │   ├── semantic.py         # Cosine similarity
│       │   ├── context.py          # Position scoring
│       │   ├── quality.py          # Anchor quality
│       │   └── combined.py         # Weighted ensemble
│       └── api/
│           └── server.py           # FastAPI server
└── node-api/
    ├── package.json
    └── src/
        ├── index.ts                # Express server
        ├── types.ts                # TypeScript interfaces
        ├── routes/                 # API routes
        └── services/               # Python engine client
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit URLs for analysis, returns job_id |
| `GET` | `/api/results/:jobId` | Poll for job status and results |
| `GET` | `/api/health` | Health check (both Node + Python) |
| `GET` | `/api/jobs` | List all jobs (Python API only) |

## License

MIT

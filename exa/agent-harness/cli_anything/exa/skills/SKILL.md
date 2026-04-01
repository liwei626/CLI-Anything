# Exa CLI Skill

## Identity
- **Name**: cli-anything-exa
- **Version**: 1.0.0
- **Category**: search
- **Entry Point**: `cli-anything-exa`

## What This CLI Does
Provides an agent-native command-line interface to the Exa API — a neural search engine
optimised for AI agent workflows. Supports web search across multiple modes (fast, deep,
deep-reasoning), finding similar pages, fetching full-text or highlighted page contents,
and getting LLM-synthesised answers with cited sources.

## Prerequisites
- Python >= 3.10
- `pip install cli-anything-exa`
- `export EXA_API_KEY="your-api-key"` (get one at https://dashboard.exa.ai/api-keys)

## Installation
```bash
pip install git+https://github.com/HKUDS/CLI-Anything.git#subdirectory=exa/agent-harness
```

## Command Reference

### search — Web search
```bash
cli-anything-exa search "<query>" [OPTIONS]

Options:
  --type       auto|fast|instant|deep|deep-reasoning  (default: auto)
  --num-results / -n   1–100  (default: 10)
  --category   company|people|research-paper|news|personal-site|financial-report
  --content    highlights|text|summary|none  (default: highlights)
  --freshness  smart|always|never  (default: smart)
  --include-domains DOMAIN   (repeatable)
  --exclude-domains DOMAIN   (repeatable)
  --from DATE   ISO 8601 start published date
  --to   DATE   ISO 8601 end published date
  --location CC  Two-letter country code for geo-bias
```

### similar — Find similar pages
```bash
cli-anything-exa similar "<url>" [--num-results N] [--content highlights|text|summary|none]
```

### contents — Fetch page contents
```bash
cli-anything-exa contents <url> [url ...] [--content text|highlights|summary] [--freshness smart|always|never]
```

### answer — LLM-synthesised answer with citations
```bash
cli-anything-exa answer "<question>"
```

### server status — Verify API key and connectivity
```bash
cli-anything-exa server status
```

### session — Inspect current REPL session
```bash
cli-anything-exa session status
cli-anything-exa session history
```

## JSON Output
All commands support `--json` at the root level for machine-readable output:
```bash
cli-anything-exa --json search "latest LLM papers" --num-results 5
```

## Common Agent Patterns

### Fast keyword lookup
```bash
cli-anything-exa --json search "site:arxiv.org transformer architectures" --type fast --content highlights
```

### Deep research on a topic
```bash
cli-anything-exa --json search "EU AI Act compliance requirements 2024" --type deep --content text
```

### Academic paper discovery
```bash
cli-anything-exa --json search "retrieval augmented generation" --category research-paper --num-results 20
```

### Company intelligence
```bash
cli-anything-exa --json search "Anthropic funding history" --category company
```

### News monitoring
```bash
cli-anything-exa --json search "AI regulation news" --category news --from 2024-01-01
```

### Find related resources
```bash
cli-anything-exa --json similar https://arxiv.org/abs/2303.08774 --num-results 10
```

### Fetch full content for summarisation
```bash
cli-anything-exa --json contents https://example.com/article --content text
```

### Quick factual answer
```bash
cli-anything-exa --json answer "What is the context window of Claude 3.5 Sonnet?"
```

## Interactive REPL
```bash
cli-anything-exa   # No subcommand → enters REPL
```
Type commands without the `cli-anything-exa` prefix. Type `exit` or `quit` to leave.

## Notes
- `highlights` content mode is 10× more token-efficient than `text` — prefer it for agent pipelines
- `--type deep` triggers multi-step reasoning; slower but synthesises across many sources
- `--category company` and `--category people` do not support date or domain-exclude filters
- Cost per query is included in JSON output under `cost_dollars`

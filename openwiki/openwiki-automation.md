---
type: "Reference"
title: "OpenWiki Automation — CI/CD Workflow, Skills, Secrets"
description: "OpenWiki automated wiki generation: GitHub Actions workflow, required secrets (OPENROUTER_API_KEY, OPENWIKI_LANGSMITH_API_KEY, LANGSMITH_API_KEY), skills configuration (mermaid-diagrams, write-connector), mermaid diagram validation."
tags: ["openwiki", "automation", "ci-cd", "github-actions", "secrets", "skills", "mermaid"]
---

# OpenWiki Automation — CI/CD Workflow, Skills, Secrets

## GitHub Actions Workflow

**File**: `.github/workflows/openwiki-update.yml`

### Workflow Triggers
- **Scheduled**: Runs periodically (cron schedule)
- **Manual**: `workflow_dispatch` for on-demand runs
- **On push**: When source files change (optional)

### Required Secrets

| Secret | Purpose | Required |
|--------|---------|----------|
| `OPENROUTER_API_KEY` | LLM API for wiki generation (OpenRouter) | Yes |
| `OPENWIKI_LANGSMITH_API_KEY` | LangSmith tracing for OpenWiki runs | Yes |
| `LANGSMITH_API_KEY` | LangSmith API key (general) | Yes |

### Workflow Steps (Typical)
1. **Checkout** — Full history (`fetch-depth: 0` required for git analysis)
2. **Setup Python** — Python 3.13
3. **Install OpenWiki** — `pip install openwiki` or from source
4. **Run OpenWiki** — Generate/update wiki from source
5. **Validate Mermaid** — Check diagram syntax
6. **Create PR** — Commit changes, open PR for review

### Fetch Depth Requirement

The workflow **must use `fetch-depth: 0`** because:
- Repository has `.git` but **no commits** (initialized but empty history)
- OpenWiki may analyze git history for change detection
- Shallow clone (`fetch-depth: 1`) would fail on empty history

## Skills Configuration

### `/skills/mermaid-diagrams/`

**File**: `SKILL.md`

**Purpose**: Embed Mermaid diagrams in generated wiki pages for:
- Runtime flows
- Call sequences
- State machines/lifecycles
- Data models/entity relationships
- Non-trivial control flow

**Usage**: When documenting significant runtime flows, call sequences, state machines, data models, or complex control flow.

### `/skills/write-connector/`

**File**: `SKILL.md`

**Purpose**: Add new built-in OpenWiki source connectors.

**Usage**: When a user asks to create or implement an OpenWiki connector.

## Mermaid Diagram Validation

The workflow includes mermaid diagram validation:
- Checks syntax of all `mermaid` code fences in wiki pages
- Fails build on invalid diagrams
- Uses mermaid-cli or similar for validation

**Common diagram types in this wiki**:
- `flowchart` — Pipeline architecture, data flow
- `sequenceDiagram` — Node interaction sequences
- `stateDiagram-v2` — LangGraph state transitions
- `erDiagram` — Data model relationships

## Local Development

To run OpenWiki locally (for testing wiki changes):

```bash
# Install OpenWiki (if published)
pip install openwiki

# Or run from source
git clone https://github.com/openwiki/openwiki
cd openwiki
pip install -e .

# Run on this repo
openwiki generate --repo . --output ./openwiki
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Workflow fails on checkout | `fetch-depth: 1` on empty repo | Use `fetch-depth: 0` |
| Mermaid validation fails | Invalid diagram syntax | Fix diagram in source page |
| LLM generation fails | Missing/invalid `OPENROUTER_API_KEY` | Add valid secret |
| LangSmith tracing fails | Missing `LANGSMITH_API_KEY` | Add valid secret |
| No changes detected | OpenWiki cache | Force rebuild or clear cache |

## Related Pages

- [Configuration](/openwiki/configuration.md) — Environment setup
- [Architecture Overview](/openwiki/architecture/overview.md) — System diagram (uses mermaid)
- [Graph Composition](/openwiki/architecture/graph.md) — State machine diagram
- [State Schema](/openwiki/architecture/state-schema.md) — Data model diagram
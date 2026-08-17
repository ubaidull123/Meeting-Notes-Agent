---
type: "Component"
title: "Database — PostgresCheckpoint (Not Implemented)"
description: "PostgresCheckpoint stub: empty postgresdb.py file (0 bytes), no checkpoint implementation, no database integration in graph."
tags: ["component", "database", "postgres", "checkpoint", "langgraph", "not-implemented"]
---

# Database — PostgresCheckpoint (Not Implemented)

## Current State

**File**: `meeting_notes_agent/src/database/postgresdb.py`

**Size**: 0 bytes (empty file)

**Content**: None

## What Should Be Here

For LangGraph persistence, a PostgresCheckpoint would typically provide:

```python
# Expected interface (not implemented)
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# Connection pool
pool = ConnectionPool(
    conninfo="postgresql://user:pass@host:5432/db",
    max_size=10,
    kwargs={"autocommit": True},
)

# Checkpoint saver
checkpointer = PostgresSaver(pool)
checkpointer.setup()  # Creates tables

# Graph compilation with checkpointer
app = graph.compile(checkpointer=checkpointer)

# Usage
config = {"configurable": {"thread_id": "meeting-123"}}
result = app.invoke(state, config=config)
# State automatically saved to Postgres
```

## Why It Matters

| Feature | Without Checkpointer | With Checkpointer |
|---------|---------------------|-------------------|
| State persistence | Lost after execution | Saved to DB |
| Resume interrupted runs | ❌ | ✅ |
| Human-in-the-loop pauses | ❌ | ✅ |
| Audit trail | ❌ | ✅ |
| Multi-turn conversations | ❌ | ✅ |

## Current Graph Compilation (No Checkpointer)

**File**: `src/graph.py`

```python
if __name__ == "__main__":
    app = graph.compile()  # No checkpointer
    print("Graph compiled successfully")
```

## Integration Point (When Implemented)

```python
# In graph.py or separate module
from meeting_notes_agent.src.database.postgresdb import get_checkpointer

def build_graph():
    # ... existing code ...
    return graph

# With checkpointer
app = build_graph().compile(checkpointer=get_checkpointer())
```

## Required Implementation

If Postgres checkpoint is needed:

1. **Add dependencies** to `pyproject.toml`:
   ```toml
   dependencies = [
       # ... existing ...
       "langgraph-checkpoint-postgres>=1.0.0",
       "psycopg[pool]>=3.1.0",
   ]
   ```

2. **Implement `postgresdb.py`**:
   ```python
   from langgraph.checkpoint.postgres import PostgresSaver
   from psycopg_pool import ConnectionPool
   import os

   _pool = None
   _checkpointer = None

   def get_pool():
       global _pool
       if _pool is None:
           database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/meetings")
           _pool = ConnectionPool(
               conninfo=database_url,
               max_size=10,
               kwargs={"autocommit": True},
           )
       return _pool

   def get_checkpointer():
       global _checkpointer
       if _checkpointer is None:
           _checkpointer = PostgresSaver(get_pool())
           _checkpointer.setup()
       return _checkpointer
   ```

3. **Add environment variable**:
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/db
   ```

## Alternatives (Simpler)

| Option | Library | Use Case |
|--------|---------|----------|
| SQLite | `langgraph-checkpoint-sqlite` | Local dev, single-user |
| In-memory | `MemorySaver()` (built-in) | Testing, ephemeral |
| Redis | `langgraph-checkpoint-redis` | Distributed, ephemeral |
| Postgres | `langgraph-checkpoint-postgres` | Production, persistent |

## Current Blockers

1. **Empty file** — No code to import
2. **No dependencies** — `langgraph-checkpoint-postgres` not in `pyproject.toml`
3. **No DATABASE_URL** — Not in `.env`
4. **Graph doesn't use checkpointer** — `compile()` called without argument

## Related Pages

- [Graph Composition](/openwiki/architecture/graph.md) — Current compile() without checkpointer
- [Configuration](/openwiki/configuration.md) — Dependencies, environment
- [Architecture Overview](/openwiki/architecture/overview.md) — Missing persistence layer
- [README Aspiration Gap](/openwiki/README-aspiration.md) — Step 13: Save Record
---
type: "Component"
title: "LLM Providers — Groq, OpenAI, OpenRouter, HuggingFace Factories"
description: "LLM client factories for Groq, OpenAI, OpenRouter, and HuggingFace. Critical issues: invalid model names (empty string, non-existent gpt-5.6-luna), HF Whisper eager loading + inference at import time, unused local models, empty Ollama directory."
tags: ["component", "llm", "groq", "openai", "openrouter", "huggingface", "whisper", "factory", "provider"]
---

# LLM Providers — Groq, OpenAI, OpenRouter, HuggingFace Factories

## Provider Overview

| Provider | Factory File | Models | Status |
|----------|--------------|--------|--------|
| **Groq** | `src/llms/API_Based/groq.py` | LLM + Whisper | ❌ Invalid model names |
| **OpenAI** | `src/llms/API_Based/openai.py` | LLM + Whisper | ❌ Invalid model name |
| **OpenRouter** | `src/llms/API_Based/openrouter.py` | LLM + Whisper | ❌ Invalid model names |
| **HuggingFace** | `src/llms/Local/hf/whisper.py` | Local Whisper | ⚠️ Eager load + inference at import |

## Groq Provider

**File**: `src/llms/API_Based/groq.py`

```python
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(override=True)

def get_groq_llm():
    """Returns a Groq LLM instance for use in the meeting notes agent."""
    return ChatGroq(model="")  # INVALID: empty string

def get_groq_whisper_llm():
    """Returns a Groq Whisper LLM instance for use in the meeting notes agent."""
    return ChatGroq(model="whisper")  # QUESTIONABLE: likely invalid
```

### Issues

| Function | Model | Problem |
|----------|-------|---------|
| `get_groq_llm()` | `""` (empty) | Will fail — no model specified |
| `get_groq_whisper_llm()` | `"whisper"` | Groq uses `whisper-large-v3` or `whisper-large-v3-turbo` |

### Valid Groq Models (2024)
- `llama-3.1-70b-versatile`
- `llama-3.1-8b-instant`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`
- `whisper-large-v3` (Whisper)
- `whisper-large-v3-turbo` (Whisper)

### Used By
- `TranscribeAudio` node → `get_groq_whisper_llm()`

### Required Fix
```python
def get_groq_llm():
    return ChatGroq(model="llama-3.1-8b-instant")

def get_groq_whisper_llm():
    return ChatGroq(model="whisper-large-v3")
```

### Environment
```bash
GROQ_API_KEY=your_groq_api_key
```

## OpenAI Provider

**File**: `src/llms/API_Based/openai.py`

```python
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

def get_openai_llm():
    """Returns an OpenAI LLM instance for use in the meeting notes agent."""
    return ChatOpenAI(model="gpt-5.6-luna")  # INVALID: does not exist

def get_openai_whisper_llm():
    """Returns an OpenAI Whisper LLM instance for use in the meeting notes agent."""
    return ChatOpenAI(model="whisper-large-v3")  # Valid model name
```

### Issues

| Function | Model | Problem |
|----------|-------|---------|
| `get_openai_llm()` | `"gpt-5.6-luna"` | **Model does not exist** |
| `get_openai_whisper_llm()` | `"whisper-large-v3"` | Valid but not used |

### Valid OpenAI Models (2024)
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`
- `whisper-1` (Whisper API)

### Used By
- `CleanTranscript` node → `get_openai_llm()`
- `Summarize` node (orphaned) → `get_openai_llm()`

### Required Fix
```python
def get_openai_llm():
    return ChatOpenAI(model="gpt-4o-mini")  # or gpt-4o, gpt-3.5-turbo
```

### Environment
```bash
OPENAI_API_KEY=your_openai_api_key
```

## OpenRouter Provider

**File**: `src/llms/API_Based/openrouter.py`

```python
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv(override=True)

def get_openrouter_llm():
    """Returns an OpenRouter LLM instance for use in the meeting notes agent."""
    return ChatOpenRouter(model="gpt-5.6-luna")  # INVALID

def get_openrouter_whisper_llm():
    """Returns an OpenRouter Whisper LLM instance for use in the meeting notes agent."""
    return ChatOpenRouter(model="whisper-large-v3")  # May work via OpenRouter
```

### Issues
Same invalid model names as OpenAI.

### Used By
**Not used by any node currently.**

### Environment
```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```

## HuggingFace Local Whisper

**File**: `src/llms/Local/hf/whisper.py`

```python
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from langchain_community.llms import HuggingFacePipeline

# Model ID
model_id = "openai/whisper-large-v3"

# Device setup
device = "cuda:0" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load model + processor — AT IMPORT TIME
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

# Create HF pipeline — AT IMPORT TIME
asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device=0 if device.startswith("cuda") else -1,
    chunk_length_s=30,
    return_timestamps=True,
)

# Wrap in LangChain — AT IMPORT TIME
llm = HuggingFacePipeline(pipeline=asr_pipeline)

# RUN INFERENCE AT IMPORT TIME — HARDCODED PATH
result = llm.invoke("path/to/audio.wav")

print(result)
```

### Critical Problems

| Problem | Impact |
|---------|--------|
| **Model loading at import** | ~3GB download, GPU/CPU memory allocation on `import` |
| **Pipeline creation at import** | Heavy computation on `import` |
| **Inference at import** | `llm.invoke("path/to/audio.wav")` runs immediately |
| **Hardcoded path** | `"path/to/audio.wav"` — almost certainly doesn't exist |
| **Unused by graph** | `TranscribeAudio` uses Groq Whisper, not this |

### Why This Breaks Everything
```python
# Any import triggers the full pipeline:
from meeting_notes_agent.src.llms.Local.hf.whisper import llm
# ↓
# Downloads model (first time)
# Loads to GPU/CPU
# Creates pipeline
# Runs inference on non-existent file
# Prints result
```

### Used By
**No node uses this.** `TranscribeAudio` imports from `groq.py` only.

### Required Fix (If Local Whisper Needed)
```python
# whisper.py — LAZY LOADING PATTERN
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from langchain_community.llms import HuggingFacePipeline

_model = None
_processor = None
_pipeline = None
_llm = None

def get_hf_whisper_llm():
    """Lazy-loaded HuggingFace Whisper LLM."""
    global _model, _processor, _pipeline, _llm
    
    if _llm is not None:
        return _llm
    
    model_id = "openai/whisper-large-v3"
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    _model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True
    ).to(device)
    
    _processor = AutoProcessor.from_pretrained(model_id)
    
    _pipeline = pipeline(
        "automatic-speech-recognition",
        model=_model,
        tokenizer=_processor.tokenizer,
        feature_extractor=_processor.feature_extractor,
        device=0 if device.startswith("cuda") else -1,
        chunk_length_s=30,
        return_timestamps=True,
    )
    
    _llm = HuggingFacePipeline(pipeline=_pipeline)
    return _llm

# NO module-level execution
```

### Environment
```bash
# No API key needed (local)
# Requires: torch, transformers, accelerate
# Optional: CUDA for GPU acceleration
```

## Ollama Directory

**Path**: `src/llms/Local/ollama/`

**Status**: **Empty directory** (placeholder)

No files, no implementation.

## Provider Usage Summary

```mermaid
flowchart LR
    subgraph "Used in Graph"
        Transcribe[TranscribeAudio Node] --> GroqWhisper[Groq Whisper\nget_groq_whisper_llm()]
        Clean[CleanTranscript Node] --> OpenAILLM[OpenAI LLM\nget_openai_llm()]
    end
    
    subgraph "Orphaned Node"
        Summarize[Summarize Node] --> OpenAILLM2[OpenAI LLM\nget_openai_llm()]
    end
    
    subgraph "Unused"
        HF[HF Whisper\nEager load at import]
        OpenRouter[OpenRouter LLM/Whisper]
        Ollama[Ollama\nEmpty dir]
    end
    
    style HF fill:#ffcdd2
    style OpenRouter fill:#fff3e0
    style Ollama fill:#fff3e0
```

## Required Fixes for Execution

| Fix | File | Priority |
|-----|------|----------|
| Fix Groq model: `model=""` → `model="llama-3.1-8b-instant"` | `groq.py` | Critical |
| Fix Groq Whisper: `model="whisper"` → `model="whisper-large-v3"` | `groq.py` | Critical |
| Fix OpenAI model: `model="gpt-5.6-luna"` → `model="gpt-4o-mini"` | `openai.py` | Critical |
| Fix OpenRouter models (if used) | `openrouter.py` | Medium |
| Remove eager loading from HF Whisper | `whisper.py` | Critical (breaks imports) |
| Add API keys to `.env` | `.env` | Critical |
| Consider removing unused providers | — | Cleanup |

## Environment Variables Needed

```bash
# .env (currently empty)
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key  # if used
# HF local: no key needed, but heavy deps
```

## Related Pages

- [Transcribe Node](/openwiki/architecture/nodes/transcribe.md) — Uses Groq Whisper
- [Clean Node](/openwiki/architecture/nodes/clean.md) — Uses OpenAI LLM
- [Summarize Node](/openwiki/architecture/nodes/summarize.md) — Uses OpenAI LLM (orphaned)
- [Configuration](/openwiki/configuration.md) — Environment setup
- [Architecture Overview](/openwiki/architecture/overview.md) — Provider integration
---
okf_version: "0.1"
---

# Files

- [Quickstart — Meeting Notes Agent Wiki](quickstart.md) - **START HERE**: High-level map, key concepts, task routing table, and navigation guide for understanding the 3-node LangGraph pipeline and its gaps vs. the 13-step README plan.
- [OpenWiki Skeleton — meeting-notes-agent](_skeleton.md)
- [Configuration — Environment, Packaging, Dependencies, Entrypoint](configuration.md) - Project configuration: pyproject.toml packaging, misconfigured CLI entrypoint (meeting_notes_agent:main doesn't exist), requirements.txt typo (langchain-comunity), empty .env file, dependency versions.
- [OpenWiki Automation — CI/CD Workflow, Skills, Secrets](openwiki-automation.md) - OpenWiki automated wiki generation: GitHub Actions workflow, required secrets (OPENROUTER_API_KEY, OPENWIKI_LANGSMITH_API_KEY, LANGSMITH_API_KEY), skills configuration (mermaid-diagrams, write-connector), mermaid diagram validation.
- [README Aspiration Gap — Planned vs Implemented](README-aspiration.md) - Gap analysis between README's 13-step pipeline plan and actual implementation: 3 working nodes, 1 orphaned broken node, 9 steps with zero code.
- [Testing — No Tests Exist, Verification Approach](testing.md) - No test files exist in the repository. Graph is non-executable without API keys. Nodes are untestable without LLM credentials. Recommended testing approach for future development.

# Directories

- [architecture](architecture/)
- [components](components/)

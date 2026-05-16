# Nexla MCP Assignment

This repository contains a local-only MCP server for grounded question answering over a small PDF corpus. The implementation is intentionally free to run: no paid LLM API, no hosted vector database, and no external parsing service.

## Summary

The server ingests every PDF in `data/`, chunks the extracted text, builds a lightweight in-memory BM25-style index, and exposes an MCP tool that answers natural-language questions with source citations.

Key choices:
- `pypdf` for PDF extraction
- official Python `mcp` SDK with FastMCP for the server
- in-repo lexical retrieval instead of embeddings or external vector storage
- extractive, citation-first answers instead of generative rewriting

This keeps the project reproducible, easy to run locally, and unlikely to fail due to billing, rate limits, or missing cloud setup.

## Repository Structure

- [src/nexla_mcp/server.py](/Users/bharathreddy/Nexla/src/nexla_mcp/server.py): FastMCP server and tool definitions
- [src/nexla_mcp/indexer.py](/Users/bharathreddy/Nexla/src/nexla_mcp/indexer.py): PDF ingestion, chunking, ranking, and answer assembly
- [src/nexla_mcp/smoke_test.py](/Users/bharathreddy/Nexla/src/nexla_mcp/smoke_test.py): end-to-end verification using the MCP client SDK
- [example_interactions.md](/Users/bharathreddy/Nexla/example_interactions.md): captured sample queries and responses
- [mcp_server_config.example.json](/Users/bharathreddy/Nexla/mcp_server_config.example.json): example MCP client configuration

## Architecture Overview

The system has three stages:

1. Ingestion
   Loads each PDF in `data/`, extracts page text with `pypdf`, and creates overlapping text chunks.

2. Retrieval
   Tokenizes chunks and builds simple BM25-style statistics in memory. At query time, the system ranks chunks by lexical overlap with the user’s question.

3. Grounded answer construction
   Selects short passages from the top-ranked chunks and returns them with `document_name`, `page_number`, and supporting snippets.

The design favors transparency over sophistication: every answer is directly traceable to retrieved source text.

## Setup

1. Create and activate a local virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the project.

```bash
python -m pip install -e .
```

3. Put only the target 4-5 PDFs in `data/`.

The server indexes every `.pdf` file in that folder, so unrelated PDFs should not be present there.

## Run The Server

Start the MCP server over stdio:

```bash
PYTHONPATH=src python -m nexla_mcp.server
```

You can also use the installed entrypoint:

```bash
PYTHONPATH=src nexla-mcp-server
```

## Verify It Works

Run the end-to-end smoke test:

```bash
PYTHONPATH=src python -m nexla_mcp.smoke_test
```

Successful output should include:
- the three MCP tools
- the indexed PDF filenames
- a grounded answer with citations
- `SMOKE TEST PASSED`

To test a custom question:

```bash
SMOKE_TEST_QUESTION="Which document mentions Bucha, Ukraine and the Stanislavchuk family?" PYTHONPATH=src python -m nexla_mcp.smoke_test
```

## MCP Client Config

An example config is included at [mcp_server_config.example.json](/Users/bharathreddy/Nexla/mcp_server_config.example.json).

It uses:
- command: `python3`
- args: `-m nexla_mcp.server`
- env: `PYTHONPATH=src`

## Tool Documentation

### `list_documents`

Returns:
- the PDF directory being indexed
- the list of indexed PDFs
- the total chunk count

### `reload_documents`

Rebuilds the in-memory index from the PDFs currently present in `data/`.

### `query_documents`

Inputs:
- `question: str`
- `top_k: int = 5`
- `max_sentences: int = 3`

Output:
- `answer`: grounded extractive answer
- `citations`: supporting references with `document_name`, `page_number`, and `snippet`
- `matched_chunks`: top retrieval hits used for debugging and inspection

Example request:

```json
{
  "question": "Which document mentions Gaza and which document mentions congestion pricing?",
  "top_k": 4,
  "max_sentences": 2
}
```

## Example Interaction Log

See [example_interactions.md](/Users/bharathreddy/Nexla/example_interactions.md) for captured interactions against the PDFs currently in `data/`.

## Trade-Offs And Limitations

- The current corpus is OCR-heavy, so some extracted text is noisy.
- The system uses lexical retrieval rather than embeddings, which keeps it free and simple but can miss semantic matches.
- Answers are intentionally extractive; they prioritize citation quality and reproducibility over fluency.

Given the assignment scope, I chose a design that is easy to explain, easy to run locally, and robust without external dependencies.

## Vibe Coding Notes

AI tooling used:
- Codex in the terminal for scaffolding, refactoring, verification, and README iteration

How I used AI:
- to generate the MCP project skeleton quickly
- to iterate on retrieval and verification workflows
- to accelerate documentation and repo cleanup

Where I overrode AI:
- choosing a fully local architecture instead of embedding APIs or hosted vector stores
- simplifying the design to match the assignment time box
- tightening verification and documentation for reproducibility

My view on AI in software engineering:
- AI is most valuable as an implementation accelerator and review partner
- architectural trade-offs, debugging judgment, and final quality control still benefit from deliberate human ownership

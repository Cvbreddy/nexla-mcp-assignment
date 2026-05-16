from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from nexla_mcp.indexer import DocumentIndex

PDF_DIR = Path(os.environ.get("PDF_DIR", "data")).resolve()
INDEX = DocumentIndex(PDF_DIR)
INDEX.build()

mcp = FastMCP("Nexla PDF QA", json_response=True)


@mcp.tool()
def list_documents() -> dict:
    """List the PDFs currently indexed by the server."""
    return {
        "pdf_directory": str(PDF_DIR),
        "indexed_documents": INDEX.documents,
        "chunk_count": len(INDEX.chunks),
    }


@mcp.tool()
def reload_documents() -> dict:
    """Rebuild the PDF index from disk without restarting the server."""
    INDEX.reload()
    return {
        "pdf_directory": str(PDF_DIR),
        "indexed_documents": INDEX.documents,
        "chunk_count": len(INDEX.chunks),
    }


@mcp.tool()
def query_documents(question: str, top_k: int = 5, max_sentences: int = 3) -> dict:
    """Answer a natural-language question using the indexed PDFs and return citations."""
    if not INDEX.is_ready:
        return {
            "answer": "No PDFs are indexed yet. Add the provided PDFs to the data directory and call reload_documents.",
            "citations": [],
            "matched_chunks": [],
        }
    return INDEX.answer(question=question, top_k=top_k, max_sentences=max_sentences)


def main() -> None:
    """Run the MCP server over stdio for local MCP clients."""
    mcp.run()


if __name__ == "__main__":
    main()

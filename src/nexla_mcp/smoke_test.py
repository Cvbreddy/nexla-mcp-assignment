from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


def _parse_json_content(result_name: str, content: list[TextContent]) -> dict:
    if not content or not isinstance(content[0], TextContent):
        raise RuntimeError(f"{result_name} returned no text content")
    return json.loads(content[0].text)


async def run() -> None:
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "nexla_mcp.server"],
        env={**os.environ, "PYTHONPATH": "src"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print("TOOLS:", tool_names)
            expected_tools = {"list_documents", "reload_documents", "query_documents"}
            missing_tools = expected_tools - set(tool_names)
            if missing_tools:
                raise RuntimeError(f"Missing MCP tools: {sorted(missing_tools)}")

            docs = await session.call_tool("list_documents", {})
            docs_payload = _parse_json_content("list_documents", docs.content)
            print("DOCUMENTS:", json.dumps(docs_payload, indent=2))
            if not docs_payload.get("indexed_documents"):
                raise RuntimeError("No PDFs are indexed in data/")

            question = os.environ.get(
                "SMOKE_TEST_QUESTION",
                "Which document mentions Gaza and which document mentions congestion pricing?",
            )
            result = await session.call_tool(
                "query_documents",
                {
                    "question": question,
                    "top_k": 4,
                    "max_sentences": 2,
                },
            )
            answer_payload = _parse_json_content("query_documents", result.content)
            print("QUESTION:", question)
            print("ANSWER:", json.dumps(answer_payload, indent=2))

            citations = answer_payload.get("citations", [])
            answer_text = answer_payload.get("answer", "").strip()
            if not answer_text:
                raise RuntimeError("query_documents returned an empty answer")
            if not citations:
                raise RuntimeError("query_documents returned no citations")

            print("SMOKE TEST PASSED")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

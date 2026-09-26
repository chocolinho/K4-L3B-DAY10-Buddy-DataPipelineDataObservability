from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain.tools import tool

from core.config import Settings, normalized_provider
from retrieval.index import LocalEmbeddingIndex
from retrieval.llm import build_llm


class MockPaperAgent:
    """Local deterministic agent used for offline demos without an API key."""

    def __init__(self, settings: Settings, index: LocalEmbeddingIndex):
        self.settings = settings
        self.index = index

    def invoke(self, payload: dict[str, Any]) -> dict[str, list[AIMessage]]:
        messages = payload.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="No question was provided.")]}
        last_message = messages[-1]
        if isinstance(last_message, dict):
            question = str(last_message.get("content", ""))
        else:
            question = str(getattr(last_message, "content", last_message))

        results = self.index.search(question, top_k=self.settings.top_k)
        if not results:
            answer = "I don't know from the indexed corpus."
        else:
            lines = ["Offline mock retrieval results:"]
            for result in results:
                lines.append(
                    f"- {result.title} (paper_id={result.paper_id}, score={result.score:.4f})"
                )
            answer = "\n".join(lines)
        return {"messages": [AIMessage(content=answer)]}


def build_agent(settings: Settings, index: LocalEmbeddingIndex):
    if normalized_provider(settings) == "mock":
        return MockPaperAgent(settings, index)

    @tool
    def semantic_search_papers(query: str, top_k: int = 4) -> str:
        """Search the local paper corpus with embeddings and return the most relevant papers."""
        results = index.search(query, top_k=top_k)
        lines = []
        for result in results:
            lines.append(
                f"paper_id: {result.paper_id}\n"
                f"title: {result.title}\n"
                f"score: {result.score:.4f}\n"
                f"{result.content}"
            )
        return "\n\n".join(lines)

    @tool
    def lookup_paper(paper_id_or_title: str) -> str:
        """Look up a paper by exact paper_id or exact title from the local corpus."""
        record = index.lookup(paper_id_or_title)
        if not record:
            return "No exact paper match found."
        return (
            f"paper_id: {record['paper_id']}\n"
            f"title: {record['title']}\n"
            f"{record['content']}"
        )

    llm = build_llm(settings=settings, temperature=0.0)
    return create_agent(
        model=llm,
        tools=[semantic_search_papers, lookup_paper],
        system_prompt=(
            "You answer questions about the indexed scholarly paper corpus sourced from Crossref. "
            "Use tools before answering factual questions. "
            "If the indexed corpus does not support the answer, say so clearly."
        ),
        name="paper_corpus_agent",
    )


def run_agent_question(agent: Any, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    final_message = messages[-1]
    return getattr(final_message, "content", str(final_message))

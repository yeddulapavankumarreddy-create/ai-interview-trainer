"""
RAG Service — Retrieval-Augmented Generation
---------------------------------------------
Implements a lightweight vector similarity search using TF-IDF cosine similarity.
No external vector database required for local development.

The knowledge base consists of structured text documents stored in
/knowledge_base/**/*.txt|.json files.

Flow:
  1. Load and index knowledge base documents (once, on startup)
  2. Build TF-IDF vectors for all chunks
  3. Given a query (profile + role + skills), retrieve top-k relevant chunks
  4. Return retrieved context string for use in Granite prompts
"""

import os
import json
import math
import logging
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = os.getenv(
    "KNOWLEDGE_BASE_DIR",
    str(Path(__file__).parent.parent.parent.parent / "knowledge_base"),
)


class TFIDFRetriever:
    """Minimal TF-IDF retrieval — no heavy ML framework required."""

    def __init__(self):
        self.documents: List[Dict] = []  # {"text": ..., "metadata": {...}}
        self.tfidf_matrix: List[Dict[str, float]] = []
        self.idf: Dict[str, float] = {}
        self._indexed = False

    def load_and_index(self, kb_dir: str):
        """Load all knowledge-base documents and build TF-IDF index."""
        self.documents = []
        docs_dir = Path(kb_dir)
        if not docs_dir.exists():
            logger.warning("Knowledge base directory not found: %s", kb_dir)
            return

        for fpath in docs_dir.rglob("*.txt"):
            try:
                content = fpath.read_text(encoding="utf-8")
                chunks = self._chunk_text(content, chunk_size=400, overlap=100)
                category = fpath.parent.name
                for i, chunk in enumerate(chunks):
                    self.documents.append({
                        "text": chunk,
                        "metadata": {
                            "source": fpath.name,
                            "category": category,
                            "chunk": i,
                        }
                    })
            except Exception as exc:
                logger.warning("Failed to load %s: %s", fpath, exc)

        for fpath in docs_dir.rglob("*.json"):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                category = fpath.parent.name
                if isinstance(data, list):
                    for item in data:
                        text = self._dict_to_text(item)
                        for chunk in self._chunk_text(text, 400, 100):
                            self.documents.append({"text": chunk, "metadata": {"source": fpath.name, "category": category}})
                elif isinstance(data, dict):
                    text = self._dict_to_text(data)
                    for chunk in self._chunk_text(text, 400, 100):
                        self.documents.append({"text": chunk, "metadata": {"source": fpath.name, "category": category}})
            except Exception as exc:
                logger.warning("Failed to load %s: %s", fpath, exc)

        if not self.documents:
            logger.warning("No documents loaded from knowledge base.")
            return

        self._build_tfidf()
        self._indexed = True
        logger.info("RAG index built: %d document chunks loaded.", len(self.documents))

    def _chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            start += chunk_size - overlap
        return chunks if chunks else [text]

    def _dict_to_text(self, d: Dict) -> str:
        parts = []
        for k, v in d.items():
            if isinstance(v, list):
                parts.append(f"{k}: {', '.join(str(x) for x in v)}")
            else:
                parts.append(f"{k}: {v}")
        return "\n".join(parts)

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_+#]+\b", text.lower())

    def _tf(self, tokens: List[str]) -> Dict[str, float]:
        freq: Dict[str, int] = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        total = len(tokens) or 1
        return {t: c / total for t, c in freq.items()}

    def _build_tfidf(self):
        N = len(self.documents)
        df: Dict[str, int] = defaultdict(int)
        all_tf = []

        for doc in self.documents:
            tokens = self._tokenize(doc["text"])
            tf = self._tf(tokens)
            all_tf.append(tf)
            for term in set(tokens):
                df[term] += 1

        self.idf = {term: math.log((N + 1) / (cnt + 1)) + 1 for term, cnt in df.items()}
        self.tfidf_matrix = [
            {term: tf_val * self.idf.get(term, 1.0) for term, tf_val in tf.items()}
            for tf in all_tf
        ]

    def _cosine_sim(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        shared = set(vec_a) & set(vec_b)
        dot = sum(vec_a[t] * vec_b[t] for t in shared)
        mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values())) or 1.0
        mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values())) or 1.0
        return dot / (mag_a * mag_b)

    def retrieve(self, query: str, top_k: int = 5, category_filter: Optional[str] = None) -> List[Dict]:
        """Return top-k most relevant document chunks for the query."""
        if not self._indexed:
            return []

        query_tokens = self._tokenize(query)
        query_tf = self._tf(query_tokens)
        query_vec = {term: tf_val * self.idf.get(term, 1.0) for term, tf_val in query_tf.items()}

        scored = []
        for i, doc_vec in enumerate(self.tfidf_matrix):
            doc = self.documents[i]
            if category_filter and doc["metadata"].get("category") != category_filter:
                continue
            score = self._cosine_sim(query_vec, doc_vec)
            scored.append((score, i))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [self.documents[idx] for _, idx in scored[:top_k]]


# Singleton retriever
_retriever = TFIDFRetriever()


def initialize_rag():
    """Load and index the knowledge base. Call once on application startup."""
    _retriever.load_and_index(KNOWLEDGE_BASE_DIR)


def retrieve_context(
    role: str,
    skills: List[str],
    interview_type: str,
    experience_level: str,
    additional_context: str = "",
) -> str:
    """
    Build a query from the candidate profile and retrieve relevant knowledge.
    Returns a formatted context string ready for injection into a Granite prompt.
    """
    query_parts = [
        f"interview questions for {role}",
        f"experience level {experience_level}",
        f"interview type {interview_type}",
    ]
    if skills:
        query_parts.append(f"skills: {' '.join(skills[:6])}")
    if additional_context:
        query_parts.append(additional_context)

    query = " ".join(query_parts)

    # Category mapping
    cat_map = {
        "technical": "technical",
        "hr": "hr",
        "behavioral": "behavioral",
        "mixed": None,
    }
    category_filter = cat_map.get(interview_type)

    results = _retriever.retrieve(query, top_k=6, category_filter=category_filter)

    if not results and category_filter is not None:
        # Retry with a wider top_k but preserve the category fence
        results = _retriever.retrieve(
            query,
            top_k=10,
            category_filter=category_filter,
        )

    if not results:
        return _fallback_context(role, interview_type)

    context_parts = []
    for i, doc in enumerate(results, 1):
        meta = doc["metadata"]
        context_parts.append(
            f"[Context {i} | Source: {meta.get('source', 'knowledge base')} | Category: {meta.get('category', 'general')}]\n{doc['text']}"
        )

    return "\n\n".join(context_parts)


def _fallback_context(role: str, interview_type: str) -> str:
    """Return hardcoded fallback context when knowledge base is empty."""
    contexts = {
        "technical": f"""Technical Interview Guidelines for {role}:
- Focus on data structures, algorithms, and system design
- Expect questions on programming languages mentioned in resume
- Be prepared to write and explain code
- Discuss time and space complexity
- Common topics: Arrays, Linked Lists, Trees, Graphs, Dynamic Programming
- System design: scalability, databases, APIs, caching, load balancing
- OOP principles: encapsulation, inheritance, polymorphism, abstraction
- Database concepts: SQL, normalization, indexing, transactions""",

        "hr": f"""HR Interview Guidelines for {role}:
- Questions focus on motivation, culture fit, and career goals
- Use specific examples from past experience
- Research the company before the interview
- Prepare answers for: Tell me about yourself, strengths/weaknesses, goals
- Show enthusiasm and professionalism
- Ask thoughtful questions about the role and company
- Discuss salary expectations if asked honestly""",

        "behavioral": f"""Behavioral Interview Guidelines for {role}:
- Use the STAR method: Situation, Task, Action, Result
- Prepare 5-7 stories from your experience
- Topics: teamwork, conflict resolution, leadership, initiative, failure/learning
- Be specific with outcomes and metrics where possible
- Show self-awareness and growth mindset
- Examples: problem-solving under pressure, handling disagreements, learning new skills""",
    }
    return contexts.get(interview_type, contexts.get("technical", "Interview preparation context."))

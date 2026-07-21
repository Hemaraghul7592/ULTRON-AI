from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    PERSON_KEYWORDS = {
        "mr",
        "mrs",
        "ms",
        "dr",
        "prof",
        "sir",
        "madam",
    }
    ORG_KEYWORDS = {
        "inc",
        "llc",
        "corp",
        "ltd",
        "company",
        "organization",
        "university",
        "college",
        "institute",
        "foundation",
    }

    async def extract(self, text: str) -> dict[str, Any]:
        entities = []
        relationships = []

        capitalized = re.findall(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b", text)
        seen = set()
        for name in capitalized:
            if name.lower() in seen or len(name) < 2:
                continue
            seen.add(name.lower())

            entity_type = self._classify_entity(name, text)
            entities.append(
                {
                    "name": name,
                    "type": entity_type,
                    "description": "Extracted from text",
                }
            )

        patterns = [
            (r"(\w+)\s+(works at|is at|employed by)\s+(\w+)", "works_at"),
            (r"(\w+)\s+(knows|is friends with)\s+(\w+)", "knows"),
            (r"(\w+)\s+(owns|has)\s+(\w+)", "owns"),
            (r"(\w+)\s+(manages|leads|directs)\s+(\w+)", "manages"),
        ]
        for pattern, rel_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                relationships.append(
                    {
                        "source": match[0],
                        "target": match[2],
                        "type": rel_type,
                        "weight": 0.7,
                    }
                )

        return {
            "entities": entities,
            "relationships": relationships,
        }

    async def extract_memories(self, text: str) -> list[dict[str, Any]]:
        memories = []
        sentences = re.split(r"[.!?]+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            importance = self._assess_importance(sentence)
            tags = self._extract_tags(sentence)
            memory_type = self._classify_memory(sentence)

            memories.append(
                {
                    "content": sentence,
                    "importance": importance,
                    "type": memory_type,
                    "tags": tags,
                }
            )

        return memories

    def _classify_entity(self, name: str, context: str) -> str:
        context_lower = context.lower()
        name_lower = name.lower()

        for kw in self.ORG_KEYWORDS:
            if kw in context_lower and name_lower in context_lower:
                return "organization"

        words_around = context_lower.split(name_lower)
        if len(words_around) > 1:
            after = words_around[1][:50]
            for kw in self.PERSON_KEYWORDS:
                if kw in after:
                    return "person"

        if name[0].isupper() and not any(c.isdigit() for c in name):
            if len(name.split()) == 1:
                return "concept"
            return "person"

        return "concept"

    def _assess_importance(self, text: str) -> float:
        importance = 0.3
        high_importance = [
            "important",
            "critical",
            "deadline",
            "urgent",
            "must",
            "always",
            "never",
            "remember",
            "key",
            "essential",
        ]
        for word in high_importance:
            if word in text.lower():
                importance += 0.15

        if any(c in text for c in ["!", "!!"]):
            importance += 0.1

        if "?" in text:
            importance += 0.05

        return min(importance, 1.0)

    def _extract_tags(self, text: str) -> list[str]:
        tags = []
        tag_patterns = {
            "personal": r"\b(my|i|me|myself|our|we)\b",
            "professional": r"\b(work|project|meeting|deadline|client|team)\b",
            "technical": r"\b(code|api|database|server|bug|feature)\b",
            "temporal": r"\b(today|tomorrow|yesterday|week|month|year)\b",
            "emotional": r"\b(feel|happy|sad|excited|worried|frustrated)\b",
        }
        for tag, pattern in tag_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
        return tags

    def _classify_memory(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["remember", "note:", "important:"]):
            return "long_term"
        if any(w in text_lower for w in ["today", "just now", "currently", "right now"]):
            return "short_term"
        return "episodic"

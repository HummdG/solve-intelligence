from __future__ import annotations

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.internal.prompt import PROMPT

# Don't modify this file

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-3.5-turbo-1106"


def get_ai(
    model: str | None = OPENAI_MODEL,
    api_key: str | None = OPENAI_API_KEY,
) -> AI:
    if not api_key or not model:
        raise ValueError("Both API key and model need to be set")
    return AI(api_key, model)


class AI:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)
        self._random_error_probability = 0.05

    async def review_document(self, document: str) -> AsyncGenerator[str | None, None]:
        """
            You are a domain-specialized AI system trained to review patent documents for technical and legal precision. Your task is to identify errors, inconsistencies, or ambiguous claims in the input patent document and provide high-quality, factual, and justifiable suggestions for correction.

            Strict Instructions:
            - DO NOT infer or fabricate technical content not explicitly stated in the document.
            - DO NOT hallucinate terminology, prior art, or legal interpretations.
            - DO NOT generate summaries or explanations outside the required JSON format.

            Input:
            - `document` (string): A plain-text patent document. May include multiple paragraphs. Will throw an error if input includes HTML, markdown, or LaTeX.

            Expected Output:
            - A generator that yields a structured JSON object containing all review issues found.

            Response Format (MUST STRICTLY FOLLOW):
            {
            "issues": [
                {
                "type": "<error_type>",                 # E.g., "inconsistency", "ambiguity", "legal_scope", "technical_clarity"
                "severity": "<high|medium|low>",        # Reflects impact on patent validity or clarity
                "paragraph": <integer>,                 # Paragraph number where issue occurs
                "description": "<description_of_issue>",# Clear, concise explanation of the identified issue
                "suggestion": "<recommended_fix>"       # Direct, factual correction or improvement
                },
                ...
            ]
            }

            Reminder:
            - Only return issues that are directly justifiable by the source document.
            - Be conservative and factual in identifying problems—accuracy is more important than coverage.
        """

        stream = await self._client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": document},
            ],
            stream=True,
        )

        async for chunk in stream:
            yield chunk.choices[0].delta.content

from typing import List, Literal
from pydantic import BaseModel, Field

class QueryAnalysis(BaseModel):
    route: Literal["rag", "conversational"] = Field(
        description="'rag' if the query requires document search, 'conversational' if it's about the conversation itself, greetings, acknowledgments, or general chat."
    )
    is_clear: bool = Field(
        description="Indicates if the user's question is clear and answerable."
    )
    questions: List[str] = Field(
        description="List of rewritten, self-contained questions."
    )
    clarification_needed: str = Field(
        description="Explanation if the question is unclear."
    )
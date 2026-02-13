import re
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import config

# Exact matches — no LLM needed
EXACT_KEYWORDS = re.compile(
    r"lucky\s*draw|prize\s*draw|enter\s*draw|join\s*draw|raffle",
    re.IGNORECASE,
)

# Soft signals — worth asking the LLM about
SOFT_SIGNALS = re.compile(
    r"\bdraw\b|\benter\b|\bprize\b|\bwin\b|\bcontest\b|\bgiveaway\b|\bsweepstake",
    re.IGNORECASE,
)

CLASSIFICATION_PROMPT = (
    "You are a strict intent classifier. The user's message will be provided. "
    "Determine if the user wants to enter or participate in a lucky draw / prize draw / raffle / giveaway.\n\n"
    "Reply with ONLY one word: YES or NO. Do not explain."
)


class IntentDetector:

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOllama(
                model=config.LLM_MODEL,
                temperature=0,
            )
        return self._llm

    def is_lucky_draw_intent(self, text: str) -> bool:
        if EXACT_KEYWORDS.search(text):
            return True

        if not SOFT_SIGNALS.search(text):
            return False

        return self._classify_with_llm(text)

    def _classify_with_llm(self, text: str) -> bool:
        try:
            response = self.llm.invoke([
                SystemMessage(content=CLASSIFICATION_PROMPT),
                HumanMessage(content=text),
            ])
            answer = response.content.strip().upper()
            # Handle models that think before answering (e.g. qwen3)
            # Look for YES/NO after any </think> tag or at the end
            if "</think>" in answer:
                answer = answer.split("</think>")[-1].strip()
            return answer.startswith("YES")
        except Exception:
            return False

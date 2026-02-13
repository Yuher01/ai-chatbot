from typing import Literal, Union, List
from langgraph.types import Send
from .graph_state import State

def route_after_rewrite(state: State) -> Union[Literal["human_input", "conversational_response"], List[Send]]:
    if state.get("route") == "conversational":
        return "conversational_response"
    elif not state.get("questionIsClear", False):
        return "human_input"
    else:
        return [
            Send("process_question", {"question": query, "question_index": idx, "messages": []})
            for idx, query in enumerate(state["rewrittenQuestions"])
        ]

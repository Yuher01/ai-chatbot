from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from .graph_state import State, AgentState
from .schemas import QueryAnalysis
from .prompts import *
from qdrant_client.http import models as qmodels

def _sample_document_snippets(collection, document_sources, chunks_per_doc=3):
    """Sample random chunks from each document to build content snippets."""
    if not collection or not document_sources:
        return None
    try:
        all_snippets = []
        for source in document_sources:
            result = collection.client.query_points(
                collection_name=collection.collection_name,
                query=qmodels.SampleQuery(sample=qmodels.Sample.RANDOM),
                query_filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(
                        key="metadata.source",
                        match=qmodels.MatchValue(value=source),
                    )]
                ),
                limit=chunks_per_doc,
                with_payload=True,
            )
            for point in result.points:
                all_snippets.append(
                    f"- [{point.payload.get('metadata', {}).get('source', 'unknown')}] "
                    f"{point.payload.get('page_content', '')[:200].strip()}"
                )
        return "\n".join(all_snippets) if all_snippets else None
    except Exception:
        return None


def analyze_chat_and_summarize(state: State, llm):
    if len(state["messages"]) < 4:
        return {"conversation_summary": ""}

    relevant_msgs = [
        msg for msg in state["messages"][:-1]
        if isinstance(msg, (HumanMessage, AIMessage))
        and not getattr(msg, "tool_calls", None)
    ]

    if not relevant_msgs:
        return {"conversation_summary": ""}

    existing_summary = state.get("conversation_summary", "")

    new_messages = "Recent messages:\n"
    for msg in relevant_msgs[-6:]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        new_messages += f"{role}: {msg.content}\n"

    context = ""
    if existing_summary.strip():
        context = f"Existing summary of earlier conversation:\n{existing_summary}\n\n"
    context += new_messages

    summary_response = llm.with_config(temperature=0.2).invoke([SystemMessage(content=get_conversation_summary_prompt())] + [HumanMessage(content=context)])
    return {"conversation_summary": summary_response.content, "agent_answers": [{"__reset__": True}]}

def analyze_and_rewrite_query(state: State, llm):
    last_message = state["messages"][-1]
    conversation_summary = state.get("conversation_summary", "")

    context_section = (f"Conversation Context:\n{conversation_summary}\n" if conversation_summary.strip() else "") + f"User Query:\n{last_message.content}\n"

    llm_with_structure = llm.with_config(temperature=0.1).with_structured_output(QueryAnalysis)
    response = llm_with_structure.invoke([SystemMessage(content=get_query_analysis_prompt())] + [HumanMessage(content=context_section)])

    if response.route == "conversational":
        return {
            "route": "conversational",
            "questionIsClear": True,
            "originalQuery": last_message.content,
            "rewrittenQuestions": []
        }

    if len(response.questions) > 0 and response.is_clear:
        delete_all = [
            RemoveMessage(id=m.id)
            for m in state["messages"]
            if not isinstance(m, SystemMessage)
        ]
        return {
            "route": "rag",
            "questionIsClear": True,
            "messages": delete_all,
            "originalQuery": last_message.content,
            "rewrittenQuestions": response.questions
        }
    else:
        clarification = response.clarification_needed if (response.clarification_needed and len(response.clarification_needed.strip()) > 10) else "I need more information to understand your question."
        return {
            "route": "rag",
            "questionIsClear": False,
            "messages": [AIMessage(content=clarification)]
        }

def human_input_node(state: State):
    return {}

def agent_node(state: AgentState, llm_with_tools):
    sys_msg = SystemMessage(content=get_rag_agent_prompt())    
    if not state.get("messages"):
        human_msg = HumanMessage(content=state["question"])
        response = llm_with_tools.invoke([sys_msg] + [human_msg])
        return {"messages": [human_msg, response]}
    
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

def extract_final_answer(state: AgentState):
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            res = {
                "final_answer": msg.content,
                "agent_answers": [{
                    "index": state["question_index"],
                    "question": state["question"],
                    "answer": msg.content
                }]
            }
            return res
    return {
        "final_answer": "Unable to generate an answer.",
        "agent_answers": [{
            "index": state["question_index"],
            "question": state["question"],
            "answer": "Unable to generate an answer."
        }]
    }

def aggregate_responses(state: State, llm, collection=None, get_document_sources=None):
    if not state.get("agent_answers"):
        return {"messages": [AIMessage(content="No answers were generated.")]}

    sorted_answers = sorted(state["agent_answers"], key=lambda x: x["index"])

    formatted_answers = ""
    for i, ans in enumerate(sorted_answers, start=1):
        formatted_answers += (f"\nAnswer {i}:\n"f"{ans['answer']}\n")

    user_message = HumanMessage(content=f"""Original user question: {state["originalQuery"]}\nRetrieved answers:{formatted_answers}""")
    synthesis_response = llm.invoke([SystemMessage(content=get_aggregation_prompt())] + [user_message])

    content = synthesis_response.content
    # Strip Sources section if it contains no real file names (e.g., "Answer 1")
    if "---" in content and "**Sources:**" in content:
        parts = content.split("---")
        sources_part = parts[-1]
        import re
        file_names = re.findall(r'[\w\-]+\.\w{2,4}', sources_part)
        if not file_names:
            content = "---".join(parts[:-1]).rstrip()

    no_answer_phrases = [
        "couldn't find any information",
        "could not find any information",
        "no answers were generated",
    ]
    if any(phrase in content.lower() for phrase in no_answer_phrases):
        document_sources = get_document_sources() if get_document_sources else None
        snippets = _sample_document_snippets(collection, document_sources)
        if snippets:
            suggestion_response = llm.invoke([
                SystemMessage(content=get_suggestion_prompt()),
                HumanMessage(content=snippets)
            ])
            content += f"\n\nHere are some questions you could try:\n{suggestion_response.content}"

    return {"messages": [AIMessage(content=content)]}

def conversational_response(state: State, llm, collection=None, get_document_sources=None):
    conversation_summary = state.get("conversation_summary", "")
    original_query = state.get("originalQuery", "")

    context = ""
    if conversation_summary.strip():
        context = f"Conversation so far:\n{conversation_summary}\n\n"
    context += f"User message:\n{original_query}"

    document_sources = get_document_sources() if get_document_sources else None

    document_snippets = _sample_document_snippets(collection, document_sources)

    response = llm.invoke([
        SystemMessage(content=get_conversational_prompt(document_sources, document_snippets)),
        HumanMessage(content=context)
    ])
    return {"messages": [AIMessage(content=response.content)]}
from langchain_core.messages import HumanMessage
from lucky_draw import LuckyDrawController
from config import LUCKY_DRAW_DB_PATH

class ChatInterface:

    def __init__(self, rag_system):
        self.rag_system = rag_system
        self.lucky_draw = LuckyDrawController(LUCKY_DRAW_DB_PATH)

    def chat(self, message, history):

        if not self.rag_system.agent_graph:
            return "⚠️ System not initialized!"

        lucky_draw_response = self.lucky_draw.handle(message)
        if lucky_draw_response is not None:
            return lucky_draw_response

        try:
            result = self.rag_system.agent_graph.invoke(
                {"messages": [HumanMessage(content=message.strip())]},
                self.rag_system.get_config()
            )
            return result["messages"][-1].content

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def clear_session(self):
        self.rag_system.reset_thread()
        self.lucky_draw.state.reset()

import gradio as gr
from langchain_core.globals import set_debug
from ui.css import custom_css
from ui.gradio_app import create_gradio_ui

set_debug(True)

if __name__ == "__main__":
    demo = create_gradio_ui()
    print("\n🚀 Launching RAG Assistant...")
    demo.launch(css=custom_css)
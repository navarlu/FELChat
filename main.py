import llama_index.core
import time
import os
import numpy as np
import threading
import subprocess
import webbrowser
from rich.console import Console
import json
from trulens.core import Feedback, Select
from trulens.providers.openai import OpenAI as OpenAIFeedbackProvider
from index_manager import IndexManager
from rag_service import RAGService

import sys

# If on Windows, set stdout and stderr encoding
if os.name == 'nt':  # Check if the operating system is Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ---------------------------
# Load configuration from config.json
# ---------------------------
with open('data/configuration/config.json', 'r') as f:
    config = json.load(f)

# Extract configuration values
INDEX_DIR       = config["index"]["directory"]
INDEX_NAME      = config["index"]["name"]
WINDOW_SIZE     = config["index"]["window_size"]

IN_DATABASE_FOLDER = config["folders"]["in_database"]
TMP_FOLDER         = config["folders"]["tmp"]
SAVE_FOLDER        = config["folders"]["save_folder"]
SAVE_FOLDER2       = config["folders"]["save_folder2"]

OPENAI_API_KEY  = config["openai"]["api_key"]

DASHBOARD_PORT  = config["dashboard"]["port"]
DASHBOARD_VIS = config["dashboard"]["visualization"]
STREAMLIT_PORT  = config["streamlit"]["port"]
STREAMLIT_URL   = config["streamlit"]["url"]

FLASK_HOST      = config["flask"]["host"]
FLASK_PORT      = config["flask"]["port"]
FLASK_DEBUG     = config["flask"]["debug"]

# ---------------------------
# Initialize components
# ---------------------------
from flask import Flask, request

# Create the index manager using configuration values
manager = IndexManager(index_name=INDEX_NAME, index_dir=INDEX_DIR, window_size=WINDOW_SIZE)

# Create the RAG service using the manager
rag = RAGService(manager)

console = Console()

# Use the provided OpenAI API key for feedback measurements
provider = OpenAIFeedbackProvider(api_key=OPENAI_API_KEY)

# Define feedback functions
f_groundedness = (
    Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
    .on(Select.RecordCalls.retrieve.rets.collect())
    .on_output()
)
f_answer_relevance = (
    Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
    .on_input()
    .on_output()
)
f_context_relevance = (
    Feedback(provider.context_relevance_with_cot_reasons, name="Context Relevance")
    .on_input()
    .on(Select.RecordCalls.retrieve.rets[:])
    .aggregate(np.mean)
)

from trulens.apps.app import TruApp

tru_rag = TruApp(
    rag,
    app_name="FELChat",
    app_version="version_0.1",
    feedbacks=[f_groundedness, f_answer_relevance, f_context_relevance],
)

# Optionally, launch the dashboard to view detailed feedback
if DASHBOARD_VIS == "yes":
    from trulens.dashboard import run_dashboard
    print("Dasboard port: ",DASHBOARD_PORT)
    run_dashboard(port=DASHBOARD_PORT)



FELChat = Flask(__name__)
os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER2, exist_ok=True)

# ---------------------------
# Helper Functions
# ---------------------------
def get_conversation_history():
    
    conversation_history = None
    return conversation_history


@FELChat.route('/query', methods=['POST'])
def query():
    incoming_data = request.json
    data = incoming_data[0]
    user_query = data.get("query")
    with tru_rag as recording:
        #GET CONVERSATION HISTORY
        conversation_history = []
        rag.conversation_history = conversation_history
        answer, context_str = rag.query(user_query)
        return answer, context_str



def monitor_new_files():
    print("Starting monitoring of the data folder for new JSON and PDF files...")
    while True:
        json_files = [f for f in os.listdir(TMP_FOLDER) if f.endswith(".json")]
        pdf_files = [f for f in os.listdir(TMP_FOLDER) if f.endswith(".pdf")]
        if pdf_files:
            print(f"Found {len(pdf_files)} new PDF file(s) in '{TMP_FOLDER}'. Processing...")
            manager.add_pdfs_to_index(TMP_FOLDER, IN_DATABASE_FOLDER)
        time.sleep(3)

def run_streamlit():
    time.sleep(2)
    subprocess.run(["streamlit", "run", "vector_store_viewer.py", "--server.port", str(STREAMLIT_PORT)])
    
streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
streamlit_thread.start()
webbrowser.open(STREAMLIT_URL)

thread_new = threading.Thread(target=monitor_new_files, daemon=True)

thread_new.start()


if __name__ == '__main__':
    FELChat.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

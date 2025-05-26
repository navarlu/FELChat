
import time
import os
import threading
import subprocess
import webbrowser
import json
from index_manager import IndexManager
from rag_service import RAGService
from flask import request, jsonify
import sys

if os.name == 'nt':  # Check if the operating system is Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

with open('data/configuration/config.json', 'r') as f:
    config = json.load(f)

INDEX_DIR       = config["index"]["directory"]
INDEX_NAME      = config["index"]["name"]
WINDOW_SIZE     = config["index"]["window_size"]

IN_DATABASE_FOLDER = config["folders"]["in_database"]
TMP_FOLDER = config["folders"]["tmp"]
SAVE_FOLDER        = config["folders"]["save_folder"]
SAVE_FOLDER2       = config["folders"]["save_folder2"]


STREAMLIT_PORT  = config["streamlit"]["port"]
STREAMLIT_URL   = config["streamlit"]["url"]

FLASK_HOST      = config["flask"]["host"]
FLASK_PORT      = config["flask"]["port"]
FLASK_DEBUG     = config["flask"]["debug"]

from flask import Flask, request

# Create the index manager using configuration values
manager = IndexManager(index_name=INDEX_NAME, index_dir=INDEX_DIR, window_size=WINDOW_SIZE)

# Create the RAG service using the manager
rag = RAGService(manager)

FELChat = Flask(__name__)
os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER2, exist_ok=True)


def get_conversation_history():
    
    conversation_history = None
    return conversation_history

@FELChat.route('/query', methods=['POST'])
def query():
    print("Received a query request")
    print("Request data: ", request.data)


    incoming_data = request.json


    if not incoming_data or not isinstance(incoming_data, list):
        return jsonify({"error": "Invalid request format"}), 400

    # Get the last user message as the actual query
    last_user_msg = next((msg for msg in reversed(incoming_data) if msg["sender"] == "user"), None)
    if not last_user_msg:
        return jsonify({"error": "No user message found"}), 400

    user_query = last_user_msg["text"]

    # Construct chat history
    conversation_history = []
    for msg in incoming_data:
        role = "user" if msg["sender"] == "user" else "assistant"
        conversation_history.append({"role": role, "content": msg["text"]})

    # Set history in RAG
    rag.conversation_history = conversation_history[:-1]  # omit the last user query to avoid duplication

    # Perform the query
    answer, docs, context, messages, rag_timings = rag.query(user_query)
    return jsonify({"answer": answer, "context": context})

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

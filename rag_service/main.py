# rag_service/main.py

import time
import os
import threading
import subprocess
# import webbrowser # Commented out or removed for Docker
import json
from index_manager import IndexManager
from rag_service import RAGService # This should import from ./rag_service.py
from flask import request, jsonify
import sys

if os.name == 'nt':  # Check if the operating system is Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Ensure the config path is correct relative to main.py running in /app
# In Docker, main.py is /app/main.py, so 'data/...' becomes '/app/data/...'
with open('data/configuration/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

INDEX_DIR       = config["index"]["directory"]
INDEX_NAME      = config["index"]["name"]
WINDOW_SIZE     = config["index"]["window_size"]

IN_DATABASE_FOLDER = config["folders"]["in_database"]
TMP_FOLDER = config["folders"]["tmp"]
SAVE_FOLDER        = config["folders"]["save_folder"]
SAVE_FOLDER2       = config["folders"]["save_folder2"]


STREAMLIT_PORT  = config["streamlit"]["port"]
STREAMLIT_URL   = config["streamlit"]["url"] # Still here, but webbrowser.open is removed

FLASK_HOST      = config["flask"]["host"]    # Ensure this is "0.0.0.0" in config.json for Docker
FLASK_PORT      = config["flask"]["port"]
FLASK_DEBUG     = config["flask"]["debug"]

from flask import Flask # Removed duplicate import of 'request'

# Create the index manager using configuration values
# Ensure paths in config (like INDEX_DIR) are relative to /app (e.g., "data/vectorstore/...")
manager = IndexManager(index_name=INDEX_NAME, index_dir=INDEX_DIR, window_size=WINDOW_SIZE)

# Create the RAG service using the manager
rag = RAGService(manager)

FELChat = Flask(__name__) # When run as script, __name__ is '__main__'

# Ensure these directories exist based on paths relative to /app (e.g., /app/data/evaluation/...)
# The paths in config.json for these folders should start with "data/"
os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER2, exist_ok=True)
os.makedirs(TMP_FOLDER, exist_ok=True) # Make sure TMP_FOLDER also exists

def get_conversation_history():
    conversation_history = None
    return conversation_history

@FELChat.route('/query', methods=['POST'])
def query():
    print("Received a query request")
    # print("Request data: ", request.data) # request.data can be large, consider logging request.json

    incoming_data = request.json
    if not incoming_data: # Simpler check for empty body
        return jsonify({"error": "Request body is empty or not JSON"}), 400
    if not isinstance(incoming_data, list): # Assuming you expect a list of message objects
        return jsonify({"error": "Invalid request format, expected a list of messages"}), 400

    last_user_msg = next((msg for msg in reversed(incoming_data) if msg.get("sender") == "user"), None)
    if not last_user_msg or "text" not in last_user_msg:
        return jsonify({"error": "No user message with text found"}), 400

    user_query = last_user_msg["text"]

    conversation_history = []
    for msg in incoming_data:
        # Ensure 'sender' and 'text' keys exist to avoid KeyErrors
        if "sender" in msg and "text" in msg:
            role = "user" if msg["sender"] == "user" else "assistant"
            conversation_history.append({"role": role, "content": msg["text"]})
        else:
            print(f"Skipping invalid message format: {msg}")


    rag.conversation_history = conversation_history[:-1]

    answer, docs, context, messages, rag_timings = rag.query(user_query)
    return jsonify({"answer": answer, "context": context}) # Consider also returning timings or docs if needed by client

def monitor_new_files():
    print(f"Starting monitoring of '{TMP_FOLDER}' for new JSON and PDF files...")
    while True:
        try:
            # Ensure TMP_FOLDER is accessible and exists
            if not os.path.isdir(TMP_FOLDER):
                print(f"Error: TMP_FOLDER '{TMP_FOLDER}' does not exist or is not a directory. Skipping monitor cycle.")
                time.sleep(10) # Wait longer if a fundamental path is missing
                continue

            # json_files = [f for f in os.listdir(TMP_FOLDER) if f.endswith(".json")] # Not used currently
            pdf_files = [f for f in os.listdir(TMP_FOLDER) if f.endswith(".pdf")]
            
            if pdf_files:
                print(f"Found {len(pdf_files)} new PDF file(s) in '{TMP_FOLDER}'. Processing...")
                # Ensure IN_DATABASE_FOLDER is also correct
                manager.add_pdfs_to_index(TMP_FOLDER, IN_DATABASE_FOLDER)
            # Add similar handling for JSON files if needed
            # if json_files:
            #     print(f"Found {len(json_files)} new JSON file(s) in '{TMP_FOLDER}'. Processing...")
            #     manager.add_jsons_to_index(TMP_FOLDER, IN_DATABASE_FOLDER)

        except Exception as e:
            print(f"Error in monitor_new_files loop: {e}")
        time.sleep(3) # Check interval

def run_streamlit():
    # Wait for Flask to potentially start, though not strictly necessary for subprocess
    time.sleep(2)
    streamlit_cmd = [
        "streamlit", "run", "vector_store_viewer.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", "0.0.0.0" # Make Streamlit accessible from outside container
    ]
    print(f"Running Streamlit: {' '.join(streamlit_cmd)}")
    subprocess.run(streamlit_cmd)

streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
streamlit_thread.start()

# The webbrowser.open() line is removed as it's not suitable for Docker.
# Users will access Streamlit via http://localhost:STREAMLIT_PORT (or mapped port)

thread_new = threading.Thread(target=monitor_new_files, daemon=True)
thread_new.start()


print(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}")
FELChat.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

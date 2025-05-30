# FELChat – Localhost Setup Guide

This guide provides step-by-step instructions to set up the FELChat project locally, leveraging Docker and Python virtual environments.

## Prerequisites

Ensure your system has the following:

- **Python**: 3.12
- **Docker**: Installed and running
- **NVIDIA CUDA**: Installed for GPU support
- **GPU**: Available with at least 30GB of free space
- **Disk Space**: At least 30GB free

## Installation Steps

### 1. Clone the Repository

```bash
git clone -b localhost_setup2 https://github.com/navarlu/FELChat.git
cd FELChat
```

### 2. Start Docker Services

Make sure Docker is running, then start the services:

```bash
docker-compose up
```

This builds and launches the required containers.

### 3. Set Up Python Virtual Environment

Navigate to the `rag_service` folder:

```bash
cd rag_service
```

Create and activate a virtual environment called `Felchat_env`:

```bash
python3.12 -m venv Felchat_env
source Felchat_env/bin/activate  # On Windows: Felchat_env\Scripts\activate
```

### 4. Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Run the Server

With the virtual environment activated, run:

```bash
python server.py
```

The server should now be running and ready for use.

## Notes and Customization

### 🔧 Modify the LLM Model

You can change the model used by editing the `server.py` file located in the `rag_service` directory.

### 🌐 Running on a Remote GPU Server

If you want to deploy `server.py` on a GPU server (e.g., cloud or remote):

1. **Expose the Server**  
   Use a tunneling tool like [ngrok](https://ngrok.com/) to expose your remote server.

2. **Edit the URL**  
   Open `server.py` and update the `LLM_CHAT_SERVER_URL` variable to point to the new public address.

3. **Rebuild the Docker Service**  
   After updating the URL, rebuild the `rag-service` container:

   ```bash
   docker-compose build rag-service
   ```

4. **Restart Docker Compose**  
   Apply the changes by restarting:

   ```bash
   docker-compose up
   ```

Your FELChat instance should now be fully functional, locally or remotely.

## 💬 How to Use FELChat

Once you've completed the setup and started the services with `docker-compose up`, follow these steps:

1. **Wait for Initialization**  
   Give the backend and frontend containers a few moments to fully initialize. This may take up to a minute, especially on the first launch.

2. **Open the WebChat Interface**  
   Visit [http://localhost:3000](http://localhost:3000) in your web browser.

3. **Start Chatting**  
   You’ll see a simple chat UI. Type your question or message into the input box and press enter. FELChat will respond using the underlying RAG system and language model.

4. **Enrich the Knowledge Base**  
   To add more documents to the vector store, simply drag and drop files into the following folder:

   ```
   data/fel/tmp
   ```

   These files will be automatically detected, processed, and indexed into the vector store for future use by the assistant.

---

## Now you're ready to chat with your documents!

## 📂 Script Overview

Descriptions of the main scripts and their roles in the FELChat system:

- **`main.py`**  
  This script serves as the file watcher and ingestion trigger. It monitors the `data/fel/tmp` directory and automatically processes any new files added there. These documents are parsed, embedded, and appended to the vector store, enriching the system's knowledge base dynamically.

- **`index_manager.py`**  
  Defines the `IndexManager` class responsible for managing the vector store. It handles initialization, saving, updating, and querying of the document index used in retrieval-augmented generation (RAG).

- **`rag_chain.py`**  
  Encapsulates the logic pipeline of the RAG system. It ties together the retriever, prompt templates, and language model, coordinating how queries are answered using both retrieved documents and the LLM.

- **`server.py`**  
  Launches the FastAPI-based backend server that powers the FELChat service. It exposes API routes for the frontend chat interface, document uploads, and LLM responses.

- **`document_utils.py`**  
  Provides helper functions for cleaning, splitting, and extracting text content from documents before they are embedded and stored.

- **`llm_utils.py`**  
  Contains utility functions to initialize and communicate with the language model. This includes formatting prompts, sending requests, and handling the model's outputs.

- **`embed_utils.py`**  
  Handles the embedding step: it converts raw or preprocessed text into vector form using a selected embedding model. These vectors are used for similarity search in the vector store.

- **`config.py`**  
  Central configuration file defining environment variables, directory paths, model names, URLs, and other key settings. Adjust this to adapt the system to local or remote deployments.

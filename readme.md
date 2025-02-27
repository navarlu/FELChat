# PDF_CHAT – super-lightweight RAG-Based Chatbot for conversational interaction with PDF files in a text console.

# Install

Install Ollama:
```
curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz
sudo tar -C ~/.local/ -xzf ollama-linux-amd64.tgz
```

Download model:
```
$ ollama pull model_name
```
where the model names is e.g. ```deepseek-r1:1.5b```. The Ollama model library is [here](https://ollama.com/library) .

Create environment:
```
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```
The python needs to be 3.9 or greater.

# Sources

- [Original code from Ollama-playground](https://github.com/NarimanN2/ollama-playground/tree/main/chat-with-pdf)
- [Youtube video of the author](https://www.youtube.com/watch?v=M6vZ6b75p9k).
- [Streamlit.io](https://streamlit.io/) Easy way to make web applications.
- [LangChain](https://github.com/langchain-ai/langchain/tree/master)  framework for developing applications powered by large language models (LLMs).
- [ollama.com](https://ollama.com/) Project that allows running LLM locally.
- [https://ollama.com/blog/embedding-models](https://ollama.com/blog/embedding-models) Models for text embedding supported by Ollama.

# Run PDF_CHAT from console

1. Download appropriate LLMs, e.g.
```
$ ollama pull deepseek-r1:14b
$ ollama pull mxbai-embed-large:latest
```

2. Run Ollama service:
```
$ ollama serve
```

3. Run the RAG script with specification of LLM for text embedding (retrieval) and reasoning, e.g.:

```
$ python pdf_rag.py --reasoning deepseek-r1:32b --embedding mxbai-embed-large:latest pdfs/StatuteCTU.pdf
```

# WebApp using Streamlit

This is the original code. First, run the Ollama service (see above). Then, issue:

```
$ source env/bin/activate
$ streamlit run streamlit_pdf_rag.py 
```
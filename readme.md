
# Install

Install Ollama:
```
curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz
sudo tar -C ~/.local/ -xzf ollama-linux-amd64.tgz
```

Download model:
```
ollama pull model_name
```
where the model names is e.g. ```deepseek-r1:1.5b```. The Ollama model library is [here](https://ollama.com/library) .

Run Ollama:
```
ollama serve
```

# Sources

- [Ollama-playground](https://github.com/NarimanN2/ollama-playground/tree/main) Code of the PDF chat. [Youtube video of the author](https://www.youtube.com/watch?v=M6vZ6b75p9k).
- [Streamlit.io](https://streamlit.io/) Easy way to make web applications.
- [LangChain](https://github.com/langchain-ai/langchain/tree/master)  framework for developing applications powered by large language models (LLMs).
- [ollama.com](https://ollama.com/) Project that allows running LLM locally.

# WebApp using Streamlit

This is the original code. First, run the Ollama service (see above). Then, issue:


```
$ source env/bin/activate
$ streamlit run streamlit_pdf_rag.py 
```
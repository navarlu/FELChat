from langchain_community.document_loaders import PDFPlumberLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain.docstore.document import Document
import pickle
import argparse
import os

template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question} 
Context: {context} 
Answer:
"""

#template = """
#Jsi asistentem pro zodpovídání otázek. K zodpovězení otázky použijte následující části vyhledaného kontextu. Pokud odpověď neznáš, řekni, že nevíš. Použij maximálně tři věty a odpověz stručně.
#Otázka: {question} 
#Kontext: {context} 
#Odpověď:
#"""

def load_pdf(file_path):

    loader = PDFPlumberLoader(file_path)
    documents = loader.load()

    return documents

def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )

    return text_splitter.split_documents(documents)

def retrieve_docs(query,k=4):
    return vector_store.similarity_search(query,k=k)

def answer_question(question, documents):
    context = "\n\n".join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm

    return chain.invoke({"question": question, "context": context})

VECTOR_STORE_PATH = "vector_store.pkl"
UPDATE_VECTORS = False  # Set to True if vectors should be updated before starting the conversation



if __name__ == "__main__":
    # Hardcoded values
    reasoning_model = "deepseek-r1:14b"
    reasoning_model = "llama3.1:latest"
    
    embedding_model = "mxbai-embed-large:latest"
    num_chunks = 4
    pdf_file = "pdfs/StatuteCTU.pdf"

    # Print the configurations
    print(f"Reasoning model: {reasoning_model}")
    print(f"Embedding model: {embedding_model}")
    print(f"# Retrieved chunks: {num_chunks}")
    print(f"PDF file: {pdf_file}")

    embeddings = OllamaEmbeddings(model=embedding_model)

    # Check if vector store exists and whether to update it
    if UPDATE_VECTORS or not os.path.exists(VECTOR_STORE_PATH) or os.path.getsize(VECTOR_STORE_PATH) == 0:
        print("Creating or updating vector store...")
        vector_store = InMemoryVectorStore(embeddings)
        documents = load_pdf(pdf_file)
        chunked_documents = split_text(documents)
        print(f"PDF split into {len(chunked_documents)} chunks.")
        vector_store.add_documents(chunked_documents)

        # Save only the processed document data
        with open(VECTOR_STORE_PATH, "wb") as f:
            pickle.dump(chunked_documents, f)
    else:
        print("Loading existing vector store...")
        try:
            with open(VECTOR_STORE_PATH, "rb") as f:
                stored_documents = pickle.load(f)
            vector_store = InMemoryVectorStore(embeddings)
            vector_store.add_documents(stored_documents)
        except (EOFError, pickle.UnpicklingError):
            print("Error loading vector store, recreating it...")
            vector_store = InMemoryVectorStore(embeddings)
            documents = load_pdf(pdf_file)
            chunked_documents = split_text(documents)
            print(f"PDF split into {len(chunked_documents)} chunks.")
            vector_store.add_documents(chunked_documents)
            with open(VECTOR_STORE_PATH, "wb") as f:
                pickle.dump(chunked_documents, f)

    # Initialize LLM
    llm = OllamaLLM(model=reasoning_model)

    # Interactive Q&A loop
    while True:
        print("---")        
        question = input('Ask a question (type "bye" to exit): ')
        if question.lower() == "bye":
            break

        related_documents = retrieve_docs(question, num_chunks)
        answer = answer_question(question, related_documents)

        print("---")        
        print(answer)
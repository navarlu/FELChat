from langchain_community.document_loaders import PDFPlumberLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain.docstore.document import Document

import argparse


template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question} 
Context: {context} 
Answer:
"""

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


if __name__ == "__main__":

    # use argparse to get input argument from the terminal which specifies directory with input PDFs
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_file", type=str, help="PDF file.")
    parser.add_argument("--reasoning", default="deepseek-r1:32b", type=str, help="Model to use for reasoning.")
    parser.add_argument("--embedding", default="mxbai-embed-large:latest", type=str, help="Model to use for embedding.")
    parser.add_argument("--num_chunks", default=4, type=int, help="Number of retrieved chunks.")

    args = parser.parse_args()

    pdf_file = args.pdf_file
    reasoning_model = args.reasoning
    embedding_model = args.embedding
    num_chunks = args.num_chunks

    #
    print(f"reasoning model: {reasoning_model}")
    print(f"embedding model: {embedding_model}")
    print(f"# retrieved chunks: {num_chunks}")

    #
    embeddings = OllamaEmbeddings(model=embedding_model)
    vector_store = InMemoryVectorStore(embeddings)
    llm = OllamaLLM(model=reasoning_model)

    #
    documents = load_pdf(pdf_file)
    chunked_documents = split_text(documents)
    print(f"PDF split to {len(chunked_documents)} chunks.")
    vector_store.add_documents(documents)

    while True:
        print("---")        
        question = input('Ask a question (type "bye" to exit): ')
        if question == "bye":
            break

        related_documents = retrieve_docs(question,num_chunks)

        answer = answer_question(question, related_documents)

        print("---")        
        print(answer)

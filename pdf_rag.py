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

def load_documents(dir):

    # load all text files in dir, with extensionn.txt, using TextLoader
    for file in 


    #loader = TextLoader('./texts/article1.txt')
    #doc1 = loader.load()
    #loader = TextLoader('./texts/article2.txt')
    #doc2 = loader.load()
    #documents = [doc1,doc2]
    #return documents

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

def index_docs(documents):
    vector_store.add_documents(documents)

def retrieve_docs(query,k=4):
    return vector_store.similarity_search(query,k=k)

def answer_question(question, documents):
    context = "\n\n".join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    return chain.invoke({"question": question, "context": context})


if __name__ == "__main__":

    # use argparse to get input argument from the terminal which specifies directory with input PDFs
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfs_directory", default="./pdfs/", type=str, help="Directory with input PDFs")
    parser.add_argument("--model", default="deepseek-r1:1.5b", type=str, help="Model to use for embeddings and reasoning")

    args = parser.parse_args()
    pdfs_directory = args.pdfs_directory    
    model = args.model

    #embeddings = OllamaEmbeddings(model="deepseek-r1:14b")
    #model = OllamaLLM(model="deepseek-r1:14b")

    embeddings = OllamaEmbeddings(model=model)
    vector_store = InMemoryVectorStore(embeddings)

    model = OllamaLLM(model=model)

    #
    documents1 = load_pdf(pdfs_directory + "sample.pdf")
    documents = load_documents()

    chunked_documents = split_text(documents)
    index_docs(chunked_documents)

    for i, doc in enumerate(chunked_documents):
        print(f"-- Chunk {i} ------------------------------------------")
        print(f"\n* {doc.page_content} [{doc.metadata}]")



    while True:
        question = input('Ask a question (type "bye" to exit): ')
        if question == "bye":
            break

        related_documents = retrieve_docs(question)

        for i, doc in enumerate(related_documents):
            print(f"-- Retrieved document {i}------------------------------------------")
            print(f"* {doc.page_content} [{doc.metadata}]")

        answer = answer_question(question, related_documents)

        
        print('------------------------------------------------------------')
        print(answer)
        print('------------------------------------------------------------')


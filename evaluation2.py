# Uncomment and run the following line in Colab to install dependencies:
# !pip install trulens trulens-providers-openai chromadb openai
from llama_index.core import Document
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core import load_index_from_storage
from llama_index.llms.openai import OpenAI as OpenAI3
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.indices.postprocessor import SentenceTransformerRerank
import json
import os
import numpy as np
import os
import openai
import glob
import os
from dotenv import load_dotenv
# Build RAG from scratch with instrumentation
# ---------------------------
from trulens.apps.app import instrument
from trulens.core import TruSession

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key is now available in os.environ
openai_api_key = os.getenv("OPENAI_API_KEY")

# (Optional) Check if the key was loaded correctly
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the .env file")





# Import the OpenAI client from the trulens provider package.
# (This is not the standard openai package, so ensure you have trulens-providers-openai installed)
from openai import OpenAI

oai_client = OpenAI()
def generate_answer(user_question, retrieved_documents, model_temperature=0.1, model_name="gpt-4o-mini"):
    """
    Generates an answer using OpenAI's API based on retrieved documents.

    Parameters:
        user_question (str): The question asked by the user.
        retrieved_documents (list): List of retrieved document texts.
        model_temperature (float): The temperature for response creativity.
        model_name (str): The OpenAI model to use.

    Returns:
        str: The generated response.
    """
    if not retrieved_documents:
        return "No relevant documents found to answer the question."

    # Construct the context prompt using the retrieved documents.
    context = "\n\n".join([f"Document {idx + 1}: {doc}" for idx, doc in enumerate(retrieved_documents)])
    prompt = f"""
You are a helpful assistant that answers questions based on provided information.

Context from retrieved documents:
{context}

Question: {user_question}

Please provide a clear and concise answer based on the context above.
"""

    try:
        # Create a chat completion using OpenAI's API.
        from openai import OpenAI as OpenAI2
        client = OpenAI2()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=model_temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"
    
def get_sentence_window_index(documents, index_dir, sentence_window_size=3):
    
    # Create a node parser with the desired window size
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=sentence_window_size,
        window_metadata_key="window",
        original_text_metadata_key="original_sentence",
    )

    # Set settings for your custom retrieval (update as needed)
    
    Settings.llm = OpenAI3()
    Settings.embed_model = "local:BAAI/bge-small-en-v1.5"
    Settings.node_parser = node_parser

    config_file = os.path.join(index_dir, "config.json")

    # Check if index exists and if the window size is different
    if os.path.exists(index_dir):
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
            if config.get("window_size") == sentence_window_size:
                
                return load_index_from_storage(StorageContext.from_defaults(persist_dir=index_dir))

        # Delete old index if window size has changed
        print("Window size changed. Rebuilding index...")
        for file in os.listdir(index_dir):
            os.remove(os.path.join(index_dir, file))

    # Create a new index from your documents
    
    sentence_index = VectorStoreIndex.from_documents(documents)
    sentence_index.storage_context.persist(persist_dir=index_dir)

    # Save new configuration
    os.makedirs(index_dir, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump({"window_size": sentence_window_size}, f)

    return sentence_index

def get_sentence_window_engine(sentence_index):
    
    # Create postprocessors and rerankers as needed
    postprocessor = MetadataReplacementPostProcessor(target_metadata_key="window")
    rerank = SentenceTransformerRerank(top_n=3, model="BAAI/bge-reranker-base")
    # Create and return the query engine
    sentence_window_engine = sentence_index.as_query_engine(
        similarity_top_k=6,
        node_postprocessors=[postprocessor, rerank],
        response_mode="no_text"  # Adjust response mode if necessary
    )
    return sentence_window_engine

class RAG:
    def __init__(self, documents, index_dir, sentence_window_size=3):
        """
        Initialize the custom retrieval engine with your documents.
        """
        self.session = TruSession()
        
        # Build or load the sentence-window index from your documents
        self.sentence_index = get_sentence_window_index(documents, index_dir, sentence_window_size)
        # Create the query engine based on the index
        self.engine = get_sentence_window_engine(self.sentence_index)
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text using the custom query engine.
        """
        # Query the engine (the exact return format may vary depending on your library)
        results = self.engine.query(query)
        # For this example, we assume 'results' is a list of nodes/dicts with a 'text' key.
        # Adjust this extraction logic as needed.
        try:
            retrieved_texts = [node.node.text for node in results.source_nodes]
            
        except Exception:
            # Fallback if results is a simple list of strings
            print("Exception")
            retrieved_texts = results if isinstance(results, list) else [str(results)]
        return retrieved_texts

    @instrument
    def generate_completion(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        return generate_answer(query, context_str)
        

    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query=query)
        completion = self.generate_completion(query=query, context_str=context_str)
        return completion , context_str

import fitz  # PyMuPDF
import os
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

def highlight_text_in_pdf(pdf_path, output_pdf_path, search_text, highlight_color=(1, 1, 0)):
    """
    Highlights occurrences of search_text in a given PDF file.

    Parameters:
        pdf_path (str): Path to the original PDF file.
        output_pdf_path (str): Path where the highlighted PDF will be saved.
        search_text (str): Text to search and highlight.
        highlight_color (tuple): RGB color tuple (default is yellow: (1, 1, 0)).
    """
    doc = fitz.open(pdf_path)
    found_text = False  # Track if we found text

    # Split text into sentences
    sentences = sent_tokenize(search_text)
    
    for page in doc:
        for sentence in sentences:
            text_instances = page.search_for(sentence)
            if text_instances:  # If sentence is found
                found_text = True
            for inst in text_instances:
                highlight = page.add_highlight_annot(inst)
                highlight.set_colors(stroke=highlight_color)
                highlight.update()

    if found_text:
        doc.save(output_pdf_path)
        print(f"Highlighted PDF saved as {output_pdf_path}")
    else:
        print(f"No matches found in {pdf_path}. Skipping.")

    doc.close()

def process_pdfs_in_folder(folder_path, search_text):
    """
    Processes all PDF files in the given folder and highlights the search text.

    Parameters:
        folder_path (str): Path to the folder containing PDFs.
        search_text (str): Text to search and highlight.
    """
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):  # Process only PDFs
            pdf_path = os.path.join(folder_path, filename)
            output_pdf_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}_highlighted.pdf")

            highlight_text_in_pdf(pdf_path, output_pdf_path, search_text)
# Example usage:
# highlight_text_in_pdf("sample.pdf", "sample_highlighted.pdf", "retrieved snippet")

if __name__ == "__main__":
        # Start a TruSession to record feedback
    
        # Define the folder containing the PDFs
    PDF_FOLDER = "C:/Users/lukan/Desktop/Projects/FEL/PVTY1/FELChat/data/"

    # Get a list of all PDF files in the folder
    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    print("PDFs: ",pdf_files)
    # Load all PDFs using SimpleDirectoryReader
    documents = SimpleDirectoryReader(input_files=pdf_files).load_data()
    index_dir = "./custom_index"

        # Instantiate your custom retrieval RAG
    rag = RAG(documents, index_dir, sentence_window_size=5)

    # ---------------------------
    # Set up feedback functions for evaluation
    # ---------------------------
    from trulens.core import Feedback, Select
    from trulens.providers.openai import OpenAI as OpenAIFeedbackProvider

    # Use GPT-4 for feedback measurements
    provider = OpenAIFeedbackProvider(model_engine="gpt-4")

    # Define a groundedness feedback function
    f_groundedness = (
        Feedback(
            provider.groundedness_measure_with_cot_reasons, name="Groundedness"
        )
        .on(Select.RecordCalls.retrieve.rets.collect())
        .on_output()
    )
    # Answer relevance feedback (between question and answer)
    f_answer_relevance = (
        Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
        .on_input()
        .on_output()
    )
    # Context relevance feedback (between question and each context chunk)
    f_context_relevance = (
        Feedback(
            provider.context_relevance_with_cot_reasons, name="Context Relevance"
        )
        .on_input()
        .on(Select.RecordCalls.retrieve.rets[:])
        .aggregate(np.mean)  # you can choose a different aggregation method if you wish
    )

    # Construct the TruLens app for the RAG system
    from trulens.apps.app import TruApp

    tru_rag = TruApp(
        rag,
        app_name="RAG",
        app_version="base",
        feedbacks=[f_groundedness, f_answer_relevance, f_context_relevance],
    )

    # ---------------------------
    # Run the app and record queries
    # ---------------------------
    with open("benchmark.txt", "r") as f:
        benchmark_questions = [line.strip() for line in f if line.strip()]
    folder = "C:/Users/lukan/Desktop/Projects/FEL/PVTY1/FELChat/data/"
    # Run the queries using the TruLens context manager
    with tru_rag as recording:
        for idx, question in enumerate(benchmark_questions, start=1):
            answer, context_str = rag.query(question)
            print(f"Query {idx}: {question}")
            print("Answer:", answer)
            print("-" * 50)
            print("Context:", context_str)
            process_pdfs_in_folder(folder, context_str[0])
            print("=" * 50)


    print("\nLeaderboard Results:")
    print(rag.session.get_leaderboard())

    from trulens.dashboard import run_dashboard

    # Uncomment the next line to launch the dashboard (this may open in a new tab)
    run_dashboard()
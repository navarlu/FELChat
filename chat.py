#!/usr/bin/env python
"""
chat_terminal.py

This script loads your RAG retrieval engine (from evaluation2.py),
and then starts an interactive terminal chat. You are prompted
to enable TrueVals evaluation for every prompt. If enabled, the
queries are recorded via TruLens for evaluation.
"""

import os
import glob
import json
import numpy as np

# Import the RAG class from your evaluation2.py file.
# Make sure evaluation2.py is in the same folder or adjust the import path.
from evaluation2 import RAG

# Import PDF reader (used in your evaluation2.py code)
from llama_index.core import SimpleDirectoryReader
from trulens.dashboard import run_dashboard
# Import TrueVals/TruLens classes for evaluation
from trulens.apps.app import TruApp
from trulens.core import Feedback, Select
from trulens.providers.openai import OpenAI as OpenAIFeedbackProvider

def init_rag():
    """
    Loads your documents from the PDF folder, builds (or loads) the index,
    and instantiates the RAG retrieval engine.
    """
    # Set your PDF folder (adjust this path as needed)
    PDF_FOLDER = "C:/Users/lukan/Desktop/Projects/FEL/PVTY1/FELChat/data/"
    
    # Get all PDF files in the folder
    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    print("Found PDFs:", pdf_files)
    
    # Load documents using your SimpleDirectoryReader
    documents = SimpleDirectoryReader(input_files=pdf_files).load_data()
    
    # Specify the directory to persist the index
    index_dir = "./custom_index"
    
    # Create the RAG engine with your documents and desired sentence window size
    rag_instance = RAG(documents, index_dir, sentence_window_size=3)
    return rag_instance

def interactive_chat(rag_instance):
    """
    Runs an interactive loop: reads user input from terminal,
    calls rag_instance.query on each prompt, and prints the answer.
    """
    print("\nChatbot is ready. Type your question and press Enter.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
        
        # Get answer from the RAG engine (which does retrieval and generation)
        answer = rag_instance.query(user_input)
        print("Bot:", answer)
        print("-" * 50)

def chat_loop(rag_instance, enable_evaluation=False, tru_rag_instance=None):
    """
    Runs the interactive chat.
    If evaluation is enabled and tru_rag_instance is provided, the chat
    is run inside the TruApp context so that every query is recorded.
    """
    if enable_evaluation and tru_rag_instance:
        with tru_rag_instance as recording:
            interactive_chat(rag_instance)
            # After chat, you can print evaluation leaderboard results.
            print("\nLeaderboard Results:")
            # The tru_rag context holds a TruSession with the recorded data.
            # (Adjust attribute names if needed.)
            print(rag_instance.session.get_leaderboard())
            run_dashboard(port=59239)
    else:
        interactive_chat(rag_instance)

    

if __name__ == "__main__":
    
    # Ask the user if they want to enable TrueVals evaluation
    #enable_eval = input("Enable TrueVals evaluation for every prompt? (yes/no): ").strip().lower() in ["yes", "y"]
    enable_eval = True
    # Initialize the RAG engine (loads PDFs, builds/loads index, etc.)
    rag_instance = init_rag()
    
    tru_rag_instance = None
    if enable_eval:
        # Set up the TrueVals evaluation feedback functions using GPT-4.
        provider = OpenAIFeedbackProvider(model_engine="gpt-4")
        
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
        
        # Create a TruApp instance wrapping your RAG engine
        tru_rag_instance = TruApp(
            rag_instance,
            app_name="RAG",
            app_version="base",
            feedbacks=[f_groundedness, f_answer_relevance, f_context_relevance]
        )
    
    # Start the chat loop (with or without evaluation)
    chat_loop(rag_instance, enable_evaluation=enable_eval, tru_rag_instance=tru_rag_instance)
    

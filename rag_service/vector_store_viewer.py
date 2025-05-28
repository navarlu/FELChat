import streamlit as st
import os
from llama_index.core import load_index_from_storage, StorageContext

INDEX_DIR = "data/vectorstore/index_storage/"

@st.cache_data  # Ensures cache is cleared when reloading
def load_index(name):
    """
    Loads an index from storage.
    """
    index_path = os.path.join(INDEX_DIR, name)
    if not os.path.exists(index_path):
        st.error(f"Index '{name}' does not exist.")
        return None
    
    storage_context = StorageContext.from_defaults(persist_dir=index_path)
    index = load_index_from_storage(storage_context)
    return index

def display_index(name):
    """
    Displays stored document information from the specified index.
    """
    index = load_index(name)
    if index is None:
        return
    
    st.title(f"📂 Documents in Index: {name}")

    documents = index.docstore.docs  # Retrieve stored documents

    if not documents:
        st.warning("No documents found in this index.")
        return
    
    for doc_id, doc in documents.items():
        with st.expander(f"📜 Document ID: {doc_id}"):
            st.write(f"**Content:** {doc.text[:500]}...")  # Show first 500 characters
            st.json(doc.metadata)

# Streamlit UI
st.sidebar.title("Index Viewer")
index_name = st.sidebar.text_input("Enter Index Name", "index_email")

if st.sidebar.button("Load Index"):
    st.cache_data.clear()  # 🔄 Clear cache to force reload
    display_index(index_name)
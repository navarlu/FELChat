from llama_index.core import VectorStoreIndex, Document

# Dictionary to store multiple named indexes
index_store = {}

def create_index_store(name):
    """
    Creates a named index vector store.
    
    Parameters:
    - name: The unique name for the index store.

    Returns:
    - The created VectorStoreIndex instance.
    """
    if name in index_store:
        raise ValueError(f"Index with name '{name}' already exists.")
    
    index_store[name] = VectorStoreIndex([])
    return index_store[name]

def add_to_index_store(name, documents):
    """
    Adds new documents to the specified named index store.
    
    Parameters:
    - name: The name of the existing index store.
    - documents: A list of Document objects to be added.
    """
    if name not in index_store:
        raise ValueError(f"Index with name '{name}' does not exist.")
    
    index = index_store[name]
    index.insert(documents)

# Example Usage
if __name__ == "__main__":
    # Create a named index store
    index_name = "my_special_index"
    create_index_store(index_name)

    # Create documents
    documents = [
        Document(text="LlamaIndex allows efficient retrieval."),
        Document(text="AI applications benefit from vector search.")
    ]

    # Add documents to the named index store
    add_to_index_store(index_name, documents)

    print(f"Documents added to index '{index_name}' successfully.")
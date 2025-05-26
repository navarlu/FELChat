import os
import threading
import json
import shutil
import PyPDF2  
import torch
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.indices.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings 


# One global embedder – use CPU/GPU as you like
EMBED_MODEL = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en",            # ★ your choice
    device="cuda" if torch.cuda.is_available() else "cpu",
)
Settings.embed_model = EMBED_MODEL
# Make a service-context that every Index / QueryEngine will inherit

class IndexManager:
    def __init__(self, index_name, index_dir, window_size):
        self.index_name = index_name
        self.index_path = os.path.join(index_dir, index_name)
        self.lock = threading.RLock()
        self.window_size = window_size
        self.index = self._create_or_load_index()
        self.query_engine = self._build_sentence_window_engine()

    def _create_or_load_index(self) -> VectorStoreIndex:
        if os.path.exists(self.index_path):
            print(f"[IndexManager] Loading existing index: {self.index_name}")
            storage_ctx = StorageContext.from_defaults(persist_dir=self.index_path)
            return load_index_from_storage(storage_ctx)
        else:
            print(f"[IndexManager] Creating new index: {self.index_name}")
            os.makedirs(self.index_path, exist_ok=True)
            print("[IndexManager] Created new index. step2")
            idx = VectorStoreIndex([])
            print("[IndexManager] Created new index. step3")
            idx.storage_context.persist(self.index_path)
            print("[IndexManager] Created new index. step4")
            return idx

    def _build_sentence_window_engine(self):
        postprocessor = MetadataReplacementPostProcessor(target_metadata_key="window")
        rerank = SentenceTransformerRerank(
            top_n=4, 
            model="BAAI/bge-reranker-base"
        )
        

        engine = self.index.as_query_engine(
            similarity_top_k=6,
            node_postprocessors=[postprocessor, rerank],
            response_mode="no_text"
        )
        return engine

    def add_documents(self, docs):
        with self.lock:
            # Convert to nodes with the sentence window parser
            parser = SentenceWindowNodeParser.from_defaults(
                window_size=self.window_size,
                window_metadata_key="window",
                original_text_metadata_key="original_sentence",
            )
            nodes = parser.get_nodes_from_documents(docs)
            self.index.insert_nodes(nodes)
            self.index.storage_context.persist(self.index_path)
            # Rebuild the engine so queries see new documents:
            self.query_engine = self._build_sentence_window_engine()
            print(f"[IndexManager] Added {len(docs)} documents.")

    def remove_by_email_id(self, email_id: str) -> int:
        with self.lock:
            docstore = self.index.docstore
            to_remove = [
                d_id for d_id, d_obj in docstore.docs.items()
                if d_obj.metadata.get("email_id") == email_id
            ]
            if not to_remove:
                return 0

            for doc_id in to_remove:
                self.index.delete(node_ids=[doc_id], delete_from_docstore=True)
                print(f"[IndexManager] Deleted doc_id={doc_id}")
            
            print(f"[IndexManager] Docstore AFTER removing email_id={email_id}, BEFORE persist:")
            print(self.list_documents())

            self.index.storage_context.persist(self.index_path)
            self.query_engine = self._build_sentence_window_engine()
            
            print(f"[IndexManager] Docstore AFTER removing email_id={email_id}, AFTER persist & engine rebuild:")
            print(self.list_documents())

            print(f"[IndexManager] Removed {len(to_remove)} docs for email_id={email_id}")
            return len(to_remove)

    def rebuild_index(self, in_database_folder):
        print(f"[IndexManager] Rebuilding Index")
        with self.lock:
            if os.path.exists(self.index_path):
                shutil.rmtree(self.index_path)
            os.makedirs(self.index_path, exist_ok=True)
            
            self.index = VectorStoreIndex([])
            self.index.storage_context.persist(self.index_path)
            
            documents = []
            for filename in os.listdir(in_database_folder):
                if filename.endswith(".json"):
                    file_path = os.path.join(in_database_folder, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        text = f"Q: {data['question']}\nA: {data['answer']}"
                        metadata = {
                            "email_id": data["email_id"],
                            "timestamp": data["timestamp"]
                        }
                        documents.append(Document(text=text, metadata=metadata))
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
            
            if documents:
                self.add_documents(documents)
            else:
                print("No documents found in the in_database folder.")
            
            self.query_engine = self._build_sentence_window_engine()
            print("[IndexManager] Rebuilt index from remaining documents.")

    def get_query_engine(self):
        return self.query_engine

    def list_documents(self):
        with self.lock:
            return {
                d_id: d.metadata for d_id, d in self.index.docstore.docs.items()
            }

    def load_json_documents(self, folder_path, destination_folder):
        documents = []
        os.makedirs(destination_folder, exist_ok=True)

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if "question" in data and "answer" in data:
                        question = data["question"].replace("\n", " ").strip()
                        answer = data["answer"].replace("\n", " ").strip()
                        text = f"Q: {question}\nA: {answer}"
                    elif "information" in data:
                        information = data["information"].replace("\n", " ").strip()
                        text = f"information: {information}"
                    else:
                        print(f"File {filename} does not have expected keys.")
                        continue

                    metadata = {
                        "email_id": data["email_id"],
                        "timestamp": data["timestamp"]
                    }
                    documents.append(Document(text=text, metadata=metadata))

                    shutil.move(file_path, os.path.join(destination_folder, filename))
                    print(f"Processed and moved file: {filename}")

                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON file {filename}: {e}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

        return documents

    def add_jsons_to_index(self, folder_path, destination_folder):
        documents = self.load_json_documents(folder_path, destination_folder)
        if not documents:
            print("No valid JSON documents found.")
            return

        self.add_documents(documents)

    # New function: Load PDF documents by extracting text
    def load_pdf_documents(self, folder_path, destination_folder):
        documents = []
        os.makedirs(destination_folder, exist_ok=True)

        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text
                    metadata = {
                        "file_name": filename,
                        "source": "pdf"
                    }
                    documents.append(Document(text=text, metadata=metadata))

                    shutil.move(file_path, os.path.join(destination_folder, filename))
                    print(f"Processed and moved PDF file: {filename}")
                except Exception as e:
                    print(f"Error processing PDF file {filename}: {e}")

        return documents

    # New function: Add PDF documents to the index
    def add_pdfs_to_index(self, folder_path, destination_folder):
        documents = self.load_pdf_documents(folder_path, destination_folder)
        if not documents:
            print("No valid PDF documents found.")
            return

        self.add_documents(documents)

# rag_service.py

from trulens.apps.app import instrument
from trulens.core import TruSession

class RAGService:
    def __init__(self, index_manager):
        self.index_manager = index_manager
        self.session = TruSession()
        self.conversation_history = []

    @instrument
    def retrieve(self, query: str) -> list:
        """
        Use the manager's (sentence-window) query engine for retrieval.
        """
        engine = self.index_manager.get_query_engine()
        print("[RAGService] docstore at retrieval time:")
        print(self.index_manager.list_documents())
        results = engine.query(query)

        unique_email_ids = set()
        unique_texts = []
        for source_node in results.source_nodes:
            node = getattr(source_node, "node", source_node)
            email_id = node.metadata.get("email_id")
            if email_id not in unique_email_ids:
                unique_email_ids.add(email_id)
                unique_texts.append(node.text)
        return unique_texts

    @instrument
    def generate_completion(self, query: str, context_docs: list[str]) -> str:
        """
        Whichever function you used to call OpenAI. For example:
        """
        # Pseudocode:
        # prompt = build_prompt(query, context_docs, conversation_history)
        # call openai.ChatCompletion.create(...)
        # return that text
        return self.generate_answer(query, context_docs)

    @instrument
    def query(self, query: str):
        """
        The overall RAG pipeline: retrieval + generation
        """
        docs = self.retrieve(query)
        answer = self.generate_completion(query, docs)
        return answer, docs
    
    def generate_answer(self, user_question, retrieved_documents, model_temperature=0.1, model_name="gpt-4o-mini"):
        """
        Generates an answer using OpenAI's API based on retrieved documents.
        This version instructs the LLM to only report the exact data found and its source.
        """
        if not retrieved_documents:
            return "No relevant documents found to answer the question."

        # Construct the context prompt using the retrieved documents.
        context = "\n\n".join([f"Document {idx + 1}: {doc}" for idx, doc in enumerate(retrieved_documents)])
        
        # Revised system message instructing the LLM to simply report what was found.
        system_message = f"""
    You are a factual assistant. Your task is to report exactly what data was found in the provided documents for the given query, and indicate where that information was located (for example, by document number or page number). 

    Important Guidelines:
    - Do not add any additional explanations or interpretations.
    - Only use the information explicitly provided in the documents.
    - If multiple documents contain relevant information, list each separately.
    - If there is any ambiguity, simply state the data as found without making assumptions.
    - Answer in Czech language.
    """

        prompt = f'''
    ---------------------------------------------------------------
    Context from retrieved documents:

    {context}
    ---------------------------------------------------------------
    Query: {user_question}
    ---------------------------------------------------------------
    '''
        messages = [{"role": "system", "content": system_message}]
        
        # Append previous conversation history if available
        if self.conversation_history:
            messages.extend(self.conversation_history)

        # Add the current user message with the prompt
        messages.append({"role": "user", "content": prompt})

        import json
        print("Messages:\n" + json.dumps(messages, indent=4, ensure_ascii=False))

        try:
            from openai import OpenAI as OpenAI2
            client = OpenAI2()
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=model_temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"
     

    def generate_answer_ema(self, user_question, retrieved_documents, model_temperature=0.1, model_name="gpt-4o-mini"):
        """
        Generates an answer using OpenAI's API based on retrieved documents.
        """
        if not retrieved_documents:
            return "No relevant documents found to answer the question."

        # Construct the context prompt using the retrieved documents.
        context = "\n\n".join([f"Document {idx + 1}: {doc}" for idx, doc in enumerate(retrieved_documents)])
        #print(context)
        system_message = f"""

    You are a helpful email assistant that answers customer inquiries based on provided documents.
    From user you will recieve his question and context in related documents.

    Important Guidelines:
    - Always prioritize information from the most recent document. 
    - If newer information conflicts with older documents, only use the latest (most recent) document.

    Example:
    If the customer asks "Do you offer delivery to Germany?" and the documents provided are:

    Document 1 (newest):
    "We no longer offer international shipping; delivery is available only within the Czech Republic."

    Document 2 (older):
    "We deliver to countries including Germany, Austria, and Slovakia."

    Correct Response:
    "Currently, we only offer delivery within the Czech Republic."

    Incorrect Response:
    "Yes, we deliver to Germany."

    Now, compose a clear, concise, and polite email response to the customer's inquiry based strictly on the above guidelines.
    """
        prompt= f'''
    ---------------------------------------------------------------
    Context from retrieved documents (sorted from newest to oldest):

    {context}
    ---------------------------------------------------------------
    Customer Question: {user_question}
    ---------------------------------------------------------------
    '''
        messages = [{"role": "system", "content": system_message}]
        
        # Append previous conversation history if available
        if self.conversation_history:
            messages.extend(self.conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": prompt})

        import json

        print("Messages:\n" + json.dumps(messages, indent=4, ensure_ascii=False))

        try:
            from openai import OpenAI as OpenAI2
            client = OpenAI2()
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=model_temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"
    


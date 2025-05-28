# rag_service.py


import requests
import re
import time
class RAGService:
    def __init__(self, index_manager):
        self.index_manager = index_manager
        
        self.conversation_history = []
        # self.server_url = "https://fe9b-2001-718-2-1634-9edc-71ff-fe40-7be2.ngrok-free.app/chat"
        # self.server_url = "https://924b-2001-718-2-1634-9edc-71ff-fe40-7be2.ngrok-free.app/chat"
        # self.server_url = "https://924b-2001-718-2-1634-9edc-71ff-fe40-7be2.ngrok-free.app/chat"
        self.server_url = "http://localhost:8003/chat"





    
    def retrieve(self, query: str) -> list:
        """
        Use the manager's (sentence-window) query engine for retrieval.
        """

        engine = self.index_manager.get_query_engine()

        print("[RAGService] docstore at retrieval time:")

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

    
    def generate_completion(self, query: str, context_docs: list[str]) -> str:
        """
        Whichever function you used to call OpenAI. For example:
        """
        # Pseudocode:
        # prompt = build_prompt(query, context_docs, conversation_history)
        # call openai.ChatCompletion.create(...)
        # return that text
        return self.generate_answer(query, context_docs)

    
    def query(self, query: str):
        timings = {}

        # Measure retrieval
        t0 = time.time()
        docs = self.retrieve(query)
        t1 = time.time()
        timings["retrieval_time_sec"] = t1 - t0

        # Measure answer generation
        t2 = time.time()
        answer, context, messages = self.generate_completion(query, docs)
        t3 = time.time()
        timings["generation_time_sec"] = t3 - t2

        timings["rag_total_time_sec"] = t3 - t0

        return answer, docs, context, messages, timings
        
    
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
    You are FEE.lix a chatbot assistant for faculty of electrical engineering in Prague. 

    Important Guidelines:
    - Do not add any additional explanations or interpretations.
    - Only use the information explicitly provided in the documents.
    - If there is any ambiguity, simply state the data as found without making assumptions.
    - Answer in English language.
    - Answer exclusively what user asked about and do not add any additional information.
    - Cite only like this: Article(10)(1). when the information is from the article 10 and point 1.
    - Answer in a conversational tone.
    - Keep the answer short and concise.
    - Answer yes or no if the question is you can and then add short explanation.
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
            answer = self.send_prompt(messages)
            return answer, context, messages
        except Exception as e:
            return f"Error generating response: {str(e)}"
     

    def send_prompt(self,prompt):
        response = requests.post(self.server_url, json={"prompt": prompt})
        if response.status_code == 200:
            full_response = response.json()["response"]
            # Find all assistant responses
            matches = re.findall(r"<\|assistant\|>\s*(.*?)(?=<\|user\|>|$)", full_response, re.DOTALL)
            if matches:
                return matches[-1].strip()  # Get the last assistant response
            else:
                return full_response.strip()
        else:
            return f"Chyba: {response.status_code} - {response.text}"


    
     


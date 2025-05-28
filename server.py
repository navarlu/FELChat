import os
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer

# Setup
print("Setting up environment and GPU...")

os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Set which GPU to use
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Choose ONE model to load
model_name = "tiiuae/falcon-rw-1b"  # or "microsoft/phi-2", "distilgpt2"
print(f"Loading model {model_name}. Please wait...")

# Load model and tokenizer
try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True,
        device_map="auto",  # Auto-assign model to available device
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print("Model and tokenizer successfully loaded!")
except Exception as e:
    print("Error loading model:", e)
    raise e

# Initialize Flask app
app = Flask(__name__)
print("Flask app initialized.")

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("prompt", [])
    print("Received request with prompt:", messages)

    # Build chat text
    text = ""
    for msg in messages:
        text += f"<|{msg['role']}|>\n{msg['content']}\n"
    text += "<|assistant|>\n"
    print("Chat template applied, resulting text:\n", text)

    # Tokenize and move inputs to model device
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    print("Inputs converted to tensor and moved to model device.")

    # Generate output
    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            pad_token_id=tokenizer.eos_token_id
        )
    print("Response generation completed.")

    # Decode output
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("Response decoding completed.")
    print("Final response:\n", answer)

    return jsonify({"response": answer})

# Start the server
if __name__ == "__main__":
    print("Starting Flask server locally...")
    app.run(host="0.0.0.0", port=8003, debug=True)

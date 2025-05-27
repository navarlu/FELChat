import os
import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Setting up environment and GPU...")

# Configure GPU (allowed devices are 0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Model name: Llama 3 8B Instruct

model_name = "distilgpt2"
model_name = "microsoft/Phi-2"
model_name = "tiiuae/falcon-rw-1b"
print(f"Loading model {model_name}. Please wait...")

try:
    model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,  # Use float32 for CPU
    low_cpu_mem_usage=True,
    device_map={"": "cpu"},
    offload_folder="./offload"
)
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        
    )
    print("Model and tokenizer successfully loaded!")
except Exception as e:
    print("Error loading model:", e)
    raise e

# Initialize Flask app
app = Flask(__name__)
print("Flask app initialized.")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("prompt", [])
    print("Received request with prompt:", messages)

    # Build chat template
    text = ""
    for msg in messages:
        text += f"<|{msg['role']}|>\n{msg['content']}\n"
    text += "<|assistant|>\n"
    print("Chat template applied, resulting text:\n", text)
    #text = "hi"
    # Tokenize and move to device
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    print("Inputs converted to tensor and moved to model device.")

    # Generate response
    print("Generating response...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            pad_token_id=tokenizer.eos_token_id
        )
    print("Response generation completed.")

    # Decode result
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("Response decoding completed.")
    print("Final response:\n", answer)

    return jsonify({"response": answer})

if __name__ == "__main__":
    print("Starting Flask server locally...")
    app.run(host="0.0.0.0", port=8003, debug=True)

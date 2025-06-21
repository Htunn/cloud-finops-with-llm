"""
Test local LLM functionality.
"""
import os
import torch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_local_llm():
    print("Testing Local LLM inference...")
    
    try:
        # Check if models directory exists with downloaded model
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        model_path = os.path.join("models", "tiny-llama")
        
        print(f"Looking for model in {model_path}")
        if not os.path.exists(model_path):
            print("❌ Model directory not found.")
            return False
        
        # Check device availability
        if torch.backends.mps.is_available():
            device = "mps"
            print("✅ MPS (Apple Silicon GPU) is available")
        else:
            device = "cpu"
            print("ℹ️ MPS not available, using CPU")
        
        # Import required modules
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=device,
            torch_dtype=torch.float16 if device == "mps" else torch.float32
        )
        
        # Test with a simple FinOps-related prompt
        prompt = "What are some ways to optimize AWS EC2 costs?"
        formatted_prompt = f"<|user|>\n{prompt}\n<|assistant|>"
        
        # Generate response
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
        
        # Decode and return the response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print("\n✅ Local LLM test successful!")
        print("\nPrompt:", prompt)
        print("\nResponse:", response)
        return True
        
    except Exception as e:
        print(f"❌ Error testing Local LLM: {str(e)}")
        return False

if __name__ == "__main__":
    test_local_llm()

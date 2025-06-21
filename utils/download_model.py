#!/usr/bin/env python3
"""
Script to download and set up the Microsoft Phi-4 model for local inference.
"""
import os
import logging
import argparse
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Model parameters
DEFAULT_MODEL = "microsoft/Phi-4-mini-4k-instruct"
MODEL_PATH = os.getenv("LOCAL_LLM_MODEL_PATH", DEFAULT_MODEL)
USE_GPU = os.getenv("LOCAL_LLM_USE_GPU", "true").lower() == "true"


def download_model(model_id: str, output_dir: str = "models/phi-4", use_gpu: bool = True):
    """
    Download and save the model for local inference.
    
    Args:
        model_id: The model ID on Hugging Face
        output_dir: Directory to save the model
        use_gpu: Whether to use GPU for inference
    """
    try:
        logger.info(f"Checking for device capabilities...")
        device = "mps" if torch.backends.mps.is_available() and use_gpu else "cpu"
        logger.info(f"Using device: {device}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure quantization for efficient loading
        logger.info(f"Configuring model quantization...")
        quant_config = None  # Disable quantization for testing
        
        # Download and save tokenizer
        logger.info(f"Downloading tokenizer from {model_id}...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        tokenizer.save_pretrained(output_dir)
        logger.info(f"Tokenizer saved to {output_dir}")
        
        # Download and save model
        logger.info(f"Downloading model from {model_id}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device,
            torch_dtype=torch.float16 if device == "mps" else torch.float32,
            quantization_config=quant_config if device == "mps" else None,
            trust_remote_code=True
        )
        model.save_pretrained(output_dir)
        logger.info(f"Model saved to {output_dir}")
        
        # Test the model
        test_inference(output_dir)
        
        logger.info(f"Model setup complete. You can now use the model for local inference.")
        
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise


def test_inference(model_dir: str):
    """
    Test the downloaded model with a simple inference.
    
    Args:
        model_dir: Directory containing the model
    """
    try:
        logger.info("Testing model with a simple inference...")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        
        device = "mps" if torch.backends.mps.is_available() and USE_GPU else "cpu"
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            device_map=device,
            torch_dtype=torch.float16 if device == "mps" else torch.float32,
            trust_remote_code=True
        )
        
        # Test prompt
        prompt = "<|user|>\nWhat is FinOps and how can it help with cloud cost management?\n<|assistant|>"
        
        # Tokenize and generate
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info(f"Model test successful.")
        logger.info(f"Sample response: {response[:100]}...")
        
    except Exception as e:
        logger.error(f"Error testing model inference: {e}")
        logger.warning("Model download completed, but inference test failed.")


def main():
    """Main function to download and set up the model."""
    parser = argparse.ArgumentParser(description="Download and set up Microsoft Phi-4 model for local inference.")
    parser.add_argument("--model", type=str, default=MODEL_PATH, help=f"Hugging Face model ID (default: {MODEL_PATH})")
    parser.add_argument("--output", type=str, default="models/phi-4", help="Output directory (default: models/phi-4)")
    parser.add_argument("--gpu", action="store_true", default=USE_GPU, help="Use GPU acceleration if available")
    
    args = parser.parse_args()
    
    logger.info(f"Starting model download process...")
    logger.info(f"Model: {args.model}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Use GPU: {args.gpu}")
    
    download_model(args.model, args.output, args.gpu)


if __name__ == "__main__":
    main()

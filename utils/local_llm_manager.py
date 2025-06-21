"""
Local LLM (TinyLlama) integration module with M3 GPU acceleration.
"""
import os
import logging
import torch
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LocalLLMManager:
    """Class to manage local LLM (TinyLlama) interactions."""
    
    def __init__(self, model_path: Optional[str] = None) -> None:
        """
        Initialize local LLM model.
        
        Args:
            model_path: Path to the model, defaults to value from environment variable
        """
        # Default to TinyLlama model if not specified
        self.model_path = model_path or os.getenv("LOCAL_LLM_MODEL_PATH", "models/tiny-llama")
        self.use_gpu = os.getenv("LOCAL_LLM_USE_GPU", "true").lower() == "true"
        
        self.device = "mps" if torch.backends.mps.is_available() and self.use_gpu else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        try:
            logger.info(f"Loading model from {self.model_path}...")
            
            # Configure quantization for efficient loading
            # Don't use quantization on MPS (Apple Silicon) as it's not fully supported
            quant_config = None
            if self.device == "cpu":
                try:
                    # Updated config for compatibility with latest bitsandbytes
                    quant_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                        bnb_4bit_use_double_quant=True
                    )
                    logger.info("Created 4-bit quantization config")
                except Exception as e:
                    logger.warning(f"Failed to create quantization config: {e}. Falling back to non-quantized model.")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            try:
                # Load model - use float16 for MPS without quantization for better compatibility
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    device_map=self.device,
                    torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
                    quantization_config=quant_config
                )
                logger.info("Local LLM model loaded successfully.")
            except ValueError as ve:
                if "bitsandbytes" in str(ve) and "8-bit" in str(ve):
                    logger.warning("Quantization error with bitsandbytes. Retrying without quantization.")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map=self.device,
                        torch_dtype=torch.float16 if self.device == "mps" else torch.float32
                    )
                    logger.info("Local LLM model loaded successfully without quantization.")
                else:
                    raise
        except Exception as e:
            logger.error(f"Error loading local LLM model: {e}")
            
            # Try to load without any quantization as a fallback
            try:
                logger.info("Attempting to load model without quantization as a fallback...")
                
                # First attempt with safetensors (often more reliable)
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map=self.device if self.device == "mps" else "auto",
                        torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
                        trust_remote_code=True,
                        use_safetensors=True
                    )
                except Exception:
                    # If safetensors fails, try without it
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map=self.device if self.device == "mps" else "auto",
                        torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
                        trust_remote_code=True,
                        use_safetensors=False
                    )
                    
                logger.info("Local LLM model loaded successfully with fallback method.")
            except Exception as second_error:
                logger.error(f"Fallback loading also failed: {second_error}")
                raise RuntimeError(f"Failed to load the model: {e}. Fallback attempt also failed: {second_error}")
    
    def generate_response(self, prompt: str, max_length: int = 1000) -> str:
        """
        Generate a response from the local LLM.
        
        Args:
            prompt: Input prompt text
            max_length: Maximum length of the generated response
            
        Returns:
            Generated response text
        """
        try:
            # Format the prompt for the model
            formatted_prompt = f"<|user|>\n{prompt}\n<|assistant|>"
            
            # Encode the prompt
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode and return the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            assistant_response = response.split("<|assistant|>")[-1].strip()
            
            return assistant_response
        
        except Exception as e:
            logger.error(f"Error generating response with local LLM: {e}")
            raise
    
    def analyze_cost_data(self, cost_data: List[Dict[str, Any]], query: str) -> str:
        """
        Analyze cost data using the local LLM.
        
        Args:
            cost_data: Cost data to analyze
            query: User query about the cost data
            
        Returns:
            Analysis text
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:10]])
            if len(cost_data) > 10:
                cost_data_str += f"\n... and {len(cost_data) - 10} more items"
            
            prompt = f"""You are a FinOps AI assistant. I need you to analyze this AWS cost data and answer my question.

Here is my AWS cost data:
{cost_data_str}

My question is: {query}

Please provide a detailed analysis based on this data."""
            
            return self.generate_response(prompt, max_length=1500)
        
        except Exception as e:
            logger.error(f"Error analyzing cost data with local LLM: {e}")
            return f"Error analyzing cost data: {str(e)}"
    
    def generate_cost_insights(self, cost_data: List[Dict[str, Any]]) -> str:
        """
        Generate cost insights using the local LLM.
        
        Args:
            cost_data: Cost data to analyze
            
        Returns:
            Cost insights text
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:15]])
            if len(cost_data) > 15:
                cost_data_str += f"\n... and {len(cost_data) - 15} more items"
            
            prompt = f"""You are a FinOps AI assistant. Analyze the following AWS cost data and provide insights.

AWS Cost Data:
{cost_data_str}

Please provide:
1. A summary of the current cost situation
2. Notable trends or patterns
3. Any services that seem to be costing more than expected
4. Potential areas for optimization

Format your response as a clear analysis."""
            
            return self.generate_response(prompt, max_length=2000)
        
        except Exception as e:
            logger.error(f"Error generating cost insights with local LLM: {e}")
            return f"Error generating cost insights: {str(e)}"

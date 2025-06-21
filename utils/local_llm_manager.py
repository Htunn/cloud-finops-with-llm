"""
Local LLM (Microsoft Phi-4) integration module with M3 GPU acceleration.
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
    """Class to manage local LLM (Microsoft Phi-4) interactions."""
    
    def __init__(self, model_path: Optional[str] = None) -> None:
        """
        Initialize local LLM model.
        
        Args:
            model_path: Path to the model, defaults to value from environment variable
        """
        self.model_path = model_path or os.getenv("LOCAL_LLM_MODEL_PATH", "microsoft/Phi-4-mini-4k-instruct")
        self.use_gpu = os.getenv("LOCAL_LLM_USE_GPU", "true").lower() == "true"
        
        self.device = "mps" if torch.backends.mps.is_available() and self.use_gpu else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        try:
            logger.info(f"Loading model from {self.model_path}...")
            
            # Configure quantization for efficient loading
            quant_config = BitsAndBytesConfig(
                load_in_8bit=True if self.device == "mps" else False,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=self.device,
                torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
                quantization_config=quant_config if self.device == "mps" else None
            )
            
            logger.info("Local LLM model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading local LLM model: {e}")
            raise
    
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

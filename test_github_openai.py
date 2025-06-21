"""
Test GitHub OpenAI integration.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to fix import issues
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Load environment variables
load_dotenv()

def test_github_openai():
    print("Testing GitHub OpenAI API integration...")
    
    try:
        from utils.github_openai_manager import GitHubOpenAIManager
        
        # Create GitHub OpenAI manager
        github_manager = GitHubOpenAIManager()
        
        # Check if token is set
        if not os.getenv("GITHUB_TOKEN"):
            print("❌ GitHub token not found in environment variables.")
            print("Please set the GITHUB_TOKEN environment variable in .env file.")
            return False
        
        # Test with a simple FinOps-related prompt
        prompt = "What are some ways to optimize AWS EC2 costs?"
        
        print("\n🔄 Generating response, this might take a moment...")
        response = github_manager.generate_response(prompt)
        
        if response and "Error" not in response:
            print("\n✅ GitHub OpenAI API test successful!")
            print("\nPrompt:", prompt)
            print("\nResponse:", response)
            return True
        else:
            print(f"\n❌ Error with GitHub OpenAI API: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GitHub OpenAI: {str(e)}")
        return False

if __name__ == "__main__":
    test_github_openai()

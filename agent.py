"""
This is a simple example of how to use the Empire Agent.
Please run the following command to install the necessary dependencies and store keys in .env:
!pip install empire-chain
"""
from datetime import datetime
from empire_chain.agent.agent import Agent
from dotenv import load_dotenv
from app import TaskTracker
from certificate_manager import CertificateManager
from web3 import Web3
import logging
import warnings
import os

# Suppress Web3 contract warnings
warnings.filterwarnings("ignore", category=UserWarning, module="web3.contract.base_contract")

# Set up logging to show only important steps
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Disable debug logs from other modules
logging.getLogger('web3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('groq').setLevel(logging.WARNING)

load_dotenv()

def create_task(description: str, deadline: str, assignee: str) -> str:
    """Create a new task using the TaskTracker contract."""
    try:
        logger.info(f"\nCreating task:")
        logger.info(f"Description: {description}")
        logger.info(f"Deadline: {deadline}")
        logger.info(f"Assignee: {assignee}")
        
        # Validate Ethereum address
        if not Web3.is_address(assignee):
            logger.error(f"❌ Invalid Ethereum address: {assignee}")
            return f"Error: Invalid Ethereum address format: {assignee}"
        
        # Validate deadline format
        try:
            datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error(f"❌ Invalid deadline format: {deadline}")
            return f"Error: Invalid deadline format. Please use 'YYYY-MM-DD HH:MM:SS' format"
        
        # Validate description
        if not description or len(description.strip()) == 0:
            logger.error("❌ Empty task description")
            return "Error: Task description cannot be empty"
        
        tracker = TaskTracker()
        result = tracker.create_task(description, deadline, assignee)
        
        if result['status'] == 'success':
            logger.info(f"✅ Task created successfully!")
            logger.info(f"Task ID: {result['task_id']}")
            logger.info(f"Transaction: {result['tx_hash']}")
            return f"Task created successfully! Task ID: {result['task_id']}, Transaction: {result['tx_hash']}"
        logger.error(f"❌ Task creation failed: {result['message']}")
        return f"Error creating task: {result['message']}"
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return f"Error in create_task: {str(e)}"

def generate_and_verify_certificate(
    name: str,
    template_path: str = "template.png",
    output_dir: str = "generated_certificates",
    font_path: str = "Montserrat-Bold.ttf",
    font_size: int = 100,
    y_position: int = 1000
) -> str:
    """Generate, authenticate, and verify a certificate using the CertificateAuthenticator contract."""
    try:
        logger.info(f"\nGenerating and verifying certificate:")
        logger.info(f"Name: {name}")
        logger.info(f"Template: {template_path}")
        logger.info(f"Output Directory: {output_dir}")
        
        # Validate inputs
        if not name or len(name.strip()) == 0:
            logger.error("❌ Empty name")
            return "Error: Name cannot be empty"
        
        if not os.path.exists(template_path):
            logger.error(f"❌ Template file not found: {template_path}")
            return f"Error: Template file not found: {template_path}"
        
        if not os.path.exists(font_path):
            logger.error(f"❌ Font file not found: {font_path}")
            return f"Error: Font file not found: {font_path}"
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output path
        output_path = os.path.join(output_dir, f"{name.replace(' ', '_')}_certificate.png")
        
        # Initialize certificate manager
        manager = CertificateManager()
        
        # Generate and authenticate certificate
        generation_result = manager.generate_certificate(
            template_path=template_path,
            name=name,
            output_path=output_path,
            font_path=font_path,
            font_size=font_size,
            y=y_position
        )
        
        if generation_result['status'] != 'success':
            logger.error(f"❌ Certificate generation failed: {generation_result['message']}")
            return f"Error generating certificate: {generation_result['message']}"
        
        # Verify the generated certificate
        verification_result = manager.verify_certificate(output_path)
        
        if verification_result['status'] != 'success':
            logger.error(f"❌ Certificate verification failed: {verification_result['message']}")
            return f"Error verifying certificate: {verification_result['message']}"
        
        # Prepare the complete response
        status = "valid" if verification_result['is_valid'] else "invalid"
        response = (
            f"✅ Certificate Process Complete!\n\n"
            f"Generation Details:\n"
            f"------------------\n"
            f"Certificate ID: {generation_result['certificate_id']}\n"
            f"Certificate Hash: {generation_result['certificate_hash']}\n"
            f"Transaction: {generation_result['tx_hash']}\n"
            f"Saved to: {generation_result['output_path']}\n\n"
            f"Verification Details:\n"
            f"-------------------\n"
            f"Status: {status}\n"
            f"Certificate Hash: {verification_result['certificate_hash']}\n"
        )
        
        logger.info(response)
        return response
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return f"Error in generate_and_verify_certificate: {str(e)}"

def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny!"

def calculate_distance(from_city: str, to_city: str) -> str:
    return f"The distance from {from_city} to {to_city} is 500km"

def get_time(timezone: str) -> str:
    return f"Current time in {timezone}: {datetime.now()}"

def translate_text(text: str, target_language: str) -> str:
    return f"Translated '{text}' to {target_language}: [translation would go here]"

def search_web(query: str, num_results: int) -> str:
    return f"Top {num_results} results for '{query}': [search results would go here]"

def main():
    # Create agent
    agent = Agent()
    
    # Register functions
    functions = [
        create_task,
        generate_and_verify_certificate,
        get_weather,
        calculate_distance,
        get_time,
        translate_text,
        search_web
    ]
    
    for func in functions:
        agent.register_function(func)
    
    # Example:         "Create a task 'Complete project documentation' with deadline '2025-07-31 23:59:59' for assignee '0x1234567890123456789012345678901234567890'",
    queries = [
        "Generate and verify a certificate for 'Harshit Malik'"
    ]
    
    # Process queries
    for query in queries:
        try:
            logger.info(f"\nProcessing query: {query}")
            result = agent.process_query(query)
            logger.info(f"Result: {result['result']}")
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}")

if __name__ == "__main__":
    main()
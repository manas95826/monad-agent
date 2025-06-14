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
from notice_manager import NoticeManager
from web3 import Web3
import logging
import warnings
import os
from leave_management import LeaveManagement
from payment_handler import handle_employee_payment as payment_handler

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
        
        # Check if contract is properly initialized
        if not manager.contract.address:
            logger.error("❌ Certificate contract not initialized")
            return "Error: Certificate contract address not set. Please check your .env file"
        
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
        
        # Add a small delay to ensure the transaction is mined
        import time
        time.sleep(2)
        
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
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return f"Error in generate_and_verify_certificate: {str(e)}"

def create_notice(category: str, description: str, priority: int, content: str) -> str:
    """Create a new notice using the NoticeManager contract."""
    try:
        if not os.getenv('CONTRACT_ADDRESS'):
            return "Error: CONTRACT_ADDRESS not set in .env file. Please deploy the contract and set the address."
            
        logger.info(f"Creating notice with parameters:")
        logger.info(f"Category: {category}")
        logger.info(f"Description: {description}")
        logger.info(f"Priority: {priority}")
        logger.info(f"Content length: {len(content)} characters")
        logger.info(f"Contract Address: {os.getenv('CONTRACT_ADDRESS')}")
        
        manager = NoticeManager()
        result = manager.create_notice(category, description, priority, content)
        
        if result['status'] == 'success':
            logger.info(f"Transaction successful: {result['tx_hash']}")
            return f"Notice created successfully! Transaction: {result['tx_hash']}"
        
        logger.error(f"Transaction failed: {result.get('message', 'Unknown error')}")
        return f"Error creating notice: {result.get('message', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Exception in create_notice: {str(e)}")
        return f"Error creating notice: {str(e)}"

def manage_leave(
    employee_address: str,
    public_hash: str,
    start_date: str,
    end_date: str,
    leave_type: str,
    reason: str,
    action: str = "request"
) -> str:
    """Manage employee leaves using the LeaveManagement contract.
    
    Args:
        employee_address: Monad address of the employee (should start with '0x' and be 42 characters long)
        public_hash: Public hash for verification
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        leave_type: Type of leave (Annual, Sick, Personal, Maternity/Paternity, Unpaid)
        reason: Reason for leave
        action: Action to perform (request, update, view)
    
    Returns:
        str: Result of the leave management operation
    """
    try:
        logger.info(f"\nManaging leave:")
        logger.info(f"Employee: {employee_address}")
        logger.info(f"Action: {action}")
        
        # Validate Monad address format
        if not employee_address.startswith('0x') or len(employee_address) != 42:
            logger.error(f"❌ Invalid Monad address format: {employee_address}")
            return f"Error: Invalid Monad address format. Address should start with '0x' and be 42 characters long"
        
        # Initialize leave management
        manager = LeaveManagement()
        
        if action == "request":
            result = manager.request_leave(start_date, end_date, leave_type, reason)
            if result['status'] == 'success':
                logger.info(f"✅ Leave request submitted successfully!")
                logger.info(f"Leave ID: {result['leave_id']}")
                logger.info(f"Transaction: {result['tx_hash']}")
                return f"Leave request submitted successfully! Leave ID: {result['leave_id']}, Transaction: {result['tx_hash']}"
            logger.error(f"❌ Leave request failed: {result['message']}")
            return f"Error requesting leave: {result['message']}"
            
        elif action == "view":
            leaves = manager.get_my_leaves()
            if not leaves:
                return "No leave requests found."
            
            response = "Leave Requests:\n"
            for leave in leaves:
                response += f"\nID: {leave['id']}\n"
                response += f"Start Date: {leave['start_date']}\n"
                response += f"End Date: {leave['end_date']}\n"
                response += f"Type: {leave['leave_type']}\n"
                response += f"Status: {leave['status']}\n"
                response += f"Reason: {leave['reason']}\n"
                response += "-" * 40 + "\n"
            
            return response
            
        else:
            return f"Error: Invalid action '{action}'. Supported actions are 'request' and 'view'"
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return f"Error in manage_leave: {str(e)}"

def process_employee_payment(
    employee_name: str,
    employee_address: str,
    description: str,
    amount: int,
    process_payment: bool = False
) -> str:
    """Process employee payment using the payment handler.
    
    Args:
        employee_name: Name of the employee
        employee_address: Monad blockchain address of the employee
        description: Description of the payment
        amount: Amount in wei
        process_payment: Whether to process the payment immediately
    
    Returns:
        str: Result of the payment operation
    """
    try:
        logger.info(f"\nProcessing employee payment:")
        logger.info(f"Employee: {employee_name}")
        logger.info(f"Address: {employee_address}")
        logger.info(f"Description: {description}")
        logger.info(f"Amount: {amount} wei")
        logger.info(f"Process Payment: {process_payment}")
        
        # Validate Monad address format
        if not employee_address.startswith('0x') or len(employee_address) != 42:
            logger.error(f"❌ Invalid Monad address format: {employee_address}")
            return f"Error: Invalid Monad address format. Address should start with '0x' and be 42 characters long"
        
        # Convert amount to integer if it's a string
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            logger.error(f"❌ Invalid amount format: {amount}")
            return f"Error: Amount must be a valid number"
        
        # Process the payment
        result = payment_handler(
            employee_name=employee_name,
            employee_address=employee_address,
            description=description,
            amount=amount,
            process_payment=process_payment
        )
        
        if result['status'] == 'success':
            response = (
                f"✅ Payment Process Complete!\n\n"
                f"Payment Details:\n"
                f"---------------\n"
                f"Payment ID: {result['payment_id']}\n"
                f"Create Transaction: {result['create_tx_hash']}\n"
                f"Block Number: {result['create_block']}\n"
            )
            
            if process_payment:
                response += (
                    f"\nProcessing Details:\n"
                    f"------------------\n"
                    f"Process Transaction: {result['process_tx_hash']}\n"
                    f"Process Block: {result['process_block']}\n"
                )
            
            logger.info(response)
            return response
        
        logger.error(f"❌ Payment processing failed: {result['message']}")
        return f"Error processing payment: {result['message']}"
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return f"Error in process_employee_payment: {str(e)}"

def main():
    # Create agent
    agent = Agent()
    
    # Register functions
    functions = [
        create_task,
        generate_and_verify_certificate,
        create_notice,
        manage_leave,
        process_employee_payment
    ]
    
    for func in functions:
        agent.register_function(func)
    
    # Example queries
    queries = [
        "Generate a certificate for Sarah Johnson",
    ]
    
    # Process queries
    for query in queries:
        try:
            result = agent.process_query(query)
            # Create a structured response with tool name and result
            response = {
                "tool_called": result.get('tool_name', 'unknown'),
                "result": result['result']
            }
            print(response)  # Print the structured response
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}")

if __name__ == "__main__":
    main()
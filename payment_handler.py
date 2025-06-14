#!/usr/bin/env python3
"""
Employee Payment Handler - Simplified Version
A single function to handle employee payments on Monad blockchain.
"""

import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configuration
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
MONAD_RPC_URL = os.getenv('MONAD_RPC_URL', 'https://testnet-rpc.monad.xyz')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

# Contract ABI (simplified for the EmployeePayment contract)
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"inputs":[
        {"internalType":"string","name":"_employeeName","type":"string"},
        {"internalType":"address","name":"_employeeAddress","type":"address"},
        {"internalType":"string","name":"_description","type":"string"},
        {"internalType":"uint256","name":"_amount","type":"uint256"}
    ],"name":"createPayment","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_paymentId","type":"uint256"}],
    "name":"processPayment","outputs":[],"stateMutability":"payable","type":"function"},
    {"anonymous":False,"inputs":[
        {"indexed":False,"internalType":"uint256","name":"paymentId","type":"uint256"},
        {"indexed":False,"internalType":"string","name":"employeeName","type":"string"},
        {"indexed":False,"internalType":"address","name":"employeeAddress","type":"address"},
        {"indexed":False,"internalType":"string","name":"description","type":"string"},
        {"indexed":False,"internalType":"uint256","name":"amount","type":"uint256"}
    ],"name":"PaymentCreated","type":"event"}
]

def handle_employee_payment(
    employee_name: str,
    employee_address: str,
    description: str,
    amount: int,
    process_payment: bool = False
) -> Dict[str, Any]:
    """
    Handle employee payment creation and processing.
    
    Args:
        employee_name (str): Name of the employee
        employee_address (str): Monad blockchain address of the employee
        description (str): Description of the payment
        amount (int): Amount in wei
        process_payment (bool): Whether to process the payment immediately
    
    Returns:
        Dict[str, Any]: Result of the operation with status and details
    """
    try:
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))
        if not w3.is_connected():
            return {"status": "error", "message": "Failed to connect to Monad RPC node"}
        
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Validate inputs
        if not all([employee_name, employee_address, description, amount]):
            return {"status": "error", "message": "All fields are required"}
        
        if not Web3.is_address(employee_address):
            return {"status": "error", "message": "Invalid employee address"}
        
        if amount <= 0:
            return {"status": "error", "message": "Amount must be greater than 0"}
        
        # Initialize account and contract
        account = Account.from_key(PRIVATE_KEY)
        contract = w3.eth.contract(
            address=CONTRACT_ADDRESS if CONTRACT_ADDRESS else None,
            abi=CONTRACT_ABI
        )
        
        # Create payment
        nonce = w3.eth.get_transaction_count(account.address)
        
        create_tx = contract.functions.createPayment(
            employee_name,
            employee_address,
            description,
            amount
        ).build_transaction({
            'chainId': 10143,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'from': account.address
        })
        
        signed_create_tx = w3.eth.account.sign_transaction(create_tx, private_key=PRIVATE_KEY)
        create_tx_hash = w3.eth.send_raw_transaction(signed_create_tx.rawTransaction)
        create_receipt = w3.eth.wait_for_transaction_receipt(create_tx_hash)
        
        # Get payment ID from event logs
        payment_id = 0
        logs = contract.events.PaymentCreated().process_receipt(create_receipt)
        if logs:
            payment_id = logs[0]['args']['paymentId']
        
        result = {
            'status': 'success',
            'payment_id': payment_id,
            'create_tx_hash': create_tx_hash.hex(),
            'create_block': create_receipt.blockNumber
        }
        
        # Process payment if requested
        if process_payment:
            nonce = w3.eth.get_transaction_count(account.address)
            
            process_tx = contract.functions.processPayment(
                payment_id
            ).build_transaction({
                'chainId': 10143,
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce,
                'from': account.address,
                'value': amount
            })
            
            signed_process_tx = w3.eth.account.sign_transaction(process_tx, private_key=PRIVATE_KEY)
            process_tx_hash = w3.eth.send_raw_transaction(signed_process_tx.rawTransaction)
            process_receipt = w3.eth.wait_for_transaction_receipt(process_tx_hash)
            
            result.update({
                'process_tx_hash': process_tx_hash.hex(),
                'process_block': process_receipt.blockNumber
            })
        
        return result
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Example usage
if __name__ == "__main__":
    # Example parameters
    test_params = {
        'employee_name': 'John Doe',
        'employee_address': '0x1234567890123456789012345678901234567890',  # Replace with actual address
        'description': 'Monthly Salary - March 2024',
        'amount': 1000000000000000000,  # 1 MONAD in wei
        'process_payment': True
    }
    
    result = handle_employee_payment(**test_params)
    print("\nPayment Result:")
    print("-" * 50)
    for key, value in result.items():
        print(f"{key}: {value}") 
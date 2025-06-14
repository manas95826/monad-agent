#!/usr/bin/env python3
"""
Employee Payment System - Monad Blockchain Integration
A system for managing employee payments on Monad blockchain.
"""

import os
import json
from datetime import datetime
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv()

# Configuration
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
MONAD_RPC_URL = os.getenv('MONAD_RPC_URL', 'https://testnet-rpc.monad.xyz')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

# Contract ABI (simplified for the EmployeePayment contract)
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"paymentId","type":"uint256"},
        {"indexed":False,"name":"employeeName","type":"string"},
        {"indexed":True,"name":"employeeAddress","type":"address"},
        {"indexed":False,"name":"description","type":"string"},
        {"indexed":False,"name":"amount","type":"uint256"},
        {"indexed":False,"name":"timestamp","type":"uint256"}
    ],"name":"PaymentCreated","type":"event"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"paymentId","type":"uint256"},
        {"indexed":True,"name":"employeeAddress","type":"address"},
        {"indexed":False,"name":"amount","type":"uint256"},
        {"indexed":False,"name":"timestamp","type":"uint256"}
    ],"name":"PaymentProcessed","type":"event"},
    {"inputs":[
        {"internalType":"string","name":"_employeeName","type":"string"},
        {"internalType":"address","name":"_employeeAddress","type":"address"},
        {"internalType":"string","name":"_description","type":"string"},
        {"internalType":"uint256","name":"_amount","type":"uint256"}
    ],"name":"createPayment","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_paymentId","type":"uint256"}],
    "name":"processPayment","outputs":[],"stateMutability":"payable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_paymentId","type":"uint256"}],
    "name":"getPayment","outputs":[
        {"internalType":"uint256","name":"id","type":"uint256"},
        {"internalType":"string","name":"employeeName","type":"string"},
        {"internalType":"address","name":"employeeAddress","type":"address"},
        {"internalType":"string","name":"description","type":"string"},
        {"internalType":"uint256","name":"amount","type":"uint256"},
        {"internalType":"uint256","name":"timestamp","type":"uint256"},
        {"internalType":"bool","name":"isPaid","type":"bool"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getMyPayments","outputs":[{
        "components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"employeeName","type":"string"},
            {"internalType":"address","name":"employeeAddress","type":"address"},
            {"internalType":"string","name":"description","type":"string"},
            {"internalType":"uint256","name":"amount","type":"uint256"},
            {"internalType":"uint256","name":"timestamp","type":"uint256"},
            {"internalType":"bool","name":"isPaid","type":"bool"}
        ],"internalType":"struct EmployeePayment.Payment[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"}
]

class PaymentSystem:
    """A simple interface to the EmployeePayment smart contract."""
    
    def __init__(self):
        if not PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY not found in .env file")
        
        self.w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Monad RPC node")
        
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account: LocalAccount = Account.from_key(PRIVATE_KEY)
        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS if CONTRACT_ADDRESS else None,
            abi=CONTRACT_ABI
        )
    
    def create_payment(self, employee_name: str, employee_address: str, description: str, amount: int) -> Dict[str, Any]:
        """Create a new payment record."""
        try:
            if not Web3.is_address(employee_address):
                return {"status": "error", "message": "Invalid employee address"}
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.createPayment(
                employee_name,
                employee_address,
                description,
                amount
            ).build_transaction({
                'chainId': 10143,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'from': self.account.address
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            payment_id = 0
            logs = self.contract.events.PaymentCreated().process_receipt(tx_receipt)
            if logs:
                payment_id = logs[0]['args']['paymentId']
            
            return {
                'status': 'success',
                'payment_id': payment_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def process_payment(self, payment_id: int, amount: int) -> Dict[str, Any]:
        """Process a payment."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.processPayment(
                int(payment_id)
            ).build_transaction({
                'chainId': 10143,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'from': self.account.address,
                'value': amount
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'status': 'success',
                'payment_id': payment_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_my_payments(self) -> List[Dict[str, Any]]:
        """Get all payments for the current user."""
        try:
            payments = self.contract.functions.getMyPayments().call({
                'from': self.account.address
            })
            
            result = []
            for payment in payments:
                result.append({
                    'id': payment[0],
                    'employee_name': payment[1],
                    'employee_address': payment[2],
                    'description': payment[3],
                    'amount': payment[4],
                    'timestamp': datetime.fromtimestamp(payment[5]).strftime('%Y-%m-%d %H:%M:%S'),
                    'is_paid': payment[6]
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting payments: {str(e)}")
            return []

def display_payments(payments: List[Dict[str, Any]]) -> None:
    """Display payments in a simple table."""
    if not payments:
        print("\nNo payments found.")
        return
    
    print("\nYour Payments:")
    print("-" * 120)
    print(f"{'ID':<5} | {'Employee Name':<20} | {'Description':<30} | {'Amount':<10} | {'Date':<19} | {'Status'}")
    print("-" * 120)
    
    for payment in payments:
        status = "Paid" if payment['is_paid'] else "Pending"
        print(f"{payment['id']:<5} | {payment['employee_name'][:18]:<20} | {payment['description'][:28]:<30} | "
              f"{payment['amount']:<10} | {payment['timestamp']:<19} | {status}")
    
    print("-" * 120)

def main():
    """Main CLI interface."""
    if not PRIVATE_KEY or not MONAD_RPC_URL:
        print("Error: Please set PRIVATE_KEY and MONAD_RPC_URL in .env file")
        return
    
    if not CONTRACT_ADDRESS:
        print("Warning: PAYMENT_CONTRACT_ADDRESS not set. Some features may not work.")
    
    try:
        payment_system = PaymentSystem()
        print(f"\nConnected to Monad testnet. Account: {payment_system.account.address}")
        print(f"Contract address: {CONTRACT_ADDRESS or 'Not set'}")
        
        while True:
            print("\nOptions:")
            print("1. Create a new payment")
            print("2. Process a payment")
            print("3. View my payments")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                try:
                    employee_name = input("Enter employee name: ").strip()
                    employee_address = input("Enter employee address: ").strip()
                    description = input("Enter payment description: ").strip()
                    amount = input("Enter payment amount (in wei): ").strip()
                    
                    if not all([employee_name, employee_address, description, amount]):
                        print("\n❌ Error: All fields are required")
                        continue
                    
                    if not amount.isdigit():
                        print("\n❌ Error: Amount must be a number")
                        continue
                        
                    result = payment_system.create_payment(
                        employee_name,
                        employee_address,
                        description,
                        int(amount)
                    )
                    
                    if result['status'] == 'success':
                        print(f"\n✅ Payment created successfully!")
                        print(f"Payment ID: {result['payment_id']}")
                        print(f"Transaction: {result['tx_hash']}")
                    else:
                        print(f"\n❌ Error: {result['message']}")
                        
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '2':
                try:
                    payments = payment_system.get_my_payments()
                    if not payments:
                        print("\nNo payments found.")
                        continue
                        
                    display_payments(payments)
                    
                    payment_id = input("\nEnter payment ID to process: ").strip()
                    amount = input("Enter payment amount (in wei): ").strip()
                    
                    if not payment_id.isdigit() or not amount.isdigit():
                        print("\n❌ Invalid payment ID or amount")
                        continue
                        
                    result = payment_system.process_payment(int(payment_id), int(amount))
                    
                    if result['status'] == 'success':
                        print(f"\n✅ Payment processed successfully!")
                        print(f"Transaction: {result['tx_hash']}")
                    else:
                        print(f"\n❌ Error: {result['message']}")
                        
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '3':
                try:
                    print("\nFetching your payments...")
                    payments = payment_system.get_my_payments()
                    display_payments(payments)
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("\n❌ Invalid choice. Please enter a number between 1 and 4.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
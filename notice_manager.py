#!/usr/bin/env python3
"""
Notice Manager - Monad Blockchain Integration
A system for managing and distributing notices, guidelines, and announcements through Monad blockchain.
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

# Contract ABI for Notice Manager
NOTICE_CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"noticeId","type":"uint256"},
        {"indexed":True,"name":"sender","type":"address"},
        {"indexed":False,"name":"category","type":"string"},
        {"indexed":False,"name":"description","type":"string"},
        {"indexed":False,"name":"priority","type":"uint8"},
        {"indexed":False,"name":"content","type":"string"},
        {"indexed":False,"name":"timestamp","type":"uint256"}
    ],"name":"NoticeCreated","type":"event"},
    {"inputs":[
        {"internalType":"string","name":"_category","type":"string"},
        {"internalType":"string","name":"_description","type":"string"},
        {"internalType":"uint8","name":"_priority","type":"uint8"},
        {"internalType":"string","name":"_content","type":"string"}
    ],"name":"createNotice","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_noticeId","type":"uint256"}],
    "name":"getNotice","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"category","type":"string"},
            {"internalType":"string","name":"description","type":"string"},
            {"internalType":"uint8","name":"priority","type":"uint8"},
            {"internalType":"string","name":"content","type":"string"},
            {"internalType":"address","name":"sender","type":"address"},
            {"internalType":"uint256","name":"timestamp","type":"uint256"}
        ],"internalType":"struct NoticeManager.Notice","name":"","type":"tuple"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"string","name":"_category","type":"string"}],
    "name":"getNoticesByCategory","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"category","type":"string"},
            {"internalType":"string","name":"description","type":"string"},
            {"internalType":"uint8","name":"priority","type":"uint8"},
            {"internalType":"string","name":"content","type":"string"},
            {"internalType":"address","name":"sender","type":"address"},
            {"internalType":"uint256","name":"timestamp","type":"uint256"}
        ],"internalType":"struct NoticeManager.Notice[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"}
]

class NoticeManager:
    """A system for managing notices and guidelines through Monad blockchain."""
    
    PRIORITY_LEVELS = ["Low", "Medium", "High", "Urgent"]
    VALID_CATEGORIES = [
        "managers",
        "senior_employees",
        "department_heads",
        "all_employees",
        "technical_team",
        "hr_team",
        "finance_team"
    ]
    
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
            abi=NOTICE_CONTRACT_ABI
        )
    
    def create_notice(self, category: str, description: str, priority: int, content: str) -> Dict[str, Any]:
        """
        Create a new notice or guideline.
        
        Args:
            category (str): The category of recipients (e.g., 'managers', 'senior_employees')
            description (str): Brief description of the notice
            priority (int): Priority level (0-3: Low to Urgent)
            content (str): The full content of the notice
            
        Returns:
            Dict containing the transaction status and details
        """
        try:
            if category.lower() not in self.VALID_CATEGORIES:
                return {"status": "error", "message": f"Invalid category. Must be one of: {', '.join(self.VALID_CATEGORIES)}"}
            
            if not 0 <= priority <= 3:
                return {"status": "error", "message": "Priority must be between 0 and 3"}
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.createNotice(
                category.lower(),
                description,
                priority,
                content
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
            
            notice_id = 0
            logs = self.contract.events.NoticeCreated().process_receipt(tx_receipt)
            if logs:
                notice_id = logs[0]['args']['noticeId']
            
            return {
                'status': 'success',
                'notice_id': notice_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_notices_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Retrieve all notices for a specific category.
        
        Args:
            category (str): The category to filter notices by
            
        Returns:
            List of notices with their details
        """
        try:
            if category.lower() not in self.VALID_CATEGORIES:
                return []
            
            notices = self.contract.functions.getNoticesByCategory(category.lower()).call({
                'from': self.account.address
            })
            
            result = []
            for notice in notices:
                notice_id, category, description, priority, content, sender, timestamp = notice
                result.append({
                    'id': notice_id,
                    'category': category,
                    'description': description,
                    'priority': self.PRIORITY_LEVELS[priority] if priority < len(self.PRIORITY_LEVELS) else 'Unknown',
                    'content': content,
                    'sender': sender,
                    'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting notices: {str(e)}")
            return []

def display_notices(notices: List[Dict[str, Any]]) -> None:
    """Display notices in a formatted table."""
    if not notices:
        print("\nNo notices found.")
        return
    
    print("\nNotices:")
    print("-" * 120)
    print(f"{'ID':<5} | {'Category':<15} | {'Description':<25} | {'Priority':<10} | {'Sender':<40} | {'Timestamp'}")
    print("-" * 120)
    
    for notice in notices:
        print(f"{notice['id']:<5} | {notice['category']:<15} | {notice['description'][:23]:<25} | "
              f"{notice['priority']:<10} | {notice['sender'][:6]}...{notice['sender'][-4:]:<40} | {notice['timestamp']}")
    
    print("-" * 120)

def main():
    """Main CLI interface for the Notice Manager."""
    if not PRIVATE_KEY or not MONAD_RPC_URL:
        print("Error: Please set PRIVATE_KEY and MONAD_RPC_URL in .env file")
        return
    
    if not CONTRACT_ADDRESS:
        print("Warning: NOTICE_CONTRACT_ADDRESS not set. Some features may not work.")
    
    try:
        manager = NoticeManager()
        print(f"\nConnected to Monad testnet. Account: {manager.account.address}")
        print(f"Contract address: {CONTRACT_ADDRESS or 'Not set'}")
        
        while True:
            print("\nOptions:")
            print("1. Create a new notice")
            print("2. View notices by category")
            print("3. Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                try:
                    print("\nValid categories:", ", ".join(manager.VALID_CATEGORIES))
                    category = input("Enter category: ").strip()
                    description = input("Enter notice description: ").strip()
                    print("\nPriority levels:")
                    for i, level in enumerate(manager.PRIORITY_LEVELS):
                        print(f"{i}. {level}")
                    priority = input("Enter priority (0-3): ").strip()
                    content = input("Enter notice content: ").strip()
                    
                    if not all([category, description, priority, content]):
                        print("\n❌ Error: All fields are required")
                        continue
                    
                    if not priority.isdigit() or int(priority) not in range(4):
                        print("\n❌ Error: Invalid priority level")
                        continue
                    
                    result = manager.create_notice(category, description, int(priority), content)
                    
                    if result['status'] == 'success':
                        print(f"\n✅ Notice created successfully!")
                        print(f"Notice ID: {result['notice_id']}")
                        print(f"Transaction: {result['tx_hash']}")
                    else:
                        print(f"\n❌ Error: {result['message']}")
                        
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '2':
                try:
                    print("\nValid categories:", ", ".join(manager.VALID_CATEGORIES))
                    category = input("\nEnter category to view notices: ").strip()
                    
                    if not category:
                        print("\n❌ Error: Category is required")
                        continue
                    
                    print("\nFetching notices...")
                    notices = manager.get_notices_by_category(category)
                    display_notices(notices)
                    
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '3':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("\n❌ Invalid choice. Please enter a number between 1 and 3.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Monad Task Tracker - Simplified Version
A minimal implementation of a task tracking dApp on Monad testnet.
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

# Contract ABI (simplified for the TaskTracker contract)
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"taskId","type":"uint256"},
        {"indexed":True,"name":"assigner","type":"address"},
        {"indexed":True,"name":"assignee","type":"address"},
        {"indexed":False,"name":"description","type":"string"},
        {"indexed":False,"name":"deadline","type":"uint256"}
    ],"name":"TaskCreated","type":"event"},
    {"inputs":[
        {"internalType":"string","name":"_description","type":"string"},
        {"internalType":"uint256","name":"_deadline","type":"uint256"},
        {"internalType":"address","name":"_assignee","type":"address"}
    ],"name":"createTask","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_taskId","type":"uint256"}],
    "name":"getTask","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"description","type":"string"},
            {"internalType":"uint256","name":"deadline","type":"uint256"},
            {"internalType":"address","name":"assigner","type":"address"},
            {"internalType":"address","name":"assignee","type":"address"},
            {"internalType":"uint8","name":"status","type":"uint8"}
        ],"internalType":"struct TaskTracker.Task","name":"","type":"tuple"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getMyTasks","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"description","type":"string"},
            {"internalType":"uint256","name":"deadline","type":"uint256"},
            {"internalType":"address","name":"assigner","type":"address"},
            {"internalType":"address","name":"assignee","type":"address"},
            {"internalType":"uint8","name":"status","type":"uint8"}
        ],"internalType":"struct TaskTracker.Task[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[
        {"internalType":"uint256","name":"_taskId","type":"uint256"},
        {"internalType":"uint8","name":"_newStatus","type":"uint8"}
    ],"name":"updateTaskStatus","outputs":[],"stateMutability":"nonpayable","type":"function"}
]

class TaskTracker:
    """A simple interface to the TaskTracker smart contract."""
    
    TASK_STATUS = ["Pending", "In Progress", "Completed", "Cancelled"]
    
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
    
    def create_task(self, description: str, deadline: str, assignee: str) -> Dict[str, Any]:
        """Create a new task."""
        try:
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            deadline_ts = int(deadline_dt.timestamp())
            
            if not Web3.is_address(assignee):
                return {"status": "error", "message": "Invalid assignee address"}
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.createTask(
                description,
                deadline_ts,
                assignee
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
            
            task_id = 0
            logs = self.contract.events.TaskCreated().process_receipt(tx_receipt)
            if logs:
                task_id = logs[0]['args']['taskId']
            
            return {
                'status': 'success',
                'task_id': task_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def update_task_status(self, task_id: int, status: int) -> Dict[str, Any]:
        """Update task status."""
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.updateTaskStatus(
                int(task_id),
                int(status)
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
            
            return {
                'status': 'success',
                'task_id': task_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_my_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks for the current user."""
        try:
            tasks = self.contract.functions.getMyTasks().call({
                'from': self.account.address
            })
            
            result = []
            for task in tasks:
                task_id, description, deadline_ts, assigner, assignee, status = task
                result.append({
                    'id': task_id,
                    'description': description,
                    'deadline': datetime.fromtimestamp(deadline_ts).strftime('%Y-%m-%d %H:%M:%S'),
                    'assigner': assigner,
                    'assignee': assignee,
                    'status': self.TASK_STATUS[status] if status < len(self.TASK_STATUS) else 'Unknown',
                    'status_code': status
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting tasks: {str(e)}")
            return []

def display_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Display tasks in a simple table."""
    if not tasks:
        print("\nNo tasks found.")
        return
    
    print("\nYour Tasks:")
    print("-" * 100)
    print(f"{'ID':<5} | {'Description':<30} | {'Deadline':<19} | {'Status':<12} | {'Assigner':<40} | {'Assignee'}")
    print("-" * 100)
    
    for task in tasks:
        print(f"{task['id']:<5} | {task['description'][:28]:<30} | {task['deadline']:<19} | {task['status']:<12} | "
              f"{task['assigner'][:6]}...{task['assigner'][-4:]:<40} | {task['assignee'][:6]}...{task['assignee'][-4:]}")
    
    print("-" * 100)

def main():
    """Main CLI interface."""
    if not PRIVATE_KEY or not MONAD_RPC_URL:
        print("Error: Please set PRIVATE_KEY and MONAD_RPC_URL in .env file")
        return
    
    if not CONTRACT_ADDRESS:
        print("Warning: CONTRACT_ADDRESS not set. Some features may not work.")
    
    try:
        tracker = TaskTracker()
        print(f"\nConnected to Monad testnet. Account: {tracker.account.address}")
        print(f"Contract address: {CONTRACT_ADDRESS or 'Not set'}")
        
        while True:
            print("\nOptions:")
            print("1. Create a new task")
            print("2. Update task status")
            print("3. View my tasks")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                try:
                    description = input("Enter task description: ").strip()
                    deadline = input("Enter deadline (YYYY-MM-DD HH:MM:SS): ").strip()
                    assignee = input("Enter assignee address: ").strip()
                    
                    if not all([description, deadline, assignee]):
                        print("\n❌ Error: All fields are required")
                        continue
                        
                    result = tracker.create_task(description, deadline, assignee)
                    
                    if result['status'] == 'success':
                        print(f"\n✅ Task created successfully!")
                        print(f"Task ID: {result['task_id']}")
                        print(f"Transaction: {result['tx_hash']}")
                    else:
                        print(f"\n❌ Error: {result['message']}")
                        
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '2':
                try:
                    tasks = tracker.get_my_tasks()
                    if not tasks:
                        print("\nNo tasks found.")
                        continue
                        
                    display_tasks(tasks)
                    
                    task_id = input("\nEnter task ID to update: ").strip()
                    print("\nStatus Codes:")
                    for i, status in enumerate(tracker.TASK_STATUS):
                        print(f"{i}. {status}")
                        
                    status = input("\nEnter new status code (0-3): ").strip()
                    
                    if not task_id.isdigit() or not status.isdigit() or int(status) not in range(4):
                        print("\n❌ Invalid task ID or status code")
                        continue
                        
                    result = tracker.update_task_status(int(task_id), int(status))
                    
                    if result['status'] == 'success':
                        print(f"\n✅ Task status updated successfully!")
                        print(f"Transaction: {result['tx_hash']}")
                    else:
                        print(f"\n❌ Error: {result['message']}")
                        
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
            
            elif choice == '3':
                try:
                    print("\nFetching your tasks...")
                    tasks = tracker.get_my_tasks()
                    display_tasks(tasks)
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

#!/usr/bin/env python3
"""
Leave & Attendance Management System
A dApp for managing employee leaves, attendance, and holiday calendars on Monad testnet.
"""

import os
import json
from datetime import datetime, timedelta
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

# Contract ABI for Leave Management
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"leaveId","type":"uint256"},
        {"indexed":True,"name":"employee","type":"address"},
        {"indexed":False,"name":"startDate","type":"uint256"},
        {"indexed":False,"name":"endDate","type":"uint256"},
        {"indexed":False,"name":"leaveType","type":"string"},
        {"indexed":False,"name":"reason","type":"string"}
    ],"name":"LeaveRequested","type":"event"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"leaveId","type":"uint256"},
        {"indexed":True,"name":"approver","type":"address"},
        {"indexed":False,"name":"status","type":"uint8"}
    ],"name":"LeaveStatusUpdated","type":"event"},
    {"inputs":[
        {"internalType":"uint256","name":"_startDate","type":"uint256"},
        {"internalType":"uint256","name":"_endDate","type":"uint256"},
        {"internalType":"string","name":"_leaveType","type":"string"},
        {"internalType":"string","name":"_reason","type":"string"}
    ],"name":"requestLeave","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[
        {"internalType":"uint256","name":"_leaveId","type":"uint256"},
        {"internalType":"uint8","name":"_status","type":"uint8"}
    ],"name":"updateLeaveStatus","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"getMyLeaves","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"uint256","name":"startDate","type":"uint256"},
            {"internalType":"uint256","name":"endDate","type":"uint256"},
            {"internalType":"string","name":"leaveType","type":"string"},
            {"internalType":"string","name":"reason","type":"string"},
            {"internalType":"address","name":"employee","type":"address"},
            {"internalType":"uint8","name":"status","type":"uint8"}
        ],"internalType":"struct LeaveManagement.Leave[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPendingLeaves","outputs":[
        {"components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"uint256","name":"startDate","type":"uint256"},
            {"internalType":"uint256","name":"endDate","type":"uint256"},
            {"internalType":"string","name":"leaveType","type":"string"},
            {"internalType":"string","name":"reason","type":"string"},
            {"internalType":"address","name":"employee","type":"address"},
            {"internalType":"uint8","name":"status","type":"uint8"}
        ],"internalType":"struct LeaveManagement.Leave[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[
        {"internalType":"uint256","name":"_date","type":"uint256"},
        {"internalType":"string","name":"_description","type":"string"}
    ],"name":"addHoliday","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"getHolidays","outputs":[
        {"components":[
            {"internalType":"uint256","name":"date","type":"uint256"},
            {"internalType":"string","name":"description","type":"string"}
        ],"internalType":"struct LeaveManagement.Holiday[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"},
    {"inputs":[
        {"internalType":"uint256","name":"_date","type":"uint256"}
    ],"name":"markAttendance","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[
        {"internalType":"uint256","name":"_startDate","type":"uint256"},
        {"internalType":"uint256","name":"_endDate","type":"uint256"}
    ],"name":"getAttendance","outputs":[
        {"components":[
            {"internalType":"uint256","name":"date","type":"uint256"},
            {"internalType":"bool","name":"present","type":"bool"}
        ],"internalType":"struct LeaveManagement.Attendance[]","name":"","type":"tuple[]"}
    ],"stateMutability":"view","type":"function"}
]

class LeaveManagement:
    """Interface for Leave & Attendance Management smart contract."""
    
    LEAVE_STATUS = ["Pending", "Approved", "Rejected"]
    LEAVE_TYPES = ["Annual", "Sick", "Personal", "Maternity/Paternity", "Unpaid"]
    
    def __init__(self):
        if not PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY not found in .env file")
        
        if not CONTRACT_ADDRESS:
            raise ValueError("LEAVE_CONTRACT_ADDRESS not found in .env file")
        
        self.w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Monad RPC node")
        
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account: LocalAccount = Account.from_key(PRIVATE_KEY)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )
    
    def request_leave(self, start_date: str, end_date: str, leave_type: str, reason: str) -> Dict[str, Any]:
        """Request a new leave."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start_dt > end_dt:
                return {"status": "error", "message": "Start date cannot be after end date"}
            
            if leave_type not in self.LEAVE_TYPES:
                return {"status": "error", "message": "Invalid leave type"}
            
            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.requestLeave(
                start_ts,
                end_ts,
                leave_type,
                reason
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
            
            leave_id = 0
            logs = self.contract.events.LeaveRequested().process_receipt(tx_receipt)
            if logs:
                leave_id = logs[0]['args']['leaveId']
            
            return {
                'status': 'success',
                'leave_id': leave_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def update_leave_status(self, leave_id: int, status: int) -> Dict[str, Any]:
        """Update leave request status."""
        try:
            if status not in range(len(self.LEAVE_STATUS)):
                return {"status": "error", "message": "Invalid status code"}
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.updateLeaveStatus(
                int(leave_id),
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
                'leave_id': leave_id,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_my_leaves(self) -> List[Dict[str, Any]]:
        """Get all leave requests for the current user."""
        try:
            leaves = self.contract.functions.getMyLeaves().call({
                'from': self.account.address
            })
            
            result = []
            for leave in leaves:
                leave_id, start_date, end_date, leave_type, reason, employee, status = leave
                result.append({
                    'id': leave_id,
                    'start_date': datetime.fromtimestamp(start_date).strftime('%Y-%m-%d'),
                    'end_date': datetime.fromtimestamp(end_date).strftime('%Y-%m-%d'),
                    'leave_type': leave_type,
                    'reason': reason,
                    'employee': employee,
                    'status': self.LEAVE_STATUS[status] if status < len(self.LEAVE_STATUS) else 'Unknown',
                    'status_code': status
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting leaves: {str(e)}")
            return []
    
    def mark_attendance(self, date: str) -> Dict[str, Any]:
        """Mark attendance for a specific date."""
        try:
            date_dt = datetime.strptime(date, "%Y-%m-%d")
            date_ts = int(date_dt.timestamp())
            
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.markAttendance(
                date_ts
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
                'date': date,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_attendance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get attendance records for a date range."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())
            
            attendance = self.contract.functions.getAttendance(
                start_ts,
                end_ts
            ).call({
                'from': self.account.address
            })
            
            result = []
            for record in attendance:
                date, present = record
                result.append({
                    'date': datetime.fromtimestamp(date).strftime('%Y-%m-%d'),
                    'present': present
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting attendance: {str(e)}")
            return []

def display_leaves(leaves: List[Dict[str, Any]]) -> None:
    """Display leave requests in a table format."""
    if not leaves:
        print("\nNo leave requests found.")
        return
    
    print("\nLeave Requests:")
    print("-" * 120)
    print(f"{'ID':<5} | {'Start Date':<12} | {'End Date':<12} | {'Type':<15} | {'Status':<10} | {'Reason'}")
    print("-" * 120)
    
    for leave in leaves:
        print(f"{leave['id']:<5} | {leave['start_date']:<12} | {leave['end_date']:<12} | "
              f"{leave['leave_type']:<15} | {leave['status']:<10} | {leave['reason']}")
    
    print("-" * 120)

def display_attendance(attendance: List[Dict[str, Any]]) -> None:
    """Display attendance records in a table format."""
    if not attendance:
        print("\nNo attendance records found.")
        return
    
    print("\nAttendance Records:")
    print("-" * 50)
    print(f"{'Date':<12} | {'Status'}")
    print("-" * 50)
    
    for record in attendance:
        status = "Present" if record['present'] else "Absent"
        print(f"{record['date']:<12} | {status}")
    
    print("-" * 50)

def main():
    """Main function definition for leave management system."""
    pass

if __name__ == "__main__":
    main() 
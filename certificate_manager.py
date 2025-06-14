#!/usr/bin/env python3
"""
Certificate Manager - Monad Integration
A system for generating and authenticating certificates on Monad blockchain.
"""

import os
import json
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Tuple

# Load environment variables
load_dotenv()

# Configuration
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
MONAD_RPC_URL = os.getenv('MONAD_RPC_URL', 'https://testnet-rpc.monad.xyz')
CONTRACT_ADDRESS = os.getenv('CERTIFICATE_CONTRACT_ADDRESS')

# Contract ABI for CertificateAuthenticator
CONTRACT_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":False,"inputs":[
        {"indexed":True,"name":"certificateId","type":"uint256"},
        {"indexed":True,"name":"issuer","type":"address"},
        {"indexed":False,"name":"name","type":"string"},
        {"indexed":False,"name":"certificateHash","type":"string"},
        {"indexed":False,"name":"timestamp","type":"uint256"}
    ],"name":"CertificateIssued","type":"event"},
    {"anonymous":False,"inputs":[{"indexed":True,"name":"certificateId","type":"uint256"}],
    "name":"CertificateRevoked","type":"event"},
    {"inputs":[
        {"internalType":"string","name":"_name","type":"string"},
        {"internalType":"string","name":"_certificateHash","type":"string"}
    ],"name":"issueCertificate","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_certificateId","type":"uint256"}],
    "name":"revokeCertificate","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"internalType":"string","name":"_certificateHash","type":"string"}],
    "name":"verifyCertificate","outputs":[{"internalType":"bool","name":"","type":"bool"}],
    "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"_certificateId","type":"uint256"}],
    "name":"getCertificate","outputs":[{
        "components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"name","type":"string"},
            {"internalType":"string","name":"certificateHash","type":"string"},
            {"internalType":"uint256","name":"timestamp","type":"uint256"},
            {"internalType":"address","name":"issuer","type":"address"},
            {"internalType":"bool","name":"isValid","type":"bool"}
        ],
        "internalType":"struct CertificateAuthenticator.Certificate",
        "name":"","type":"tuple"
    }],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getMyCertificates","outputs":[{
        "components":[
            {"internalType":"uint256","name":"id","type":"uint256"},
            {"internalType":"string","name":"name","type":"string"},
            {"internalType":"string","name":"certificateHash","type":"string"},
            {"internalType":"uint256","name":"timestamp","type":"uint256"},
            {"internalType":"address","name":"issuer","type":"address"},
            {"internalType":"bool","name":"isValid","type":"bool"}
        ],
        "internalType":"struct CertificateAuthenticator.Certificate[]",
        "name":"","type":"tuple[]"
    }],"stateMutability":"view","type":"function"}
]

class CertificateManager:
    """A system for generating and authenticating certificates on Monad blockchain."""
    
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
    
    def generate_certificate(
        self,
        template_path: str,
        name: str,
        output_path: str,
        font_path: str,
        font_size: int = 180,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        y: int = 570
    ) -> Dict[str, Any]:
        """Generate a certificate and authenticate it on the blockchain."""
        try:
            # Generate the certificate image
            img = Image.open(template_path)
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"Font load error: {e}. Using default font.")
                font = ImageFont.load_default()
            
            text_width = draw.textlength(name, font=font)
            x = (img.width - text_width) // 2
            draw.text((x, y), name, font=font, fill=text_color)
            
            # Save the certificate
            img.save(output_path)
            
            # Calculate hash of the certificate
            with open(output_path, 'rb') as f:
                certificate_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Authenticate on blockchain
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.issueCertificate(
                name,
                certificate_hash
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
            
            # Get certificate ID from event
            certificate_id = 0
            logs = self.contract.events.CertificateIssued().process_receipt(tx_receipt)
            if logs:
                certificate_id = logs[0]['args']['certificateId']
            
            return {
                'status': 'success',
                'certificate_id': certificate_id,
                'certificate_hash': certificate_hash,
                'tx_hash': tx_hash.hex(),
                'block_number': tx_receipt.blockNumber,
                'output_path': output_path
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def verify_certificate(self, certificate_path: str) -> Dict[str, Any]:
        """Verify a certificate's authenticity on the blockchain."""
        try:
            with open(certificate_path, 'rb') as f:
                certificate_hash = hashlib.sha256(f.read()).hexdigest()
            
            is_valid = self.contract.functions.verifyCertificate(certificate_hash).call()
            
            return {
                'status': 'success',
                'is_valid': is_valid,
                'certificate_hash': certificate_hash
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_my_certificates(self) -> List[Dict[str, Any]]:
        """Get all certificates issued by the current user."""
        try:
            certificates = self.contract.functions.getMyCertificates().call({
                'from': self.account.address
            })
            
            result = []
            for cert in certificates:
                result.append({
                    'id': cert[0],
                    'name': cert[1],
                    'certificate_hash': cert[2],
                    'timestamp': datetime.fromtimestamp(cert[3]).strftime('%Y-%m-%d %H:%M:%S'),
                    'issuer': cert[4],
                    'is_valid': cert[5]
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting certificates: {str(e)}")
            return []

def process_certificate(args):
    """Helper function to process a single certificate for threading"""
    manager, template_path, name, output_path, font_path, font_size, text_color, y = args
    try:
        result = manager.generate_certificate(
            template_path, name, output_path, font_path, font_size, text_color, y
        )
        return f"Generated and authenticated certificate for {name}: {result['certificate_hash']}"
    except Exception as e:
        return f"Error processing certificate for {name}: {str(e)}"

def main():
    # Configuration
    template_path = "template.png"
    csv_path = "data.csv"
    output_dir = "generated_certificates"
    font_path = "Montserrat-Bold.ttf"
    font_size = 100
    y = 1000
    
    # Thread pool configuration
    max_workers = 512
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        manager = CertificateManager()
        print(f"\nConnected to Monad testnet. Account: {manager.account.address}")
        print(f"Contract address: {CONTRACT_ADDRESS or 'Not set'}")
        
        # Read participant data
        df = pd.read_csv(csv_path)
        
        # Prepare arguments for each certificate generation task
        tasks = []
        for index, row in df.iterrows():
            name = row['name']
            output_path = os.path.join(output_dir, f"{name.replace(' ', '_')}_certificate.png")
            tasks.append((
                manager, template_path, name, output_path,
                font_path, font_size, (255, 255, 255), y
            ))
        
        # Process certificates using thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(process_certificate, task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                result = future.result()
                print(result)
        
        # Display all issued certificates
        print("\nIssued Certificates:")
        certificates = manager.get_my_certificates()
        for cert in certificates:
            print(f"\nCertificate ID: {cert['id']}")
            print(f"Name: {cert['name']}")
            print(f"Hash: {cert['certificate_hash']}")
            print(f"Issued: {cert['timestamp']}")
            print(f"Valid: {'Yes' if cert['is_valid'] else 'No'}")
            print("-" * 50)
    
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
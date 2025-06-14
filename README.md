# OrgNet – The All-in-One Company Operations Platform

OrgNet is a comprehensive platform that streamlines and automates all core company operations, including task management, salary payments, leave management, certificate generation, and official notices. Built with a modern web frontend and a robust backend, OrgNet leverages blockchain for transparency and security, and integrates with Supabase for seamless data management.

---

## Features

- **Unified Dashboard:** Manage tasks, payments, leaves, certificates, and notices from a single interface.
- **Task Tracking:** Assign, update, and monitor tasks on-chain for full transparency.
- **Salary Management:** Record INR salaries and process MON token payments on the Monad blockchain.
- **Leave Management:** Submit, approve, and track employee leaves.
- **Certificate Generation:** Create and verify digital certificates for employees.
- **Notice Board:** Issue and manage official company notices.
- **Blockchain-Powered:** All critical actions are recorded on the Monad blockchain for auditability.
- **Supabase Integration:** Employee profiles and transaction history are securely managed.
- **Comprehensive Error Handling:** Robust validation and error reporting across all modules.

---

## Tech Stack

- **Frontend:** Next.js, React, TailwindCSS, Clerk (authentication), Supabase, Ethers.js, Hardhat (for smart contracts)
- **Backend:** FastAPI, Python, Web3.py, Pydantic, Uvicorn, dotenv
- **Blockchain:** Monad Testnet (for smart contracts and payments)
- **Database:** Supabase (PostgreSQL)
- **Smart Contracts:** Solidity (Task, Salary, Certificate, Leave, Notice management)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/manas95826/orgnet.git
cd orgnet
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your private keys and config
uvicorn api:app --reload
```

- **Environment Variables:**  
  - `PRIVATE_KEY` – Your admin wallet private key (with 0x prefix)
  - `MONAD_RPC_URL` – Monad node URL (default: https://testnet-rpc.monad.xyz)
  - `CONTRACT_ADDRESS` – Deployed contract address

### 3. Frontend Setup

```bash
cd ../frontend
npm install
cp env-sample.txt .env.local  # Fill in Supabase and contract details
npm run dev
```

- **Key .env variables:**  
  - `NEXT_PUBLIC_APP_URL` – Frontend URL
  - `SUPABASE_URL` and `SUPABASE_KEY` – Supabase project credentials
  - `SALARY_CONTRACT` – Salary contract address

---

## Usage

- **Access the dashboard:**  
  Open [http://localhost:3000](http://localhost:3000) in your browser.

- **APIs:**  
  The backend exposes a `/process-query` endpoint for all organizational actions (task, leave, payment, certificate, notice).

- **Smart Contract Addresses:**  
  - CertificateRegistry: `0x9D3c6ca...C9Ef2`
  - SalaryPayment: `0xd8A3B...030049EdC6A9742680`
  - TaskTracker: `0x295AC...a07Fb941857`

---

## Security Best Practices

- **Never commit `.env` files or private keys.**
- Use environment variables for all sensitive data.
- Validate all user input and wallet addresses.
- Monitor transaction status and handle errors gracefully.

---
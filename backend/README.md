# Monad Task Tracker (Simplified)

A simple, single-file implementation of a task tracking dApp on Monad testnet.

## Files

- `app.py` - Main application with CLI interface
- `contracts/TaskTracker.sol` - Smart contract source code
- `.env` - Environment configuration
- `requirements.txt` - Python dependencies

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure `.env`:
   ```
   PRIVATE_KEY=your_private_key_with_0x_prefix
   MONAD_RPC_URL=https://testnet-rpc.monad.xyz
   CONTRACT_ADDRESS=0x295AC10bc44e9163eA73ca94A69b3a07Fb941857
   ```

3. Run the app:
   ```bash
   python app.py
   ```

## Usage

1. Create tasks
2. Update task status
3. View your tasks
4. Exit the application

## Contract Details

- **Address**: `0x295AC10bc44e9163eA73ca94A69b3a07Fb941857`
- **Network**: Monad Testnet (Chain ID: 10143)
- **Explorer**: https://testnet.monadexplorer.com/

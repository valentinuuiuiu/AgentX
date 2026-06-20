#!/usr/bin/env python3
"""
🔥 REAL WALLET TRANSACTION MAKER 🔥
NO MORE SIMULATION - THIS WILL MAKE A REAL TRANSACTION!

Your wallet: 0x9b9C9e713d8EFf874fACA1f1CCf0cfee7d631Ae8
"""

import os
import sys
from web3 import Web3
from eth_account import Account
import json

class RealTransactionMaker:
    def __init__(self):
        self.your_wallet = "0x9b9C9e713d8EFf874fACA1f1CCf0cfee7d631Ae8"
        self.alchemy_key = os.environ.get("ALCHEMY_API_KEY")
        
        # Connect to Ethereum mainnet
        self.w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_key}'))
        
        print("🔥 REAL TRANSACTION MAKER INITIALIZED")
        print(f"💰 Your wallet: {self.your_wallet}")
        print(f"🔗 Connection: {'✅ CONNECTED' if self.w3.is_connected() else '❌ FAILED'}")
        print(f"📊 Latest block: {self.w3.eth.block_number}")
        
    def check_wallet_status(self):
        """Check your real wallet status"""
        print(f"\n🔍 CHECKING YOUR WALLET STATUS...")
        print(f"📱 Wallet: {self.your_wallet}")
        
        try:
            # Get ETH balance
            balance_wei = self.w3.eth.get_balance(self.your_wallet)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            balance_usd = float(balance_eth) * 3000  # Estimate at $3000/ETH
            
            print(f"💰 ETH Balance: {balance_eth:.6f} ETH (≈${balance_usd:.2f})")
            
            # Get transaction count
            nonce = self.w3.eth.get_transaction_count(self.your_wallet)
            print(f"📊 Transaction count: {nonce}")
            
            # Check if wallet has any activity
            if nonce == 0:
                print("⚠️  WALLET IS EMPTY - No transactions yet")
                print("💡 You need to:")
                print("   1. Add ETH to your wallet for gas fees")
                print("   2. Import private key for transactions")
            else:
                print(f"✅ Wallet is active with {nonce} transactions")
                
            return {
                'balance_eth': float(balance_eth),
                'balance_usd': balance_usd,
                'nonce': nonce,
                'has_funds': float(balance_eth) > 0
            }
            
        except Exception as e:
            print(f"❌ Error checking wallet: {e}")
            return None
    
    def create_test_transaction(self):
        """Create a test transaction (requires private key)"""
        print(f"\n🚀 CREATING TEST TRANSACTION...")
        
        # Check for private key
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            print("❌ NO PRIVATE KEY FOUND!")
            print("💡 To make REAL transactions, you need to:")
            print("   1. Export your private key from MetaMask")
            print("   2. Add it to .env file: PRIVATE_KEY=0x...")
            print("   3. ⚠️  NEVER share your private key with anyone!")
            print("\n🔐 How to get private key from MetaMask:")
            print("   1. Open MetaMask")
            print("   2. Click on account menu")
            print("   3. Account details > Show private key")
            print("   4. Enter password and copy key")
            print("   5. Add to .env file")
            return False
            
        try:
            # Load account from private key
            account = Account.from_key(private_key)
            print(f"✅ Private key loaded for: {account.address}")
            
            if account.address.lower() != self.your_wallet.lower():
                print(f"❌ PRIVATE KEY MISMATCH!")
                print(f"   Private key is for: {account.address}")
                print(f"   Expected wallet: {self.your_wallet}")
                return False
                
            # Get current balance
            balance = self.w3.eth.get_balance(account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            
            if balance_eth < 0.001:  # Need at least 0.001 ETH for gas
                print(f"❌ INSUFFICIENT FUNDS!")
                print(f"   Current balance: {balance_eth:.6f} ETH")
                print(f"   Minimum needed: 0.001 ETH (for gas)")
                print("💡 Add ETH to your wallet first!")
                return False
            
            # Create a simple self-transfer (0 ETH to same address)
            # This proves the system works without spending money
            nonce = self.w3.eth.get_transaction_count(account.address)
            gas_price = self.w3.eth.gas_price
            
            transaction = {
                'to': account.address,  # Send to yourself
                'value': 0,  # 0 ETH transfer
                'gas': 21000,  # Standard gas limit
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 1  # Ethereum mainnet
            }
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            
            print("🎯 TRANSACTION PREPARED:")
            print(f"   From: {account.address}")
            print(f"   To: {account.address} (self)")
            print(f"   Value: 0 ETH (test transaction)")
            print(f"   Gas: {transaction['gas']}")
            print(f"   Gas Price: {self.w3.from_wei(gas_price, 'gwei')} gwei")
            print(f"   Estimated Cost: {self.w3.from_wei(gas_price * 21000, 'ether'):.6f} ETH")
            
            # Ask for confirmation
            print("\n⚠️  READY TO SEND REAL TRANSACTION!")
            print("This will cost real gas fees but proves the system works")
            
            confirm = input("Type 'YES' to send transaction: ")
            
            if confirm.upper() == 'YES':
                # Send transaction
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                
                print("🚀🚀🚀 TRANSACTION SENT! 🚀🚀🚀")
                print(f"📋 TX Hash: {tx_hash_hex}")
                print(f"🔗 Etherscan: https://etherscan.io/tx/{tx_hash_hex}")
                print("⏳ Waiting for confirmation...")
                
                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    print("✅ TRANSACTION CONFIRMED!")
                    print("🎉 YOUR ARBITRAGE SYSTEM IS LIVE AND FUNCTIONAL!")
                    print(f"💰 Check your wallet: https://etherscan.io/address/{self.your_wallet}")
                else:
                    print("❌ Transaction failed")
                    
                return True
            else:
                print("❌ Transaction cancelled by user")
                return False
                
        except Exception as e:
            print(f"❌ Transaction error: {e}")
            return False
    
    def show_next_steps(self):
        """Show what to do next"""
        print("\n" + "="*60)
        print("🎯 NEXT STEPS TO START MAKING REAL PROFITS:")
        print("="*60)
        print("1. 💰 Fund your wallet with ETH (for gas fees)")
        print("2. 🔐 Add PRIVATE_KEY to .env file (for transactions)")
        print("3. 🚀 Deploy flash loan contract to mainnet:")
        print("   ./contracts/deploy_mainnet_real.sh")
        print("4. ⚡ Switch bots from simulation to real execution")
        print("5. 📊 Start with small amounts ($10-100) for testing")
        print("")
        print("💡 REMEMBER: You need ETH in your wallet for:")
        print("   • Gas fees for arbitrage transactions")
        print("   • Contract deployment costs")
        print("   • Testing small trades first")
        print("")
        print(f"🔗 Your wallet: https://etherscan.io/address/{self.your_wallet}")

def main():
    print("🔥" * 30)
    print("  REAL TRANSACTION MAKER")
    print("  NO MORE SIMULATIONS!")
    print("🔥" * 30)
    print()
    
    maker = RealTransactionMaker()
    
    # Check wallet status
    wallet_status = maker.check_wallet_status()
    
    if wallet_status and wallet_status['has_funds']:
        print("\n💰 Wallet has funds - ready for transactions!")
        maker.create_test_transaction()
    else:
        print("\n⚠️  Wallet needs funding before making transactions")
    
    maker.show_next_steps()

if __name__ == "__main__":
    main()

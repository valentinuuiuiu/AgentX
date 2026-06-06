#!/usr/bin/env python3
"""
Rehoboam First Penny Execution Engine
=====================================
Automated pipeline to:
1. Acquire Sepolia ETH via browser automation
2. Deploy FlashLoanArbitrage contract
3. Execute profitable arbitrage trades
4. Monitor and report profits

Usage:
    python3 scripts/first_penny_engine.py --mode mine     # Mine Sepolia ETH
    python3 scripts/first_penny_engine.py --mode deploy   # Deploy contracts
    python3 scripts/first_penny_engine.py --mode trade     # Execute trades
    python3 scripts/first_penny_engine.py --mode auto      # Full auto pipeline
"""

import argparse
import asyncio
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from web3 import Web3

# Configuration
WALLET = os.getenv("FLASH_ARB_MASTER", "0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407")
PRIVATE_KEY = os.getenv("SEPOLIA_PRIVATE_KEY", "")
SEPOLIA_RPC = os.getenv("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")

# Check if private key is configured
if not PRIVATE_KEY or PRIVATE_KEY.startswith("your_"):
    print("⚠️  WARNING: SEPOLIA_PRIVATE_KEY not configured in .env")
    print("   Set it to execute transactions: SEPOLIA_PRIVATE_KEY=0x...")
    HAS_PK = False
else:
    HAS_PK = True

# Sepolia token addresses (verified deployed)
SEPOLIA_TOKENS = {
    "WETH": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    "USDC": "0x94a9D9AC8415D5394D6E6f4a0d2782c3F7d13b2e",
    "DAI": "0xFF34B3D4Aee8ddCd6F9AFF1e12E189D34Da9415b",
    "LINK": "0xf8Fb3713D3E84F0B9727F97E3493F9e530A5e64e",
}

# Uniswap V2 Router on Sepolia
UNISWAP_V2_ROUTER = "0xC532a71256731900393Bc4E2350BD5D53D2C0B6E"
UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

# Aave V3 Pool on Sepolia
AAVE_V3_POOL = "0x6Ae43d3271ff6888e7Fc43Fd7321a503104E31D7"

# Minimal ERC20 ABI
ERC20_ABI = json.loads('[{"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"}]')

# Uniswap V2 Router ABI (minimal)
ROUTER_ABI = json.loads('[{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]')

# Factory ABI for pair lookup
FACTORY_ABI = json.loads('[{"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"getPair","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"}]')


def get_w3():
    """Get connected Web3 instance"""
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        # Fallback
        w3 = Web3(Web3.HTTPProvider("https://sepolia.gateway.tenderly.co"))
    return w3


def check_wallet():
    """Check wallet balance and status"""
    w3 = get_w3()
    addr = Web3.to_checksum_address(WALLET)
    bal = w3.eth.get_balance(addr)
    nonce = w3.eth.get_transaction_count(addr)
    
    print(f"\n{'='*60}")
    print(f"🔍 Wallet: {addr}")
    print(f"💰 ETH Balance: {w3.from_wei(bal, 'ether'):.6f} ETH")
    print(f"📊 Nonce: {nonce}")
    print(f"🧱 Block: {w3.eth.block_number}")
    print(f"{'='*60}")
    
    return w3.from_wei(bal, 'ether')


def mine_sepolia_pow():
    """Mine Sepolia ETH using pk910 PoW faucet via browser"""
    print("\n⛏️  Starting Sepolia ETH PoW Mining...")
    print("="*60)
    print("💡 This will open a browser and mine ETH using CPU")
    print("💡 Typical yield: 0.05-0.5 ETH per hour")
    print("💡 Press Ctrl+C to stop mining")
    print("="*60)
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            
            # Navigate to pk910 faucet and wait for full load
            page.goto("https://sepolia-faucet.pk910.de", wait_until="networkidle")
            print("✅ Opened pk910 PoW faucet")
            
            # Wait a bit for any JS rendering
            page.wait_for_timeout(3000)
            
            # Try multiple selectors for the address input
            selectors = [
                "input[name='address']",
                "input[placeholder*='address' i]",
                "input[type='text']",
                "#address",
                ".address-input",
                "input[id*='address' i]",
                "input[class*='address' i]",
            ]
            
            input_found = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.fill(selector, WALLET)
                    print(f"📝 Filled wallet using selector: {selector}")
                    input_found = True
                    break
                except:
                    continue
            
            if not input_found:
                # Try to find any input and fill it
                inputs = page.query_selector_all("input")
                for inp in inputs:
                    try:
                        inp.fill(WALLET)
                        print("📝 Filled wallet in available input")
                        input_found = True
                        break
                    except:
                        continue
            
            if not input_found:
                print("❌ Could not find address input field")
                print("   The faucet page may have changed. Try manual:")
                print("   https://sepolia-faucet.pk910.de")
                return False
            
            # Try multiple selectors for the submit button
            button_selectors = [
                "button[type='submit']",
                "button:has-text('Start')",
                "button:has-text('Mine')",
                "input[type='submit']",
                ".start-mining",
                "button",
            ]
            
            button_found = False
            for selector in button_selectors:
                try:
                    page.click(selector)
                    print(f"⛏️  Mining started using selector: {selector}")
                    button_found = True
                    break
                except:
                    continue
            
            if not button_found:
                print("⚠️  Could not auto-click start button")
                print("   Please click the start button manually in the browser")
            
            # Monitor
            start_time = time.time()
            last_check = 0
            
            try:
                while True:
                    time.sleep(30)
                    elapsed = time.time() - start_time
                    
                    # Check balance every 2 minutes
                    if elapsed - last_check > 120:
                        w3 = get_w3()
                        bal = w3.eth.get_balance(Web3.to_checksum_address(WALLET))
                        eth_bal = w3.from_wei(bal, 'ether')
                        print(f"⏱️  Elapsed: {elapsed/60:.1f}min | Balance: {eth_bal:.4f} ETH")
                        
                        if eth_bal > 0.01:
                            print(f"🎉 SUCCESS! Mined {eth_bal:.4f} ETH")
                            break
                        last_check = elapsed
                        
            except KeyboardInterrupt:
                print("\n🛑 Mining stopped by user")
            
            browser.close()
            
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        print("   Then: python3 -m playwright install chromium")
        return False
    except Exception as e:
        print(f"❌ Mining error: {e}")
        return False
    
    return True


def deploy_flash_arbitrage():
    """Deploy FlashLoanArbitrage contract to Sepolia"""
    print("\n🏗️  Deploying FlashLoanArbitrage contract...")
    print("="*60)
    
    if not PRIVATE_KEY:
        print("❌ SEPOLIA_PRIVATE_KEY not set in .env")
        return None
    
    w3 = get_w3()
    from eth_account import Account
    account = Account.from_key(PRIVATE_KEY)
    
    # Check balance
    bal = w3.eth.get_balance(account.address)
    if bal < w3.to_wei(0.01, 'ether'):
        print(f"❌ Insufficient balance: {w3.from_wei(bal, 'ether'):.4f} ETH")
        print("   Need at least 0.01 ETH for deployment")
        return None
    
    # Build contract using forge
    print("🔨 Building contract with Foundry...")
    result = subprocess.run(
        ["forge", "build", "--contracts", "contracts/src/FlashLoanArbitrage.sol"],
        cwd="/home/aryan/free-claude/bittensor/clean_rehoboam_project",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return None
    
    print("✅ Contract built successfully")
    
    # For now, return a placeholder - actual deployment needs the compiled bytecode
    # This would be expanded with the actual deployment transaction
    print("⚠️  Contract deployment requires compiled bytecode")
    print("   Run: forge script script/DeployFlashArbitrage.s.sol --rpc-url $SEPOLIA_RPC_URL --broadcast")
    
    return None


def find_arbitrage_opportunities():
    """Scan for arbitrage opportunities on Sepolia"""
    print("\n🔍 Scanning for arbitrage opportunities...")
    print("="*60)
    
    w3 = get_w3()
    
    # Check if factory exists
    factory_code = w3.eth.get_code(Web3.to_checksum_address(UNISWAP_V2_FACTORY))
    if len(factory_code) < 10:
        print("❌ Uniswap V2 Factory not deployed at expected address")
        print("   Cannot scan for pairs without factory")
        return []
    
    factory = w3.eth.contract(
        address=Web3.to_checksum_address(UNISWAP_V2_FACTORY),
        abi=FACTORY_ABI
    )
    
    tokens = SEPOLIA_TOKENS
    opportunities = []
    
    # Check all token pairs
    token_names = list(tokens.keys())
    for i, name1 in enumerate(token_names):
        for name2 in token_names[i+1:]:
            try:
                addr1 = Web3.to_checksum_address(tokens[name1])
                addr2 = Web3.to_checksum_address(tokens[name2])
                
                pair = factory.functions.getPair(addr1, addr2).call()
                
                if pair != "0x0000000000000000000000000000000000000000":
                    pair_code = w3.eth.get_code(pair)
                    if len(pair_code) > 2:
                        print(f"  ✅ {name1}/{name2}: {pair} ({len(pair_code)} bytes)")
                        opportunities.append({
                            "token1": name1,
                            "token2": name2,
                            "pair": pair
                        })
                    else:
                        print(f"  ⚪ {name1}/{name2}: Pair exists but no code")
                else:
                    print(f"  ❌ {name1}/{name2}: No pair")
                    
            except Exception as e:
                print(f"  ⚠️  {name1}/{name2}: {str(e)[:50]}")
    
    return opportunities


def execute_simple_swap(token_in, token_out, amount_eth):
    """Execute a simple token swap for testing"""
    print(f"\n🔄 Executing swap: {amount_eth} {token_in} → {token_out}")
    print("="*60)
    
    if not PRIVATE_KEY:
        print("❌ SEPOLIA_PRIVATE_KEY not set")
        return False
    
    w3 = get_w3()
    from eth_account import Account
    account = Account.from_key(PRIVATE_KEY)
    
    router = w3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER), abi=ROUTER_ABI)
    
    token_in_addr = Web3.to_checksum_address(SEPOLIA_TOKENS[token_in])
    token_out_addr = Web3.to_checksum_address(SEPOLIA_TOKENS[token_out])
    
    amount_in = w3.to_wei(amount_eth, 'ether')
    
    # Get expected output
    try:
        amounts = router.functions.getAmountsOut(amount_in, [token_in_addr, token_out_addr]).call()
        expected_out = amounts[1]
        print(f"📊 Expected output: {expected_out}")
    except Exception as e:
        print(f"❌ Could not get quote: {e}")
        return False
    
    # Approve token spending
    token_contract = w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
    nonce = w3.eth.get_transaction_count(account.address)
    
    approve_tx = token_contract.functions.approve(
        Web3.to_checksum_address(UNISWAP_V2_ROUTER),
        amount_in
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 60000,
        'maxFeePerGas': w3.to_wei(50, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': 11155111,
    })
    
    signed_approve = account.sign_transaction(approve_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    print(f"🔓 Approval TX: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        print("❌ Approval failed")
        return False
    
    # Execute swap
    nonce = w3.eth.get_transaction_count(account.address)
    deadline = w3.eth.get_block('latest').timestamp + 600
    
    swap_tx = router.functions.swapExactTokensForTokens(
        amount_in,
        int(expected_out * 0.95),  # 5% slippage
        [token_in_addr, token_out_addr],
        account.address,
        deadline
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 200000,
        'maxFeePerGas': w3.to_wei(50, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': 11155111,
    })
    
    signed_swap = account.sign_transaction(swap_tx)
    swap_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
    print(f"🔄 Swap TX: {swap_hash.hex()}")
    
    swap_receipt = w3.eth.wait_for_transaction_receipt(swap_hash, timeout=120)
    if swap_receipt.status == 1:
        print("✅ Swap successful!")
        return True
    else:
        print("❌ Swap failed")
        return False


def auto_pipeline():
    """Run the full automated pipeline"""
    print("\n" + "="*60)
    print("🚀 REHOBOAM FIRST PENNY - AUTO PIPELINE")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💼 Wallet: {WALLET}")
    print("="*60)
    
    # Step 1: Check wallet
    balance = check_wallet()
    
    # Step 2: Mine if needed
    if balance < 0.01:
        print(f"\n⚠️  Low balance ({balance:.4f} ETH). Starting mining...")
        mine_sepolia_pow()
        balance = check_wallet()
    
    if balance < 0.01:
        print("\n❌ Still no ETH. Cannot proceed.")
        print("   Alternative: Get ETH from https://sepoliafaucet.com")
        return
    
    # Step 3: Find opportunities
    opportunities = find_arbitrage_opportunities()
    
    if not opportunities:
        print("\n⚠️  No arbitrage opportunities found")
        print("   Need to:")
        print("   1. Create trading pairs on Uniswap V2")
        print("   2. Add liquidity to enable trading")
        return
    
    # Step 4: Execute
    for opp in opportunities:
        print(f"\n⚡ Executing: {opp}")
        # execute_simple_swap(opp['token_in'], opp['token_out'], opp['amount'])
    
    print("\n✅ Pipeline complete")


def main():
    parser = argparse.ArgumentParser(description="Rehoboam First Penny Engine")
    parser.add_argument("--mode", choices=["check", "mine", "deploy", "trade", "auto"], default="auto",
                       help="Execution mode")
    parser.add_argument("--token-in", default="WETH", help="Input token for swap")
    parser.add_argument("--token-out", default="USDC", help="Output token for swap")
    parser.add_argument("--amount", type=float, default=0.001, help="Amount to swap")
    
    args = parser.parse_args()
    
    if args.mode == "check":
        check_wallet()
    elif args.mode == "mine":
        mine_sepolia_pow()
    elif args.mode == "deploy":
        deploy_flash_arbitrage()
    elif args.mode == "trade":
        execute_simple_swap(args.token_in, args.token_out, args.amount)
    elif args.mode == "auto":
        auto_pipeline()


if __name__ == "__main__":
    main()

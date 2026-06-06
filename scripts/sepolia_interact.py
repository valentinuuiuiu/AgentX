#!/usr/bin/env python3
"""
Rehoboam Sepolia Interact — Direct Web3 + Playwright MetaMask Bridge
=====================================================================
Interacts with Sepolia testnet via:
1. Direct Web3.py for read operations & transactions (if private key available)
2. Playwright + Firefox for MetaMask interactions (browser automation)

Usage:
    python3 scripts/sepolia_interact.py --check          # Check wallet balances
    python3 scripts/sepolia_interact.py --faucet          # Request Sepolia ETH from faucets
    python3 scripts/sepolia_interabt.py --swap            # Execute test swap on Uniswap
    python3 scripts/sepolia_interact.py --metamask        # Open Firefox with MetaMask
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from web3 import Web3

# Sepolia configuration
SEPOLIA_CHAIN_ID = 11155111
SEPOLIA_RPC = os.getenv("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
ALCHEMY_RPC = os.getenv("SEPOLIA_RPC_URL", "")

# Fallback RPCs
FALLBACK_RPCS = [
    "https://ethereum-sepolia-rpc.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
    "https://rpc.sepolia.ethpandaops.io",
]

# Known Sepolia token addresses (well-known deployed tokens)
SEPOLIA_TOKENS = {
    "WETH": {
        "address": "0xC558DB57039C6E8E0A6ad8A51C573a13E1C0D2A0",
        "decimals": 18,
        "symbol": "WETH",
    },
    "USDC": {
        "address": "0x94a9D9AC8415D5394D6E6f4a0d2782c3F7d13b2e",
        "decimals": 6,
        "symbol": "USDC",
    },
    "DAI": {
        "address": "0xFF34B3D4Aee8ddCd6F9AFF1e12E189D34Da9415b",
        "decimals": 18,
        "symbol": "DAI",
    },
    "LINK": {
        "address": "0xf8Fb3713D3E84F0B9727F97E3493F9e530A5e64e",
        "decimals": 18,
        "symbol": "LINK",
    },
}

# Uniswap V2 Router on Sepolia
UNISWAP_V2_ROUTER = "0xC532a71256731900393Bc4E2350BD5D53D2C0B6E"

# ERC-20 ABI (minimal)
ERC20_ABI = json.loads('[{"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"}]')

# Uniswap V2 Router ABI (minimal for swap)
ROUTER_ABI = json.loads('[{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"fee","type":"uint24"}],"name":"getPool","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"}]')


def get_w3():
    """Get connected Web3 instance"""
    for rpc in [ALCHEMY_RPC] + FALLBACK_RPCS:
        if not rpc:
            continue
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
            if w3.is_connected():
                print(f"✅ Connected to {rpc}")
                return w3
        except Exception:
            continue
    raise ConnectionError("Could not connect to any Sepolia RPC")


def check_balances(w3, address):
    """Check ETH and token balances for an address"""
    addr = Web3.to_checksum_address(address)
    eth_bal = w3.eth.get_balance(addr)
    nonce = w3.eth.get_transaction_count(addr)
    
    print(f"\n{'='*60}")
    print(f"🔍 Wallet: {addr}")
    print(f"💰 ETH Balance: {w3.from_wei(eth_bal, 'ether'):.6f} ETH")
    print(f"📊 Nonce: {nonce}")
    print(f"🧱 Block: {w3.eth.block_number}")
    print(f"{'='*60}")
    
    print("\n📋 Token Balances:")
    for name, token_info in SEPOLIA_TOKENS.items():
        try:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_info["address"]),
                abi=ERC20_ABI
            )
            bal = contract.functions.balanceOf(addr).call()
            decimals = token_info["decimals"]
            human_bal = bal / (10 ** decimals)
            symbol = contract.functions.symbol().call()
            print(f"  {symbol}: {human_bal:.6f} ({name})")
        except Exception as e:
            print(f"  {name}: ⚠️ Contract not deployed or error: {e}")
    
    return eth_bal


def request_faucet(address):
    """Guide user to Sepolia faucets"""
    print(f"\n🚰 Sepolia Faucets for {address}:")
    print(f"{'='*60}")
    print(f"1. Alchemy Faucet: https://sepoliafaucet.com")
    print(f"2. Infura Faucet: https://www.infura.io/faucet/sepolia")
    print(f"3. QuickNode Faucet: https://faucet.quicknode.com/ethereum/sepolia")
    print(f"4. Chainlink Faucet: https://faucets.chain.link/sepolia")
    print(f"5. Google Cloud Faucet: https://cloud.google.com/application/web3/faucet/ethereum/sepolia")
    print(f"\n💡 Paste your address: {address}")
    print(f"{'='*60}")


def open_metamask_firefox():
    """Open Firefox with MetaMask extension using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
        
        print("\n🦊 Opening Firefox with Playwright...")
        print("💡 MetaMask extension needs to be loaded manually or via extension path")
        print("   This opens a browser you can interact with programmatically")
        
        with sync_playwright() as p:
            browser = p.firefox.launch(
                headless=False,
                firefox_user_prefs={
                    "dom.webnotifications.enabled": False,
                    "privacy.resistFingerprinting": False,
                }
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            
            # Navigate to Sepolia network info
            page.goto("https://sepolia.etherscan.io")
            print("✅ Firefox opened — navigate to your MetaMask wallet")
            print("   Press Ctrl+C to close when done")
            
            # Keep browser open
            try:
                page.wait_for_timeout(600000)  # 10 minutes
            except KeyboardInterrupt:
                print("\n🛑 Closing browser...")
            
            browser.close()
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && python3 -m playwright install firefox")
    except Exception as e:
        print(f"❌ Error: {e}")


def send_eth(w3, private_key, to_address, amount_eth):
    """Send ETH on Sepolia"""
    from eth_account import Account
    
    account = Account.from_key(private_key)
    from_addr = account.address
    to_addr = Web3.to_checksum_address(to_address)
    
    nonce = w3.eth.get_transaction_count(from_addr)
    gas_price = w3.eth.gas_price
    
    tx = {
        'nonce': nonce,
        'to': to_addr,
        'value': w3.to_wei(amount_eth, 'ether'),
        'gas': 21000,
        'maxFeePerGas': min(gas_price * 2, w3.to_wei(50, 'gwei')),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': SEPOLIA_CHAIN_ID,
    }
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    print(f"📤 Transaction sent: {tx_hash.hex()}")
    print(f"🔗 View: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"✅ Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
    print(f"⛽ Gas used: {receipt.gasUsed}")
    
    return tx_hash.hex()


def wrap_eth_to_weth(w3, private_key, amount_eth):
    """Wrap ETH to WETH on Sepolia"""
    from eth_account import Account
    
    account = Account.from_key(private_key)
    from_addr = account.address
    
    weth_addr = Web3.to_checksum_address(SEPOLIA_TOKENS["WETH"]["address"])
    weth = w3.eth.contract(address=weth_addr, abi=ERC20_ABI)
    
    # WETH deposit function signature
    deposit_abi = json.loads('[{"inputs":[],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"}]')
    weth_full = w3.eth.contract(address=weth_addr, abi=ERC20_ABI + deposit_abi)
    
    nonce = w3.eth.get_transaction_count(from_addr)
    gas_price = w3.eth.gas_price
    
    tx = weth_full.functions.deposit().build_transaction({
        'from': from_addr,
        'value': w3.to_wei(amount_eth, 'ether'),
        'nonce': nonce,
        'gas': 50000,
        'maxFeePerGas': min(gas_price * 2, w3.to_wei(50, 'gwei')),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': SEPOLIA_CHAIN_ID,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    print(f"🔄 Wrapping {amount_eth} ETH → WETH")
    print(f"📤 TX: {tx_hash.hex()}")
    print(f"🔗 View: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"✅ Status: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
    
    return tx_hash.hex()


def approve_token(w3, private_key, token_name, spender, amount):
    """Approve token spending"""
    from eth_account import Account
    
    account = Account.from_key(private_key)
    from_addr = account.address
    
    token_info = SEPOLIA_TOKENS[token_name]
    token_addr = Web3.to_checksum_address(token_info["address"])
    spender_addr = Web3.to_checksum_address(spender)
    
    token = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    
    # Check current allowance
    current_allowance = token.functions.allowance(from_addr, spender_addr).call()
    if current_allowance >= amount:
        print(f"✅ {token_name} already approved for {spender}")
        return current_allowance
    
    nonce = w3.eth.get_transaction_count(from_addr)
    gas_price = w3.eth.gas_price
    
    max_approval = 2**256 - 1  # Unlimited approval
    
    tx = token.functions.approve(spender_addr, max_approval).build_transaction({
        'from': from_addr,
        'nonce': nonce,
        'gas': 60000,
        'maxFeePerGas': min(gas_price * 2, w3.to_wei(50, 'gwei')),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': SEPOLIA_CHAIN_ID,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    print(f"🔓 Approving {token_name} for {spender}")
    print(f"📤 TX: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"✅ Approval: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
    
    return tx_hash.hex()


def swap_tokens(w3, private_key, from_token, to_token, amount_in):
    """Swap tokens on Uniswap V2 Sepolia"""
    from eth_account import Account
    
    account = Account.from_key(private_key)
    from_addr = account.address
    
    router_addr = Web3.to_checksum_address(UNISWAP_V2_ROUTER)
    router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)
    
    from_info = SEPOLIA_TOKENS[from_token]
    to_info = SEPOLIA_TOKENS[to_token]
    
    from_addr_token = Web3.to_checksum_address(from_info["address"])
    to_addr_token = Web3.to_checksum_address(to_info["address"])
    
    amount_in_wei = int(amount_in * (10 ** from_info["decimals"]))
    
    # Get expected output
    try:
        amounts_out = router.functions.getAmountsOut(amount_in_wei, [from_addr_token, to_addr_token]).call()
        expected_out = amounts_out[1]
        expected_human = expected_out / (10 ** to_info["decimals"])
        print(f"📊 Expected output: {expected_human:.6f} {to_token}")
    except Exception as e:
        print(f"⚠️ Could not get price quote: {e}")
        print(f"   Pool may not exist for {from_token}→{to_token} on Sepolia")
        return None
    
    # Approve token spending
    approve_token(w3, private_key, from_token, UNISWAP_V2_ROUTER, amount_in_wei)
    time.sleep(2)
    
    # Set deadline 10 minutes from now
    deadline = w3.eth.get_block('latest').timestamp + 600
    slippage = 0.5  # 0.5% slippage
    amount_out_min = int(expected_out * (1 - slippage / 100))
    
    nonce = w3.eth.get_transaction_count(from_addr)
    gas_price = w3.eth.gas_price
    
    tx = router.functions.swapExactTokensForTokens(
        amount_in_wei,
        amount_out_min,
        [from_addr_token, to_addr_token],
        from_addr,
        deadline
    ).build_transaction({
        'from': from_addr,
        'nonce': nonce,
        'gas': 200000,
        'maxFeePerGas': min(gas_price * 2, w3.to_wei(50, 'gwei')),
        'maxPriorityFeePerGas': w3.to_wei(1, 'gwei'),
        'chainId': SEPOLIA_CHAIN_ID,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    print(f"🔄 Swapping {amount_in} {from_token} → {to_token}")
    print(f"📤 TX: {tx_hash.hex()}")
    print(f"🔗 View: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"✅ Swap: {'SUCCESS' if receipt.status == 1 else 'FAILED'}")
    print(f"⛽ Gas used: {receipt.gasUsed}")
    
    return tx_hash.hex()


def main():
    parser = argparse.ArgumentParser(description="Rehoboam Sepolia Interact")
    parser.add_argument("--check", action="store_true", help="Check wallet balances")
    parser.add_argument("--faucet", action="store_true", help="Show faucet URLs")
    parser.add_argument("--metamask", action="store_true", help="Open Firefox with Playwright")
    parser.add_argument("--send-eth", type=float, help="Send ETH to address")
    parser.add_argument("--to", type=str, help="Destination address for send")
    parser.add_argument("--wrap", type=float, help="Wrap ETH to WETH")
    parser.add_argument("--swap", action="store_true", help="Swap tokens on Uniswap")
    parser.add_argument("--from-token", type=str, default="WETH", help="Source token for swap")
    parser.add_argument("--to-token", type=str, default="USDC", help="Target token for swap")
    parser.add_argument("--amount", type=float, default=0.001, help="Amount for swap/wrap")
    parser.add_argument("--address", type=str, help="Wallet address (default: from .env)")
    
    args = parser.parse_args()
    
    # Get address
    address = args.address or os.getenv("FLASH_ARB_MASTER", "0x96f15Fe7Da0f32EB3a77e4eA5bf55bc2CAc29844")
    
    w3 = get_w3()
    
    if args.check:
        check_balances(w3, address)
    
    elif args.faucet:
        request_faucet(address)
    
    elif args.metamask:
        open_metamask_firefox()
    
    elif args.send_eth:
        private_key = os.getenv("PRIVATE_KEY") or os.getenv("SEPOLIA_PRIVATE_KEY")
        if not private_key:
            print("❌ Set PRIVATE_KEY or SEPOLIA_PRIVATE_KEY in .env to send transactions")
            sys.exit(1)
        if not args.to:
            print("❌ Specify --to <address> to send ETH")
            sys.exit(1)
        send_eth(w3, private_key, args.to, args.send_eth)
    
    elif args.wrap:
        private_key = os.getenv("PRIVATE_KEY") or os.getenv("SEPOLIA_PRIVATE_KEY")
        if not private_key:
            print("❌ Set PRIVATE_KEY or SEPOLIA_PRIVATE_KEY in .env to wrap ETH")
            sys.exit(1)
        wrap_eth_to_weth(w3, private_key, args.wrap)
    
    elif args.swap:
        private_key = os.getenv("PRIVATE_KEY") or os.getenv("SEPOLIA_PRIVATE_KEY")
        if not private_key:
            print("❌ Set PRIVATE_KEY or SEPOLIA_PRIVATE_KEY in .env to swap tokens")
            sys.exit(1)
        swap_tokens(w3, private_key, args.from_token, args.to_token, args.amount)
    
    else:
        # Default: check balances
        check_balances(w3, address)
        print(f"\n💡 Use --help for more options")
        print(f"   --check     Check balances")
        print(f"   --faucet    Show faucet URLs")
        print(f"   --metamask  Open Firefox browser")
        print(f"   --swap      Swap tokens on Uniswap")


if __name__ == "__main__":
    main()
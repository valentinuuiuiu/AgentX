#!/usr/bin/env python3
"""
Rehoboam System Integration Verifier
Tests all MCP servers, Web3 connections, and service integrations
"""

import os
import requests
import json
import time
import sys
from datetime import datetime

class RehoboamVerifier:
    def __init__(self):
        self.base_url = "http://localhost:5002"
        alchemy_key = os.environ.get("ALCHEMY_API_KEY", "")
        if not alchemy_key:
            print("⚠️ WARNING: ALCHEMY_API_KEY not found in environment. Web3 tests may fail.")
        self.mcp_services = {
            "registry": {"port": 3001, "url": "http://localhost:3001", "name": "MCP Registry"},
            "consciousness": {"port": 3600, "url": "http://localhost:3600", "name": "Consciousness Layer"},
            "function-gemma": {"port": 3111, "url": "http://localhost:3111", "name": "Function Gemma"},
            "etherscan": {"port": 3101, "url": "http://localhost:3101", "name": "Etherscan Analyzer"},
            "chainlink": {"port": 3102, "url": "http://localhost:3102", "name": "Chainlink Feeds"},
            "trading-agents": {"port": 3700, "url": "http://localhost:3700", "name": "Trading Agents"}
        }
        self.web3_chains = {
            "ethereum": {"rpc": f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}", "name": "Ethereum"},
            "polygon": {"rpc": f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}", "name": "Polygon"},
            "arbitrum": {"rpc": f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}", "name": "Arbitrum"},
            "optimism": {"rpc": f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}", "name": "Optimism"}
        }
        
    def test_mcp_service(self, service_name, service_info):
        """Test if an MCP service is responding"""
        try:
            print(f"  Testing {service_info['name']}...", end=" ")
            response = requests.get(f"{service_info['url']}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ OK (HTTP {response.status_code})")
                return True
            else:
                print(f"✗ Error (HTTP {response.status_code})")
                return False
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection refused")
            return False
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            return False
    
    def test_web3_connection(self, chain_name, chain_info):
        """Test Web3 RPC connection"""
        try:
            print(f"  Testing {chain_info['name']}...", end=" ")
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            response = requests.post(chain_info['rpc'], json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    block_num = int(data['result'], 16)
                    print(f"✓ OK (Block: {block_num:,})")
                    return True
            print(f"✗ Error (HTTP {response.status_code})")
            return False
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            return False
    
    def test_api_endpoint(self):
        """Test main Rehoboam API"""
        try:
            print("  Testing Rehoboam API...", end=" ")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ OK (HTTP {response.status_code})")
                return True
            else:
                print(f"✗ Error (HTTP {response.status_code})")
                return False
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            return False
    
    def verify_all(self):
        """Run complete verification"""
        print("=" * 60)
        print(f"Rehoboam System Verification")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        results = {
            "mcp_services": {},
            "web3_chains": {},
            "api": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test MCP Services
        print("\n[1/3] Testing MCP Services:")
        mcp_ok = 0
        for service_name, service_info in self.mcp_services.items():
            if self.test_mcp_service(service_name, service_info):
                results["mcp_services"][service_name] = "OK"
                mcp_ok += 1
            else:
                results["mcp_services"][service_name] = "ERROR"
        
        # Test Web3 Connections
        print("\n[2/3] Testing Web3 RPC Connections:")
        web3_ok = 0
        for chain_name, chain_info in self.web3_chains.items():
            if self.test_web3_connection(chain_name, chain_info):
                results["web3_chains"][chain_name] = "OK"
                web3_ok += 1
            else:
                results["web3_chains"][chain_name] = "ERROR"
        
        # Test API
        print("\n[3/3] Testing Rehoboam API:")
        results["api"] = self.test_api_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY:")
        print(f"  MCP Services: {mcp_ok}/{len(self.mcp_services)} working")
        print(f"  Web3 Chains: {web3_ok}/{len(self.web3_chains)} working")
        print(f"  API: {'✓ Working' if results['api'] else '✗ Failed'}")
        print("=" * 60)
        
        # Save results
        with open('/home/aryan/free-claude/bittensor/clean_rehoboam_project/verification_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

if __name__ == "__main__":
    verifier = RehoboamVerifier()
    results = verifier.verify_all()
    
    # Exit with error if any critical service is down
    critical_failures = 0
    for service_status in results["mcp_services"].values():
        if service_status != "OK":
            critical_failures += 1
    
    if not results["api"]:
        critical_failures += 1
    
    sys.exit(1 if critical_failures > 0 else 0)

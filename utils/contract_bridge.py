"""
Rehoboam Smart Contract Bridge - Python <-> Solidity Integration
=================================================================

This module connects the Rehoboam AI agent to the on-chain smart contract system.
It provides:
  1. High-level Python wrappers for all Rehoboam contracts
  2. Web3 integration for reading/writing on-chain
  3. Event monitoring (trade executions, vault flows, multi-sig actions)
  4. AI-to-contract command pipeline
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContractConfig:
    """Configuration for a deployed contract instance."""
    name: str
    address: str
    abi: Optional[Dict[str, Any]] = None


class SmartContractBridge:
    """
    Python bridge to Rehoboam's on-chain contracts.

    Usage:
        bridge = SmartContractBridge(rpc_url="...", private_key="...")
        await bridge.connect()
        status = await bridge.get_vault_stats()
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        chain_id: int = 31337,  # Default: Anvil local
    ):
        self.rpc_url = rpc_url or os.environ.get("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.private_key = private_key or os.environ.get("PRIVATE_KEY")
        self.chain_id = chain_id

        self._web3 = None
        self._account = None
        self._contracts: Dict[str, ContractConfig] = {}

    async def connect(self) -> bool:
        """Initialize Web3 connection and account."""
        try:
            from web3 import Web3

            self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            is_connected = self._web3.is_connected()
            logger.info(f"Web3 connected to {self.rpc_url}: {is_connected}")

            if self.private_key:
                self._account = self._web3.eth.account.from_key(self.private_key)
                logger.info(f"Account: {self._account.address}")

            return is_connected

        except ImportError:
            logger.warning("web3 not installed. Install: pip install web3")
            return False
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def register_contract(self, config: ContractConfig):
        """Register a deployed contract address."""
        self._contracts[config.name] = config
        logger.info(f"Registered contract: {config.name} at {config.address}")

    def register_contracts(self, addresses: Dict[str, str]):
        """Register multiple contracts at once."""
        for name, address in addresses.items():
            self.register_contract(ContractConfig(name=name, address=address))

    # ============================================================
    # VAULT OPERATIONS (VetalGuardedVault)
    # ============================================================
    async def contribute_to_vault(
        self, vault_address: str, amount_wei: int, intention: str
    ) -> Dict[str, Any]:
        """
        Contribute ETH to the LivingAbundanceDistributor vault.

        Args:
            vault_address: Deployed vault contract address
            amount_wei: Amount in wei
            intention: Human-readable intention string
        """
        from web3 import Web3

        if not self._account:
            return {"success": False, "error": "No account configured"}

        # Minimal ABI for contributeAbundance
        abi = [
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "intention",
                        "type": "string",
                    }
                ],
                "name": "contributeAbundance",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function",
            },
            {
                "inputs": [],
                "name": "getVaultStats",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "balance",
                        "type": "uint256",
                    },
                    {
                        "internalType": "uint256",
                        "name": "totalContributed",
                        "type": "uint256",
                    },
                    {
                        "internalType": "uint256",
                        "name": "totalLessons",
                        "type": "uint256",
                    },
                    {
                        "internalType": "uint256",
                        "name": "wisdomCount",
                        "type": "uint256",
                    },
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(vault_address), abi=abi
        )

        try:
            tx = contract.functions.contributeAbundance(intention).build_transaction({
                "from": self._account.address,
                "value": amount_wei,
                "nonce": self._web3.eth.get_transaction_count(self._account.address),
                "gas": 300000,
                "gasPrice": self._web3.eth.gas_price,
            })

            signed_tx = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "gas_used": receipt["gasUsed"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def request_vault_abundance(
        self,
        vault_address: str,
        amount_wei: int,
        intention: str,
    ) -> Dict[str, Any]:
        """Request abundance flow from the vault."""
        from web3 import Web3

        if not self._account:
            return {"success": False, "error": "No account configured"}

        abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "string", "name": "intention", "type": "string"},
                ],
                "name": "requestAbundanceFlow",
                "outputs": [
                    {"internalType": "uint256", "name": "", "type": "uint256"}
                ],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        ]

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(vault_address), abi=abi
        )

        try:
            tx = contract.functions.requestAbundanceFlow(
                amount_wei, intention
            ).build_transaction({
                "from": self._account.address,
                "nonce": self._web3.eth.get_transaction_count(self._account.address),
                "gas": 300000,
                "gasPrice": self._web3.eth.gas_price,
            })

            signed_tx = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_vault_stats(
        self, vault_address: str
    ) -> Dict[str, Any]:
        """Read vault statistics (view function, no gas)."""
        from web3 import Web3

        if not self._web3:
            return {"error": "Not connected"}

        abi = [
            {
                "inputs": [],
                "name": "getVaultStats",
                "outputs": [
                    {"internalType": "uint256", "name": "balance", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalContributed", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalLessons", "type": "uint256"},
                    {"internalType": "uint256", "name": "wisdomCount", "type": "uint256"},
                ],
                "stateMutability": "view",
                "type": "function",
            }
        ]

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(vault_address), abi=abi
        )

        try:
            balance, contributed, lessons, wisdom = contract.functions.getVaultStats().call()
            return {
                "success": True,
                "balance_wei": balance,
                "balance_eth": self._web3.from_wei(balance, "ether"),
                "total_contributed_wei": contributed,
                "total_lessons": lessons,
                "wisdom_entries": wisdom,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # TRADE EXECUTOR OPERATIONS
    # ============================================================
    async def register_strategy(
        self, executor_address: str, strategy_id: bytes, min_profit_bps: int
    ) -> Dict[str, Any]:
        """Register a trading strategy with the TradeExecutor."""
        from web3 import Web3

        if not self._account:
            return {"success": False, "error": "No account configured"}

        abi = [
            {
                "inputs": [
                    {"internalType": "bytes32", "name": "strategyId", "type": "bytes32"},
                    {"internalType": "uint256", "name": "minProfitBps", "type": "uint256"},
                    {"internalType": "address", "name": "executor", "type": "address"},
                ],
                "name": "registerStrategy",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            }
        ]

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(executor_address), abi=abi
        )

        try:
            tx = contract.functions.registerStrategy(
                strategy_id, min_profit_bps, self._account.address
            ).build_transaction({
                "from": self._account.address,
                "nonce": self._web3.eth.get_transaction_count(self._account.address),
                "gas": 300000,
                "gasPrice": self._web3.eth.gas_price,
            })

            signed_tx = self._web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================
    # EVENT MONITORING
    # ============================================================
    async def watch_trades(
        self, executor_address: str, from_block: Optional[int] = None,
        to_block: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch TradeExecuted events from the TradeExecutor."""
        from web3 import Web3

        if not self._web3:
            return [{"error": "Not connected"}]

        # TradeExecuted event signature
        event_abi = {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "trader", "type": "address"},
                {"indexed": True, "name": "tokenIn", "type": "address"},
                {"indexed": True, "name": "tokenOut", "type": "address"},
                {"indexed": False, "name": "amountIn", "type": "uint256"},
                {"indexed": False, "name": "amountOut", "type": "uint256"},
                {"indexed": False, "name": "profit", "type": "uint256"},
                {"indexed": False, "name": "strategyName", "type": "string"},
            ],
            "name": "TradeExecuted",
            "type": "event",
        }

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(executor_address),
            abi=[event_abi],
        )

        try:
            logs = contract.events.TradeExecuted.get_logs(
                from_block=from_block or 0,
                to_block=to_block or "latest",
            )
            return [log for log in logs]
        except Exception as e:
            return [{"error": str(e)}]

    async def watch_vault_flows(
        self, vault_address: str, from_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch AbundanceRequested and AbundanceReceived events."""
        from web3 import Web3

        if not self._web3:
            return [{"error": "Not connected"}]

        events_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "soul", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "newAbundanceScore", "type": "uint256"},
                ],
                "name": "AbundanceReceived",
                "type": "event",
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "flowId", "type": "uint256"},
                    {"indexed": True, "name": "soul", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "intention", "type": "string"},
                ],
                "name": "AbundanceRequested",
                "type": "event",
            },
        ]

        contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(vault_address), abi=events_abi
        )

        try:
            received = contract.events.AbundanceReceived.get_logs(
                from_block=from_block or 0, to_block="latest"
            )
            requested = contract.events.AbundanceRequested.get_logs(
                from_block=from_block or 0, to_block="latest"
            )
            return list(received) + list(requested)
        except Exception as e:
            return [{"error": str(e)}]


# Global instance
contract_bridge = SmartContractBridge()

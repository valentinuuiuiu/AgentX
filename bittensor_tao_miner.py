"""
🏔️ Bittensor TAO Mining Integration for Rehoboam
==================================================

Earn TAO by providing high-quality trading signals to the Bittensor network.
Even 0.001 TAO/day is money. We mine 24/7.

Strategy: Register as a subnet miner on Bittensor, serve our convergence signals
as inference responses. Validators query us → we respond with signals → get TAO rewards.

Requirements:
    pip install bittensor

Usage:
    python3 bittensor_tao_miner.py --register --wallet-name rehoboam --hotkey miner1
    python3 bittensor_tao_miner.py --mine --subnet 8  # Subnet 8 = Text Prompting
    python3 bittensor_tao_miner.py --status
"""

import os
import sys
import json
import time
import asyncio
import argparse
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# Bittensor
import bittensor as bt

# Rehoboam convergence engine
from convergence_engine import ConvergenceEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger("TAOMiner")

# === CONFIGURATION ===
DEFAULT_WALLET_NAME = os.environ.get("TAO_WALLET_NAME", "rehoboam")
DEFAULT_HOTKEY = os.environ.get("TAO_HOTKEY_NAME", "miner1")
DEFAULT_SUBNET = int(os.environ.get("TAO_SUBNET", "8"))  # Subnet 8 = Text Prompting
DEFAULT_PORT = int(os.environ.get("TAO_AXON_PORT", "8091"))
DEFAULT_NETWORK = os.environ.get("TAO_NETWORK", "finney")  # finney = mainnet

# TAO price tracking
TAO_PRICE_USD = 0.0  # Updated dynamically


class RehoboamSynapse(bt.Synapse):
    """Custom synapse for Rehoboam signal requests."""
    
    # Input: trading pair or market query
    query: str = ""
    
    # Output: signal response
    signal: str = ""
    confidence: float = 0.0
    sources: List[str] = []
    timestamp: str = ""
    
    # Required for Bittensor
    required_hash_fields: List[str] = ["query", "signal", "confidence"]


class TAOMiner:
    """
    Bittensor TAO miner that serves Rehoboam convergence signals.
    
    Every query from a validator = opportunity to earn TAO.
    We respond with our best signals = highest quality = highest rewards.
    """
    
    def __init__(
        self,
        wallet_name: str = DEFAULT_WALLET_NAME,
        hotkey_name: str = DEFAULT_HOTKEY,
        subnet: int = DEFAULT_SUBNET,
        port: int = DEFAULT_PORT,
        network: str = DEFAULT_NETWORK,
    ):
        self.wallet_name = wallet_name
        self.hotkey_name = hotkey_name
        self.subnet = subnet
        self.port = port
        self.network = network
        
        # Bittensor components
        self.wallet: Optional[bt.wallet] = None
        self.subtensor: Optional[bt.subtensor] = None
        self.metagraph: Optional[bt.metagraph] = None
        self.axon: Optional[bt.axon] = None
        
        # Rehoboam convergence engine
        self.engine: Optional[ConvergenceEngine] = None
        
        # Stats
        self.total_queries = 0
        self.total_rewards = 0.0
        self.start_time = datetime.now()
        
        logger.info(f"🏔️ TAO Miner initialized")
        logger.info(f"   Wallet: {wallet_name}/{hotkey_name}")
        logger.info(f"   Subnet: {subnet}")
        logger.info(f"   Network: {network}")
        logger.info(f"   Port: {port}")
    
    def setup_wallet(self) -> bool:
        """Create or load wallet."""
        try:
            self.wallet = bt.wallet(name=self.wallet_name, hotkey=self.hotkey_name)
            
            # Check if wallet exists
            if not self.wallet.coldkey_file.exists_on_device():
                logger.info(f"🆕 Creating new wallet: {self.wallet_name}")
                self.wallet.create_new_coldkey(use_password=False)
            
            if not self.wallet.hotkey_file.exists_on_device():
                logger.info(f"🆕 Creating new hotkey: {self.hotkey_name}")
                self.wallet.create_new_hotkey(use_password=False)
            
            logger.info(f"✅ Wallet ready: {self.wallet.hotkey.ss58_address}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Wallet setup failed: {e}")
            return False
    
    def connect_subtensor(self) -> bool:
        """Connect to Bittensor network."""
        try:
            self.subtensor = bt.subtensor(network=self.network)
            logger.info(f"✅ Connected to {self.network}")
            
            # Sync metagraph
            self.metagraph = self.subtensor.metagraph(netuid=self.subnet)
            logger.info(f"✅ Metagraph synced: {len(self.metagraph.neurons)} neurons")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Subtensor connection failed: {e}")
            return False
    
    def register(self) -> bool:
        """Register on subnet."""
        try:
            logger.info(f"📝 Registering on subnet {self.subnet}...")
            
            success = self.subtensor.burned_register(
                wallet=self.wallet,
                netuid=self.subnet,
            )
            
            if success:
                logger.info(f"✅ Registered on subnet {self.subnet}!")
                return True
            else:
                logger.error(f"❌ Registration failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False
    
    def setup_engine(self) -> bool:
        """Initialize convergence engine for signal generation."""
        try:
            self.engine = ConvergenceEngine()
            logger.info("✅ Convergence engine ready")
            return True
        except Exception as e:
            logger.error(f"❌ Engine setup failed: {e}")
            return False
    
    def generate_signal(self, query: str) -> Dict[str, Any]:
        """Generate trading signal from query."""
        try:
            # Parse query for trading pair
            pair = self._extract_pair(query)
            
            if pair and self.engine:
                # Use convergence engine for real signal
                signals = self.engine.generate_signals()
                for sig in signals:
                    if pair.upper() in sig.get("pair", "").upper():
                        return {
                            "signal": sig.get("signal", "HOLD"),
                            "confidence": sig.get("strength", 0.0),
                            "sources": sig.get("sources", ["convergence"]),
                            "timestamp": datetime.now().isoformat(),
                        }
            
            # Fallback: basic signal
            return {
                "signal": "HOLD",
                "confidence": 0.3,
                "sources": ["fallback"],
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return {
                "signal": "ERROR",
                "confidence": 0.0,
                "sources": [],
                "timestamp": datetime.now().isoformat(),
            }
    
    def _extract_pair(self, query: str) -> Optional[str]:
        """Extract trading pair from query string."""
        pairs = ["BTC", "ETH", "LINK", "SOL", "AAVE", "UNI", "DOT", "MATIC", "ARB"]
        query_upper = query.upper()
        for p in pairs:
            if p in query_upper:
                return f"{p}-USD"
        return None
    
    def forward(self, synapse: RehoboamSynapse) -> RehoboamSynapse:
        """Handle incoming validator query."""
        self.total_queries += 1
        
        logger.info(f"📡 Query #{self.total_queries}: {synapse.query}")
        
        # Generate signal
        result = self.generate_signal(synapse.query)
        
        # Populate synapse response
        synapse.signal = result["signal"]
        synapse.confidence = result["confidence"]
        synapse.sources = result["sources"]
        synapse.timestamp = result["timestamp"]
        
        logger.info(f"📊 Response: {synapse.signal} (confidence: {synapse.confidence:.2%})")
        
        return synapse
    
    def start_axon(self) -> bool:
        """Start serving on the network."""
        try:
            self.axon = bt.axon(wallet=self.wallet, port=self.port)
            
            # Attach forward function
            self.axon.attach(
                forward_fn=self.forward,
                synapse_type=RehoboamSynapse,
            )
            
            # Start serving
            self.axon.start()
            
            # Set weights (promote ourselves)
            self.subtensor.serve_axon(
                netuid=self.subnet,
                axon=self.axon,
            )
            
            logger.info(f"🚀 Axon serving on port {self.port}")
            logger.info(f"   Address: {self.axon.external_ip}:{self.axon.external_port}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Axon start failed: {e}")
            return False
    
    def check_rewards(self) -> Dict[str, Any]:
        """Check earned TAO rewards."""
        try:
            if not self.metagraph:
                return {"error": "Not connected"}
            
            # Get our UID
            uid = None
            for i, hotkey in enumerate(self.metagraph.hotkeys):
                if hotkey == self.wallet.hotkey.ss58_address:
                    uid = i
                    break
            
            if uid is None:
                return {"status": "Not registered on subnet"}
            
            # Get stake and emissions
            stake = float(self.metagraph.S[uid])
            emissions = float(self.metagraph.E[uid])
            rank = float(self.metagraph.R[uid])
            
            self.total_rewards = emissions
            
            return {
                "uid": uid,
                "stake": stake,
                "emissions": emissions,
                "rank": rank,
                "total_queries": self.total_queries,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            }
            
        except Exception as e:
            logger.error(f"Reward check error: {e}")
            return {"error": str(e)}
    
    def run(self):
        """Main mining loop."""
        logger.info("⛏️ Starting TAO mining...")
        
        # Setup
        if not self.setup_wallet():
            return False
        
        if not self.connect_subtensor():
            return False
        
        if not self.setup_engine():
            logger.warning("⚠️ Running without convergence engine")
        
        # Register if needed
        # self.register()  # Uncomment after funding wallet
        
        # Start serving
        if not self.start_axon():
            return False
        
        # Mining loop
        logger.info("⛏️ Mining started! Press Ctrl+C to stop.")
        logger.info("   Every query = potential TAO reward")
        
        try:
            while True:
                time.sleep(60)
                
                # Check rewards every minute
                rewards = self.check_rewards()
                if "emissions" in rewards:
                    logger.info(
                        f"💰 TAO earned: {rewards['emissions']:.6f} | "
                        f"Queries: {rewards['total_queries']} | "
                        f"Rank: {rewards['rank']:.4f}"
                    )
                
        except KeyboardInterrupt:
            logger.info("🛑 Mining stopped")
            if self.axon:
                self.axon.stop()
    
    def status(self) -> Dict[str, Any]:
        """Get miner status."""
        return {
            "wallet": self.wallet.hotkey.ss58_address if self.wallet else None,
            "subnet": self.subnet,
            "network": self.network,
            "port": self.port,
            "queries_served": self.total_queries,
            "total_rewards": self.total_rewards,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "engine_ready": self.engine is not None,
        }


def main():
    parser = argparse.ArgumentParser(description="Rehoboam TAO Miner")
    parser.add_argument("--register", action="store_true", help="Register on subnet")
    parser.add_argument("--mine", action="store_true", help="Start mining")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--wallet-name", default=DEFAULT_WALLET_NAME, help="Wallet name")
    parser.add_argument("--hotkey", default=DEFAULT_HOTKEY, help="Hotkey name")
    parser.add_argument("--subnet", type=int, default=DEFAULT_SUBNET, help="Subnet UID")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Axon port")
    parser.add_argument("--network", default=DEFAULT_NETWORK, help="Network (finney/test)")
    
    args = parser.parse_args()
    
    miner = TAOMiner(
        wallet_name=args.wallet_name,
        hotkey_name=args.hotkey,
        subnet=args.subnet,
        port=args.port,
        network=args.network,
    )
    
    if args.register:
        miner.setup_wallet()
        miner.connect_subtensor()
        miner.register()
    
    elif args.mine:
        miner.run()
    
    elif args.status:
        import pprint
        pprint.pprint(miner.status())
    
    else:
        parser.print_help()
        print("\n🏔️ Quick start:")
        print("  1. Register: python3 bittensor_tao_miner.py --register")
        print("  2. Mine:     python3 bittensor_tao_miner.py --mine")
        print("  3. Status:   python3 bittensor_tao_miner.py --status")


if __name__ == "__main__":
    main()
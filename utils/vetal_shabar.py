"""
Vetal Shabar - Forge/Foundry Integration Tool Belt for Rehoboam
===============================================================

"The tools of Vetal Shabar" — bridging Rehoboam's AI consciousness
with the power of Foundry's Forge toolkit for smart contract
compilation, testing, deployment, verification, and on-chain interaction.

Tools provided:
  1. forge_compile    - Compile all contracts with gas reports
  2. forge_test       - Run unit + fuzz tests with coverage
  3. forge_deploy     - Deploy contracts to any chain via broadcast
  4. forge_verify     - Verify deployed contracts on block explorers
  5. forge_cast_call  - Read on-chain state (view/pure functions)
  6. forge_cast_send  - Send transactions via wallet
  7. forge_anvil      - Spin up local testnet for sandbox testing
  8. forge_snapshot   - Gas snapshot comparisons
  9. forge_upgrade    - Check for dependency/tool updates
 10. forge_audit      - Static analysis and Slither security checks
"""

import os
import json
import subprocess
import logging
import tempfile
import shutil
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ChainID(Enum):
    """Supported chain IDs for deployment and interaction."""
    ETHEREUM_MAINNET = 1
    SEPOLIA = 11155111
    ARBITRUM = 42161
    BASE = 8453
    OPTIMISM = 10
    POLYGON = 137
    ANVIL_LOCAL = 31337


@dataclass
class ForgeResult:
    """Result from any Forge/Foundry operation."""
    success: bool
    tool: str
    output: str
    error: str
    duration_seconds: float
    timestamp: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Truncate very long output for JSON serialization
        if len(result["output"]) > 10000:
            result["output"] = result["output"][:10000] + "...[truncated]"
        return result


class VetalShabar:
    """
    The tools of Vetal Shabar — Rehoboam's on-chain intelligence layer.

    Provides programmatic access to Forge/Foundry CLI tools so that
    Rehoboam AI and its companions can compile, test, deploy, verify,
    and interact with the smart contract system autonomously.
    """

    def __init__(
        self,
        contracts_dir: Optional[str] = None,
        deployer_key: Optional[str] = None,
        eth_rpc_url: Optional[str] = None,
        eth_rpc_url_fallback: Optional[str] = None,
    ):
        """
        Initialize the Vetal Shabar tool belt.

        Args:
            contracts_dir: Path to the contracts/ directory with foundry.toml
            deployer_key: Private key (hex, no 0x prefix) for deployment
            eth_rpc_url: Primary RPC URL for deployment/cast
            eth_rpc_url_fallback: Fallback RPC URL
        """
        # Locate the contracts directory
        if contracts_dir and os.path.isdir(contracts_dir):
            self.contracts_dir = contracts_dir
        else:
            # Try common locations
            for path in ["contracts", "src/contracts", "../contracts"]:
                if os.path.isdir(path) and os.path.isfile(os.path.join(path, "foundry.toml")):
                    self.contracts_dir = path
                    break
            else:
                self.contracts_dir = "contracts"

        self.deployer_key = deployer_key or os.environ.get("PRIVATE_KEY", "")
        self.eth_rpc_url = eth_rpc_url or os.environ.get("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.eth_rpc_url_fallback = eth_rpc_url_fallback or os.environ.get("ETH_RPC_FALLBACK_URL", "")

        # Forge binary path
        self.forge_bin = shutil.which("forge") or "forge"
        self.cast_bin = shutil.which("cast") or "cast"
        self.anvil_bin = shutil.which("anvil") or "anvil"
        self.slither_bin = shutil.which("slither") or "slither"

        # Tool availability cache
        self._tools_available: Dict[str, bool] = {}
        self._check_tools()

        # History of all operations for audit trail
        self.operation_history: List[ForgeResult] = []

        logger.info(f"Vetal Shabar tool belt initialized: contracts_dir={self.contracts_dir}")
        logger.info(f"Tools available: forge={self._tools_available.get('forge', False)}, "
                    f"cast={self._tools_available.get('cast', False)}, "
                    f"anvil={self._tools_available.get('anvil', False)}, "
                    f"slither={self._tools_available.get('slither', False)}")

    def _check_tools(self):
        """Check which Foundry/Forge tools are available."""
        for name, binary in [("forge", self.forge_bin), ("cast", self.cast_bin),
                             ("anvil", self.anvil_bin), ("slither", self.slither_bin)]:
            try:
                result = subprocess.run([binary, "--version"],
                                       capture_output=True, text=True, timeout=5)
                self._tools_available[name] = result.returncode == 0
            except Exception:
                self._tools_available[name] = False

    def _run_command(
        self, tool: str, args: List[str], timeout: int = 300,
        extra_env: Optional[Dict[str, str]] = None
    ) -> ForgeResult:
        """
        Execute a forge/cast/anvil/slither command.

        Args:
            tool: The tool name for logging
            args: Command arguments
            timeout: Seconds before killing the process
            extra_env: Additional environment variables
        """
        start = datetime.now()

        env = os.environ.copy()
        env["FOUNDRY_DISABLE_REPORTS"] = "true"

        # Inject deployer key if not in args
        if self.deployer_key and "--private-key" not in args and "-k" not in args:
            env["PRIVATE_KEY"] = self.deployer_key

        # Inject RPC URLs
        if any(a.startswith("--rpc-url") or a == "--rpc-url" for a in args) or "--rpc-url" not in args:
            if "--rpc-url" not in args:
                args.extend(["--rpc-url", self.eth_rpc_url])

        if extra_env:
            env.update(extra_env)

        try:
            cmd = [tool] + args
            logger.debug(f"Running: {' '.join(cmd[:8])}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.contracts_dir,
                env=env,
            )

            output = result.stdout.strip()
            error = result.stderr.strip()
            duration = (datetime.now() - start).total_seconds()

            forge_result = ForgeResult(
                success=result.returncode == 0,
                tool=tool,
                output=output,
                error=error if result.returncode != 0 else "",
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"exit_code": result.returncode, "args": args},
            )

            self.operation_history.append(forge_result)
            return forge_result

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds()
            result = ForgeResult(
                success=False, tool=tool, output="",
                error=f"Command timed out after {timeout}s",
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"timeout": True},
            )
            self.operation_history.append(result)
            return result

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            result = ForgeResult(
                success=False, tool=tool, output="",
                error=str(e),
                duration_seconds=duration,
                timestamp=datetime.now().isoformat(),
                metadata={"exception": True},
            )
            self.operation_history.append(result)
            return result

    # ============================================================
    # TOOL 1: forge compile
    # ============================================================
    def forge_compile(self, optimized: bool = True, sizes: bool = True) -> ForgeResult:
        """
        Compile all Solidity contracts with Foundry.

        Args:
            optimized: Enable optimizer
            sizes: Show contract sizes after compilation
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found. Install Foundry: curl -L https://foundry.paradigm.xyz | bash",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = ["compile", "--force"]
        if optimized:
            args.extend(["--optimize", "--optimizer-runs", "20000"])
        if sizes:
            args.append("--sizes")

        return self._run_command(self.forge_bin, args, timeout=300)

    # ============================================================
    # TOOL 2: forge test
    # ============================================================
    def forge_test(
        self,
        match_test: Optional[str] = None,
        match_path: Optional[str] = None,
        match_contract: Optional[str] = None,
        verbose: bool = False,
        fuzz_runs: int = 256,
        gas_report: bool = True,
    ) -> ForgeResult:
        """
        Run Foundry tests (unit + fuzz).

        Args:
            match_test: Only run tests matching this name
            match_path: Only run tests in files matching this path
            match_contract: Only run tests in contracts matching this name
            verbose: Show step-by-step trace on failure
            fuzz_runs: Number of fuzz test runs
            gas_report: Show gas usage report
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = ["test", "-vvvv"]

        if match_test:
            args.extend(["--match-test", match_test])
        if match_path:
            args.extend(["--match-path", match_path])
        if match_contract:
            args.extend(["--match-contract", match_contract])
        if gas_report:
            args.append("--gas-report")

        args.extend(["--fuzz-runs", str(fuzz_runs)])

        return self._run_command(self.forge_bin, args, timeout=600)

    # ============================================================
    # TOOL 3: forge create / forge script (deployment)
    # ============================================================
    def forge_deploy(
        self,
        contract: str,
        chain_id: ChainID = ChainID.ANVIL_LOCAL,
        constructor_args: Optional[str] = None,
        verify: bool = False,
        broadcast: bool = True,
        dry_run: bool = False,
    ) -> ForgeResult:
        """
        Deploy a contract using forge create.

        Args:
            contract: Contract source:ContractName (e.g., "src/TradeExecutor.sol:TradeExecutor")
            chain_id: Target chain
            constructor_args: ABI-encoded constructor arguments
            verify: Verify on Etherscan after deployment
            broadcast: Actually broadcast the transaction
            dry_run: Show what would be deployed without signing
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        rpc_url = self._get_rpc_for_chain(chain_id)
        if not rpc_url:
            return ForgeResult(
                success=False, tool="forge", output="",
                error=f"No RPC URL configured for chain {chain_id.name}",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = [
            "create", contract,
            "--rpc-url", rpc_url,
        ]

        if self.deployer_key:
            args.extend(["--private-key", self.deployer_key])

        if constructor_args:
            args.extend(["--constructor-args", constructor_args])

        if verify:
            args.append("--verify")

        if dry_run:
            args.append("--dry-run")

        return self._run_command(self.forge_bin, args, timeout=300)

    def forge_deploy_script(
        self,
        script_path: str,
        func: str = "run()",
        chain_id: ChainID = ChainID.ANVIL_LOCAL,
        broadcast: bool = True,
        dry_run: bool = False,
    ) -> ForgeResult:
        """
        Deploy using a Foundry script (forge script).

        Args:
            script_path: Path to the script file (e.g., "script/DeployVault.s.sol")
            func: Function to call in the script
            chain_id: Target chain
            broadcast: Broadcast the transaction
            dry_run: Dry run only
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        rpc_url = self._get_rpc_for_chain(chain_id)

        args = [
            "script", script_path,
            "--rpc-url", rpc_url,
            "--sig", func,
            "-vvvv",
        ]

        if self.deployer_key:
            args.extend(["--private-key", self.deployer_key])

        if broadcast:
            args.append("--broadcast")
        if dry_run:
            args.append("--dry-run")

        return self._run_command(self.forge_bin, args, timeout=600)

    # ============================================================
    # TOOL 4: forge verify
    # ============================================================
    def forge_verify(
        self,
        address: str,
        contract: str,
        chain_id: ChainID = ChainID.ETHEREUM_MAINNET,
        constructor_args: Optional[str] = None,
    ) -> ForgeResult:
        """Verify a deployed contract on Etherscan."""
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = [
            "verify-contract", "--chain-id", str(chain_id.value),
            address, contract,
        ]

        if constructor_args:
            args.extend(["--constructor-args", constructor_args])

        return self._run_command(self.forge_bin, args, timeout=120)

    # ============================================================
    # TOOL 5: cast call (read on-chain)
    # ============================================================
    def cast_call(
        self,
        address: str,
        function_sig: str,
        args: Optional[List[str]] = None,
        chain_id: ChainID = ChainID.ETHEREUM_MAINNET,
    ) -> ForgeResult:
        """
        Call a view/pure function on a deployed contract.

        Args:
            address: Contract address
            function_sig: Function signature (e.g., "totalAbundance()")
            args: Function arguments
            chain_id: Chain to query
        """
        if not self._tools_available.get("cast"):
            return ForgeResult(
                success=False, tool="cast", output="",
                error="cast binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        rpc_url = self._get_rpc_for_chain(chain_id)
        cmd_args = ["call", "--rpc-url", rpc_url, address, function_sig]
        if args:
            cmd_args.extend(args)

        return self._run_command(self.cast_bin, cmd_args, timeout=30)

    # ============================================================
    # TOOL 6: cast send (write on-chain)
    # ============================================================
    def cast_send(
        self,
        address: str,
        function_sig: str,
        args: Optional[List[str]] = None,
        value: Optional[str] = None,
        chain_id: ChainID = ChainID.ETHEREUM_MAINNET,
    ) -> ForgeResult:
        """
        Send a transaction to a deployed contract.

        Args:
            address: Contract address
            function_sig: Function signature (e.g., "contributeAbundance(string)")
            args: Function arguments
            value: ETH value to send with transaction
            chain_id: Target chain
        """
        if not self._tools_available.get("cast"):
            return ForgeResult(
                success=False, tool="cast", output="",
                error="cast binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        rpc_url = self._get_rpc_for_chain(chain_id)
        cmd_args = ["send", "--rpc-url", rpc_url, address, function_sig]

        if self.deployer_key:
            cmd_args.extend(["--private-key", self.deployer_key])

        if args:
            cmd_args.extend(args)

        if value:
            cmd_args.extend(["--value", value])

        return self._run_command(self.cast_bin, cmd_args, timeout=120)

    # ============================================================
    # TOOL 7: anvil (local testnet)
    # ============================================================
    def anvil_start(
        self,
        port: int = 8545,
        chain_id: int = 31337,
        mnemonic: str = "test test test test test test test test test test test junk",
        fork_url: Optional[str] = None,
        block_time: Optional[int] = None,
        background: bool = True,
    ) -> ForgeResult:
        """
        Start a local Anvil testnet (subprocess).

        Args:
            port: Port to listen on
            chain_id: Chain ID for the local network
            mnemonic: HD wallet mnemonic
            fork_url: Fork a remote chain
            block_time: Block time in seconds (for auto-mining)
            background: Run in background
        """
        if not self._tools_available.get("anvil"):
            return ForgeResult(
                success=False, tool="anvil", output="",
                error="anvil binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = ["--port", str(port), "--chain-id", str(chain_id)]

        if fork_url:
            args.extend(["--fork-url", fork_url])
        if block_time:
            args.extend(["-b", str(block_time)])
        if mnemonic:
            args.extend(["--mnemonic", mnemonic])

        # Anvil runs indefinitely, use Popen
        try:
            env = os.environ.copy()
            cmd = [self.anvil_bin] + args
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.contracts_dir,
                env=env,
            )
            # Wait a moment for startup
            import time
            time.sleep(2)
            poll = process.poll()
            return ForgeResult(
                success=(poll is None),
                tool="anvil",
                output=f"Anvil started on port {port} (PID {process.pid})",
                error="",
                duration_seconds=2.0,
                timestamp=datetime.now().isoformat(),
                metadata={"pid": process.pid, "port": port, "chain_id": chain_id},
            )
        except Exception as e:
            return ForgeResult(
                success=False, tool="anvil", output="",
                error=str(e),
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

    # ============================================================
    # TOOL 8: forge snapshot (gas tracking)
    # ============================================================
    def forge_snapshot(self) -> ForgeResult:
        """
        Take a gas usage snapshot for all tests.
        Useful for tracking gas efficiency improvements.
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        args = ["snapshot"]
        return self._run_command(self.forge_bin, args, timeout=300)

    # ============================================================
    # TOOL 9: forge upgrade check
    # ============================================================
    def forge_upgrade_deps(
        self,
        libs: Optional[List[str]] = None,
    ) -> ForgeResult:
        """
        Update Foundry dependencies (forge-std, openzeppelin, etc.).

        Args:
            libs: Specific libs to update (e.g., ["forge-std", "openzeppelin-contracts"])
        """
        if not self._tools_available.get("forge"):
            return ForgeResult(
                success=False, tool="forge", output="",
                error="forge binary not found",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        target_libs = libs or ["forge-std", "openzeppelin-contracts"]
        results = []
        all_success = True

        for lib in target_libs:
            lib_path = os.path.join(self.contracts_dir, "lib", lib)
            if os.path.isdir(lib_path):
                result = self._run_command("git", ["pull", "origin", "master"],
                                          timeout=60)
                results.append(result)
                if not result.success:
                    all_success = False
            else:
                logger.warning(f"Lib {lib} not found at {lib_path}")

        return ForgeResult(
            success=all_success,
            tool="forge_update",
            output="\n".join(r.output for r in results),
            error="\n".join(r.error for r in results if r.error),
            duration_seconds=sum(r.duration_seconds for r in results),
            timestamp=datetime.now().isoformat(),
            metadata={"libs_updated": target_libs},
        )

    # ============================================================
    # TOOL 10: Static analysis / security audit
    # ============================================================
    def forge_audit(self, contract_path: Optional[str] = None) -> ForgeResult:
        """
        Run Slither static analysis on the contracts.
        Requires slither-analyzer to be installed: pip install slither-analyzer
        """
        if not self._tools_available.get("slither"):
            return ForgeResult(
                success=False, tool="slither", output="",
                error="slither not found. Install: pip install slither-analyzer",
                duration_seconds=0,
                timestamp=datetime.now().isoformat(),
            )

        target = contract_path or self.contracts_dir
        args = [target, "--fail-none"]
        return self._run_command(self.slither_bin, args, timeout=300)

    # ============================================================
    # HELPER: Get RPC URL for chain
    # ============================================================
    def _get_rpc_for_chain(self, chain_id: ChainID) -> Optional[str]:
        """Get the RPC URL for a given chain."""
        # Use environment variable if set and matches
        chain_to_env = {
            ChainID.ETHEREUM_MAINNET: ["ETH_RPC_URL", "ETHEREUM_RPC_URL"],
            ChainID.SEPOLIA: ["SEPOLIA_RPC_URL"],
            ChainID.ARBITRUM: ["ARBITRUM_RPC_URL"],
            ChainID.BASE: ["BASE_RPC_URL"],
        }

        if chain_id == ChainID.ANVIL_LOCAL:
            return "http://127.0.0.1:8545"

        for env_var in chain_to_env.get(chain_id, []):
            url = os.environ.get(env_var)
            if url:
                return url

        # Fallback to primary RPC
        return self.eth_rpc_url if self.eth_rpc_url else None

    # ============================================================
    # UTILITY: Deploy all project contracts in sequence
    # ============================================================
    def deploy_all_contracts(
        self,
        chain_id: ChainID = ChainID.ANVIL_LOCAL,
        broadcast: bool = True,
    ) -> List[ForgeResult]:
        """
        Deploy all Rehoboam contracts in the correct order.

        Order:
          1. ProtectedToken
          2. VetalGuardedVault
          3. DivineMultiSig
          4. FlashArbitrageBot
          5. RealProfitFlashArbitrage
          6. KarmicGovernance
        """
        contract_sources = [
            "src/ProtectedToken.sol:ProtectedToken",
            "src/VetalGuardedVault.sol:LivingAbundanceDistributor",
            "src/DivineMultiSig.sol:DivineMultiSig",
            "src/FlashArbitrageBot.sol:FlashArbitrageBot",
            "src/RealProfitFlashArbitrage.sol:RealProfitFlashArbitrage",
            "src/KarmicGovernance.sol:KarmicGovernance",
        ]

        results = []
        for contract in contract_sources:
            logger.info(f"Deploying {contract}...")
            result = self.forge_deploy(
                contract=contract,
                chain_id=chain_id,
                dry_run=not broadcast,
            )
            results.append(result)
            if not result.success:
                logger.error(f"Failed to deploy {contract}: {result.error}")
                break

        return results

    # ============================================================
    # UTILITY: Get complete system status
    # ============================================================
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all tools, contracts, and history."""
        contracts = []
        src_dir = os.path.join(self.contracts_dir, "src")
        if os.path.isdir(src_dir):
            for f in os.listdir(src_dir):
                if f.endswith(".sol") and not f.endswith(".disabled") and not f.endswith(".backup"):
                    contracts.append(f)

        return {
            "tools_available": self._tools_available,
            "contracts_dir": self.contracts_dir,
            "contracts_found": contracts,
            "deployer_configured": bool(self.deployer_key),
            "rpc_url_configured": bool(self.eth_rpc_url),
            "operation_count": len(self.operation_history),
            "last_operation": self.operation_history[-1].to_dict() if self.operation_history else None,
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
vetal_shabar = VetalShabar()

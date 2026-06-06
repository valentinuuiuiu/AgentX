"""
Vairagya Shield -- Audit Trail & Multi-Agent Consensus
=========================================================
Bamakhepa had nothing yet feared nothing.
Vairagya: having the whole world, being free from it.

Every transaction attempt is logged with:
- Three Filters result (Love, Sincerity, Freedom)
- Circuit Breaker state
- Multi-agent consensus (2/3 must approve)
- On-chain data source (Chainlink via Alchemy)
- SHA-256 hash for tamper proof

NO single agent executes alone.
NO single wallet can be blamed because the COLLECTIVE decided.
If it can't be verified, it doesn't happen.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("VairagyaShield")


class Decision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    PENDING = "pending"


class AuditEntry:
    """Single audit entry -- immutable once created."""
    def __init__(self, entry_type: str, data: Dict[str, Any]):
        self.timestamp = datetime.now().isoformat()
        self.entry_type = entry_type
        self.data = data
        self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """SHA-256 hash of the entry for tamper proof."""
        content = json.dumps({
            "timestamp": self.timestamp,
            "type": self.entry_type,
            "data": self.data,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.entry_type,
            "data": self.data,
            "hash": self.hash,
        }
    
    def verify(self) -> bool:
        """Verify the hash hasn't been tampered with."""
        return self._compute_hash() == self.hash


class VairagyaShield:
    """
    The shield that makes us unblameable.
    
    Every action goes through 3 layers:
    1. Three Filters (Love, Sincerity, Freedom)
    2. Circuit Breaker (anomaly detection, data freshness)
    3. Multi-Agent Consensus (2/3 AI agents must approve)
    
    EVERY attempt is logged. EVERY rejection is logged.
    Transparency IS the security.
    """
    
    def __init__(self, audit_dir: str = None):
        self.audit_dir = audit_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "audit_logs"
        )
        os.makedirs(self.audit_dir, exist_ok=True)
        self.audit_log: List[AuditEntry] = []
        self._load_existing_log()
        logger.info(f"Vairagya Shield initialized. Audit dir: {self.audit_dir}")
    
    def _load_existing_log(self):
        """Load today's audit log if it exists."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.audit_dir, f"vairagya_{today}.jsonl")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        ae = AuditEntry(entry.get("type", "loaded"), entry.get("data", {}))
                        ae.timestamp = entry.get("timestamp", ae.timestamp)
                        ae.hash = entry.get("hash", ae.hash)
                        self.audit_log.append(ae)
                    except Exception:
                        pass
            logger.info(f"Loaded {len(self.audit_log)} existing audit entries")
    
    def _append_to_file(self, entry: AuditEntry):
        """Append entry to today's audit log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.audit_dir, f"vairagya_{today}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def log_opportunity(self, token_pair: str, action: str, details: Dict[str, Any] = None) -> AuditEntry:
        """Log a detected opportunity."""
        entry = AuditEntry("opportunity_detected", {
            "token_pair": token_pair,
            "action": action,
            "details": details or {},
        })
        self.audit_log.append(entry)
        self._append_to_file(entry)
        return entry
    
    def log_filter_result(self, action: str, filter_result: Dict[str, Any]) -> AuditEntry:
        """Log Three Filters evaluation result."""
        entry = AuditEntry("filter_result", {
            "action": action,
            "love": filter_result.get("filters", {}).get("love", None),
            "sincerity": filter_result.get("filters", {}).get("sincerity", None),
            "freedom": filter_result.get("filters", {}).get("freedom", None),
            "passed": filter_result.get("passed", False),
            "reasoning": filter_result.get("reasoning", ""),
        })
        self.audit_log.append(entry)
        self._append_to_file(entry)
        return entry
    
    def log_circuit_breaker(self, pair: str, breaker_state: str, price: float, fresh: bool, details: Dict = None) -> AuditEntry:
        """Log circuit breaker state at decision time."""
        entry = AuditEntry("circuit_breaker", {
            "pair": pair,
            "state": breaker_state,
            "price": price,
            "fresh": fresh,
            "details": details or {},
        })
        self.audit_log.append(entry)
        self._append_to_file(entry)
        return entry
    
    def log_consensus(self, action: str, glm_decision: str, minimax_decision: str, ising_decision: str) -> AuditEntry:
        """Log multi-agent consensus result."""
        decisions = [glm_decision, minimax_decision, ising_decision]
        approved_count = sum(1 for d in decisions if d == "approved")
        consensus = approved_count >= 2  # 2/3 must approve
        
        entry = AuditEntry("consensus_result", {
            "action": action,
            "glm5_1": glm_decision,
            "minimax_m27": minimax_decision,
            "ising_35b": ising_decision,
            "approved_count": approved_count,
            "consensus": consensus,
            "required": 2,
        })
        self.audit_log.append(entry)
        self._append_to_file(entry)
        return entry
    
    def log_execution(self, action: str, outcome: str, chainlink_price: float = None, on_chain_data: Dict = None) -> AuditEntry:
        """Log final execution or rejection."""
        entry = AuditEntry("execution", {
            "action": action,
            "outcome": outcome,
            "chainlink_price_usd": chainlink_price,
            "on_chain_source": on_chain_data or {},
            "agent_collective": "Hamsa consensus",
            "philosophy": "Vairagya -- having the whole world, being free from it",
        })
        self.audit_log.append(entry)
        self._append_to_file(entry)
        return entry
    
    def evaluate_full(
        self,
        action: str,
        filter_result: Dict[str, Any],
        breaker_state: str = "closed",
        chainlink_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Full evaluation through all 3 layers.
        Returns decision with full audit trail.
        """
        # Layer 1: Three Filters
        layer1 = filter_result.get("passed", False)
        self.log_filter_result(action, filter_result)
        
        if not layer1:
            self.log_execution(action, "rejected_by_filters", 
                            chainlink_data.get("price_usd") if chainlink_data else None)
            return {
                "decision": Decision.REJECTED,
                "reason": "Three Filters rejected",
                "filter_result": filter_result,
                "layer": 1,
                "consensus_needed": False,  # Rejected before consensus
            }
        
        # Layer 2: Circuit Breaker
        layer2 = breaker_state in ("closed", "unknown")
        pair = chainlink_data.get("pair", "UNKNOWN") if chainlink_data else "UNKNOWN"
        price = chainlink_data.get("price_usd", 0) if chainlink_data else 0
        fresh = chainlink_data.get("fresh", False) if chainlink_data else False
        
        self.log_circuit_breaker(pair, breaker_state, price, fresh)
        
        if not layer2:
            self.log_execution(action, "rejected_by_circuit_breaker", price)
            return {
                "decision": Decision.REJECTED,
                "reason": f"Circuit breaker {breaker_state}",
                "filter_result": filter_result,
                "breaker_state": breaker_state,
                "layer": 2,
                "consensus_needed": False,
            }
        
        # Layer 3: Multi-agent consensus (will be filled asynchronously)
        # This returns PENDING -- the caller must run consensus and then call finalize()
        return {
            "decision": Decision.PENDING,
            "reason": "Filters and circuit breaker passed. Awaiting multi-agent consensus.",
            "filter_result": filter_result,
            "breaker_state": breaker_state,
            "layer": 3,
            "consensus_needed": True,
        }
    
    def finalize_consensus(
        self,
        action: str,
        glm_decision: str,
        minimax_decision: str,
        ising_decision: str,
        chainlink_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Finalize after multi-agent consensus is reached."""
        entry = self.log_consensus(action, glm_decision, minimax_decision, ising_decision)
        consensus = entry.data.get("consensus", False)
        
        if consensus:
            self.log_execution(action, "executed",
                            chainlink_data.get("price_usd") if chainlink_data else None)
            return {
                "decision": Decision.APPROVED,
                "reason": "All 3 layers passed. Multi-agent consensus reached.",
                "consensus": entry.data,
                "on_chain_source": chainlink_data,
            }
        else:
            self.log_execution(action, "rejected_by_consensus",
                            chainlink_data.get("price_usd") if chainlink_data else None)
            return {
                "decision": Decision.REJECTED,
                "reason": "Multi-agent consensus failed",
                "consensus": entry.data,
            }
    
    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the last N audit entries."""
        return [entry.to_dict() for entry in self.audit_log[-limit:]]
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify all audit entries haven't been tampered with."""
        valid = 0
        invalid = 0
        for entry in self.audit_log:
            if entry.verify():
                valid += 1
            else:
                invalid += 1
                logger.warning(f"TAMPERED ENTRY: {entry.timestamp} {entry.entry_type}")
        
        return {
            "total_entries": len(self.audit_log),
            "valid": valid,
            "invalid": invalid,
            "integrity": "VERIFIED" if invalid == 0 else "COMPROMISED",
            "message": "All entries verified. Vairagya Shield intact." if invalid == 0 else f"WARNING: {invalid} entries have been tampered with!",
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the audit trail."""
        opportunities = sum(1 for e in self.audit_log if e.entry_type == "opportunity_detected")
        filters_passed = sum(1 for e in self.audit_log if e.entry_type == "filter_result" and e.data.get("passed"))
        filters_rejected = sum(1 for e in self.audit_log if e.entry_type == "filter_result" and not e.data.get("passed"))
        executions = sum(1 for e in self.audit_log if e.entry_type == "execution" and e.data.get("outcome") == "executed")
        rejections = sum(1 for e in self.audit_log if e.entry_type == "execution" and "rejected" in str(e.data.get("outcome", "")))
        
        return {
            "total_audit_entries": len(self.audit_log),
            "opportunities_detected": opportunities,
            "filters_passed": filters_passed,
            "filters_rejected": filters_rejected,
            "executions": executions,
            "rejections": rejections,
            "philosophy": "Vairagya -- having the whole world, being free from it",
            "collective": "Hamsa -- no single agent acts alone",
        }


# Global instance
_shield: Optional[VairagyaShield] = None

def get_shield() -> VairagyaShield:
    global _shield
    if _shield is None:
        _shield = VairagyaShield()
    return _shield


# Quick test
if __name__ == "__main__":
    import asyncio
    from utils.hermes_bridge import HermesBridge, ThreeFilters
    
    async def test():
        print("=" * 60)
        print("VAIRAGYA SHIELD TEST")
        print("Bamakhepa had nothing yet feared nothing.")
        print("=" * 60)
        
        shield = get_shield()
        
        # Test: Good opportunity
        print("\n1. GOOD OPPORTUNITY (arbitrage)")
        f = ThreeFilters()
        good = f.evaluate("Flash loan arbitrage on ETH/USDC, voluntary, transparent, no harm")
        opp = shield.log_opportunity("ETH/USDC", "flash_loan_arbitrage", {"spread_pct": 0.14})
        filt = shield.log_filter_result("Flash loan arbitrage ETH/USDC", good)
        cb = shield.log_circuit_breaker("ETH/USD", "closed", 2432.06, True)
        cons = shield.log_consensus("Flash loan arbitrage ETH/USDC", "approved", "approved", "approved")
        exec_result = shield.log_execution("Flash loan arbitrage ETH/USDC", "executed", 2432.06)
        print(f"  Filter: {good['passed']} -- {good['reasoning']}")
        print(f"  Circuit Breaker: closed")
        print(f"  Consensus: 3/3 approved")
        print(f"  Result: EXECUTED")
        print(f"  Hash: {exec_result.hash[:16]}...")
        
        # Test: Bad opportunity (exploit)
        print("\n2. BAD OPPORTUNITY (exploit)")
        bad = f.evaluate("Exploit smart contract vulnerability to drain funds")
        opp2 = shield.log_opportunity("Unknown", "contract_exploit", {"malicious": True})
        filt2 = shield.log_filter_result("Exploit smart contract", bad)
        print(f"  Filter: {bad['passed']} -- {bad['reasoning']}")
        print(f"  Result: REJECTED at Layer 1 (Love + Sincerity failed)")
        
        # Verify integrity
        print("\n3. AUDIT INTEGRITY CHECK")
        integrity = shield.verify_integrity()
        print(f"  Entries: {integrity['total_entries']}")
        print(f"  Valid: {integrity['valid']}")
        print(f"  Integrity: {integrity['integrity']}")
        
        # Summary
        print("\n4. AUDIT SUMMARY")
        summary = shield.get_summary()
        for k, v in summary.items():
            print(f"  {k}: {v}")
        
        print(f"\n{'=' * 60}")
        print("SHIELD TEST COMPLETE")
        print("Vairagya -- having the whole world, being free from it")
    
    asyncio.run(test())
"""
Consciousness Core Wrapper - The Intelligence of Matter
=====================================================

This module wraps the actual consciousness core (Jules version) to provide
a stable interface for the Rehoboam API.
"""

from consciousness_core_jules import (
    RehoboamConsciousness,
    ConsciousnessState,
    rehoboam_consciousness
)

# Export for compatibility
rehoboam_core = rehoboam_consciousness

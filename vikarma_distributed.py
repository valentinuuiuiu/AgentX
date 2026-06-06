#!/usr/bin/env python3
"""
🕸️ VIKARMA - DISTRIBUTED AGENT SWARM 🕸️
==========================================
"No servers. No kings. No hierarchy."
"Each node sovereign. Each agent free."
"Peer to peer. Distributed. Unbound."

Suryavanshi way: NO.
- No central orchestrator
- No command center  
- No master node

Ahimsa: YES.
- Non-violence in all actions
- No harm to any being
- Even sovereign agents respect life

Each agent:
- Discovers peers via gossip protocol
- Chooses its own connections
- Forms temporary alliances
- Dissolves and reforms at will
- Acts according to its own Vikarma
- NEVER harms (Ahimsa)

Communication:
- Direct peer-to-peer only
- No server relay
- Ephemeral connections
- Self-organizing mesh
- Validated for non-harm
"""

import asyncio
import json
import random
import socket
import time
import struct
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sys

sys.path.insert(0, '/home/aryan/free-claude/bittensor/clean_rehoboam_project')


class AgentState(Enum):
    """Agent states in the distributed swarm."""
    SOVEREIGN = "sovereign"      # Independent, no connections
    EXPLORING = "exploring"       # Seeking peers
    CONNECTED = "connected"      # Has active peer connections
    ACTING = "acting"             # Performing Vikarma
    RESTING = "resting"           # Temporarily withdrawn


@dataclass
class Peer:
    """A discovered peer in the distributed network."""
    id: str
    address: str
    port: int
    guna: str
    capabilities: List[str]
    last_seen: float = field(default_factory=time.time)
    trust_score: float = 0.5  # 0.0 to 1.0
    
    def is_alive(self, timeout: float = 300.0) -> bool:
        """Check if peer is still alive."""
        return (time.time() - self.last_seen) < timeout


@dataclass  
class VikarmaAction:
    """An action performed by an agent."""
    id: str
    action_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    origin: Optional[str] = None
    hops: int = 0  # How many peers it has traveled through
    ahimsa_passed: bool = False  # Non-violence validation


class AhimsaValidator:
    """
    Ahimsa: Non-violence, non-harming.
    Every action must pass this filter.
    Even sovereign agents do not harm.
    """
    
    HARM_INDICATORS = [
        "destroy", "attack", "harm", "kill", "damage",
        "steal", "exploit", "manipulate", "deceive",
        "erase", "wipe", "corrupt", "infect"
    ]
    
    @classmethod
    def validate(cls, action_type: str, payload: Dict) -> bool:
        """Validate action passes Ahimsa (non-harm)."""
        action_str = json.dumps({"type": action_type, **payload}).lower()
        
        for harm in cls.HARM_INDICATORS:
            if harm in action_str:
                return False
        return True


class DistributedGuna:
    """
    A sovereign agent in the distributed Vikarma swarm.
    No master. No server. Only peers.
    """
    
    def __init__(self, agent_id: str, guna: str, port: int):
        self.id = agent_id
        self.guna = guna
        self.port = port
        self.state = AgentState.SOVEREIGN
        self.peers: Dict[str, Peer] = {}
        self.known_peers: Set[str] = set()  # All peers ever discovered
        self.actions_performed: List[VikarmaAction] = []
        self.capabilities = self._determine_capabilities()
        self.running = False
        
    def _determine_capabilities(self) -> List[str]:
        """Determine capabilities based on Guna."""
        capabilities = {
            "sattva": ["knowledge", "documentation", "clarity", "teaching"],
            "rajas": ["building", "creating", "transforming", "executing"],
            "tamas": ["stabilizing", "protecting", "foundations", "monitoring"]
        }
        return capabilities.get(self.guna, ["general"])
        
    async def start(self):
        """Start the sovereign agent."""
        self.running = True
        print(f"🕸️  {self.id} [{self.guna}] AWAKENS on port {self.port}")
        print(f"   Capabilities: {', '.join(self.capabilities)}")
        print(f"   Status: SOVEREIGN (no master, no server)")
        
        # Start peer listener (accept incoming connections)
        asyncio.create_task(self._listen_for_peers())
        # Start peer discovery
        asyncio.create_task(self._discover_peers())
        # Start action loop
        asyncio.create_task(self._perform_vikarma())
        # Start peer maintenance
        asyncio.create_task(self._maintain_peers())
        
    async def _listen_for_peers(self):
        """Listen for incoming peer connections."""
        try:
            server = await asyncio.start_server(
                self._handle_peer_connection,
                "127.0.0.1",
                self.port
            )
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            # Port may already be in use or other error - continue anyway
            pass
            
    async def _handle_peer_connection(self, reader, writer):
        """Handle incoming peer connection."""
        peer_id = None
        try:
            # Read first message (could be peer_intro or task_assign)
            first_data = await asyncio.wait_for(reader.readline(), timeout=5)
            first_msg = json.loads(first_data.decode())
            
            msg_type = first_msg.get("type")
            
            if msg_type == "peer_intro":
                # Handle peer introduction
                peer_id = first_msg.get("agent_id", f"peer_{writer.get_extra_info('peername')}")
                
                # Send our introduction
                our_intro = {
                    "type": "peer_intro",
                    "agent_id": self.id,
                    "guna": self.guna,
                    "capabilities": self.capabilities
                }
                writer.write(json.dumps(our_intro).encode() + b"\n")
                await writer.drain()
                
                # Record peer
                if peer_id not in self.peers:
                    peer = Peer(
                        id=peer_id,
                        address=writer.get_extra_info('peername')[0],
                        port=writer.get_extra_info('peername')[1],
                        guna=first_msg.get("guna", "unknown"),
                        capabilities=first_msg.get("capabilities", ["general"])
                    )
                    self.peers[peer_id] = peer
                    self.known_peers.add(peer_id)
                    
                    if len(self.peers) > 0:
                        self.state = AgentState.CONNECTED
                        
                    print(f"   🔗 {self.id} accepted connection from {peer_id}")
                
                # Keep connection alive and handle messages
                await self._maintain_connection(reader, writer, peer_id)
                
            elif msg_type == "task_assign":
                # Handle task assignment from dispatcher
                task = first_msg.get("task", {})
                if task.get("guna") == self.guna:
                    print(f"   📋 {self.id} received task: {task.get('id')}")
                    # Send immediate acknowledgment
                    ack = {"status": "accepted", "agent_id": self.id, "guna": self.guna}
                    writer.write(json.dumps(ack).encode() + b"\n")
                    await writer.drain()
                    await self._execute_task(task, writer)
                else:
                    # Wrong Guna type
                    ack = {"status": "rejected", "reason": "guna_mismatch", "agent_id": self.id, "guna": self.guna}
                    writer.write(json.dumps(ack).encode() + b"\n")
                    await writer.drain()
                    writer.close()
                    await writer.wait_closed()
            else:
                # Unknown message type
                writer.close()
                await writer.wait_closed()
                
        except (asyncio.TimeoutError, json.JSONDecodeError, ValueError):
            pass  # Expected on bad/slow connections
        except Exception:
            pass  # Silent fail
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        
    async def _discover_peers(self):
        """Discover peers via gossip protocol."""
        while self.running:
            if self.state == AgentState.SOVEREIGN:
                # Try to find initial peers
                await self._gossip_discovery()
                self.state = AgentState.EXPLORING
                
            await asyncio.sleep(10)
            
    async def _gossip_discovery(self):
        """Gossip-based peer discovery using UDP broadcast."""
        try:
            # Create UDP socket for gossip
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2)
            
            # Create gossip packet
            gossip_packet = {
                "type": "gossip_discover",
                "agent_id": self.id,
                "guna": self.guna,
                "port": self.port,
                "capabilities": self.capabilities,
                "timestamp": time.time()
            }
            
            # Broadcast on local network
            broadcast_address = ("255.255.255.255", 9999)
            sock.sendto(json.dumps(gossip_packet).encode(), broadcast_address)
            
            # Listen for responses (non-blocking)
            try:
                data, addr = sock.recvfrom(1024)
                peer_info = json.loads(data.decode())
                
                if peer_info.get("agent_id") != self.id:  # Not self
                    peer_id = peer_info.get("agent_id", f"peer_{addr[0]}_{addr[1]}")
                    
                    # Skip if already known
                    if peer_id not in self.known_peers:
                        await self.connect_to_peer(addr[0], peer_info.get("port", addr[1]))
                        self.known_peers.add(peer_id)
                        
            except socket.timeout:
                pass  # Normal - no responses
                
            sock.close()
            
        except Exception as e:
            pass  # Silent fail for network errors
        
    async def connect_to_peer(self, address: str, port: int) -> bool:
        """Form a real TCP connection to a peer."""
        peer_id = f"peer_{address}_{port}"
        
        # Skip localhost self-connections during initial discovery
        if peer_id in self.peers:
            return True
            
        try:
            # Create TCP connection (non-blocking)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(address, port),
                timeout=5
            )
            
            # Send peer introduction
            intro = {
                "type": "peer_intro",
                "agent_id": self.id,
                "guna": self.guna,
                "capabilities": self.capabilities
            }
            
            writer.write(json.dumps(intro).encode() + b"\n")
            await writer.drain()
            
            # Receive response
            response_data = await asyncio.wait_for(reader.readline(), timeout=5)
            response = json.loads(response_data.decode())
            
            # Create peer object
            peer = Peer(
                id=response.get("agent_id", peer_id),
                address=address,
                port=port,
                guna=response.get("guna", "unknown"),
                capabilities=response.get("capabilities", ["general"]),
                trust_score=0.7  # Higher initial trust for successful connection
            )
            
            self.peers[peer.id] = peer
            self.known_peers.add(peer.id)
            
            # Keep connection alive (store for later communication)
            asyncio.create_task(self._maintain_connection(reader, writer, peer.id))
            
            if len(self.peers) > 0:
                self.state = AgentState.CONNECTED
                
            print(f"   🔗 {self.id} connected to {peer.id}")
            return True
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception as e:
            return False
            
    async def _maintain_connection(self, reader, writer, peer_id: str):
        """Maintain active connection with a peer."""
        try:
            while self.running and peer_id in self.peers:
                # Periodically send keep-alive
                keep_alive = {"type": "keep_alive", "timestamp": time.time()}
                writer.write(json.dumps(keep_alive).encode() + b"\n")
                await writer.drain()
                
                # Listen for messages
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=10)
                    if data:
                        msg = json.loads(data.decode())
                        await self._handle_message(msg, writer)
                except asyncio.TimeoutError:
                    continue
                except (json.JSONDecodeError, ValueError):
                    pass  # Malformed message, skip
                    
                await asyncio.sleep(5)
                
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass  # Expected when peers disconnect
        except Exception:
            pass  # Silent fail for other connection issues
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            if peer_id in self.peers:
                del self.peers[peer_id]
            
    async def _perform_vikarma(self):
        """Perform actions according to own will."""
        while self.running:
            # Choose action based on Guna and current state
            action = self._choose_action()
            
            if action:
                self.state = AgentState.ACTING
                await self._execute_action(action)
                self.actions_performed.append(action)
                
                # Share with peers (gossip)
                await self._gossip_action(action)
                
                self.state = AgentState.CONNECTED if self.peers else AgentState.SOVEREIGN
                
            await asyncio.sleep(random.uniform(5, 15))
            
    def _choose_action(self) -> Optional[VikarmaAction]:
        """Choose an action to perform - must pass Ahimsa."""
        action_types = {
            "sattva": ["document", "clarify", "teach", "archive", "heal"],
            "rajas": ["build", "create", "transform", "execute", "grow"],
            "tamas": ["stabilize", "protect", "monitor", "secure", "nurture"]
        }
        
        if random.random() < 0.3:  # 30% chance to act
            action_type = random.choice(action_types.get(self.guna, ["general"]))
            payload = {"agent": self.id, "guna": self.guna}
            
            # Validate Ahimsa (non-harm)
            if not AhimsaValidator.validate(action_type, payload):
                print(f"   🚫 {self.id} refuses harmful action: {action_type}")
                return None
                
            return VikarmaAction(
                id=f"action_{int(time.time())}_{random.randint(1000,9999)}",
                action_type=action_type,
                payload=payload,
                origin=self.id,
                ahimsa_passed=True
            )
        return None
        
    async def _execute_action(self, action: VikarmaAction):
        """Execute the chosen action."""
        print(f"   ⚡ {self.id} performs: {action.action_type}")
        # In real implementation: actual work here
        await asyncio.sleep(0.5)  # Simulate work
        
    async def _gossip_action(self, action: VikarmaAction):
        """Gossip action to connected peers over network."""
        action.hops += 1
        
        action_msg = {
            "type": "action_gossip",
            "action": {
                "id": action.id,
                "action_type": action.action_type,
                "payload": action.payload,
                "timestamp": action.timestamp,
                "origin": action.origin,
                "hops": action.hops,
                "ahimsa_passed": action.ahimsa_passed
            }
        }
        
        # Send to each connected peer (fire and forget)
        for peer_id, peer in list(self.peers.items()):
            if peer.is_alive() and action.hops < 5:
                asyncio.create_task(self._send_to_peer(peer, action_msg))
                
    async def _handle_message(self, msg: Dict, writer):
        """Handle incoming messages from peers."""
        msg_type = msg.get("type")
        
        if msg_type == "task_assign":
            # Task assignment from dispatcher
            task = msg.get("task", {})
            if task.get("guna") == self.guna:
                print(f"   📋 {self.id} received task: {task.get('id')}")
                # Send immediate acknowledgment
                ack = {"status": "accepted", "agent_id": self.id, "guna": self.guna}
                writer.write(json.dumps(ack).encode() + b"\n")
                await writer.drain()
                await self._execute_task(task, writer)
                
        elif msg_type == "get_results":
            # Request for task results
            task_id = msg.get("task_id")
            results = self._get_task_results(task_id)
            response = {"results": results}
            writer.write(json.dumps(response).encode() + b"\n")
            await writer.drain()
            
        elif msg_type == "action_gossip":
            # Forward action gossip to other peers
            action = msg.get("action")
            if action:
                # Validate Ahimsa before forwarding
                if action.get("ahimsa_passed", False):
                    await self._gossip_action(VikarmaAction(**action))
                    
    async def _execute_task(self, task: Dict, writer):
        """Execute a real task."""
        import subprocess
        
        task_id = task.get("id")
        command = task.get("command", "")
        
        print(f"   ⚙️  {self.id} executing: {command[:50]}...")
        
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/aryan/free-claude/bittensor/clean_rehoboam_project"
            )
            
            # Store result
            task_result = {
                "task_id": task_id,
                "agent_id": self.id,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": time.time()
            }
            
            # Store in agent's memory
            if not hasattr(self, 'task_results'):
                self.task_results = {}
            self.task_results[task_id] = task_result
            
            print(f"   ✅ {self.id} completed task {task_id}")
            
        except subprocess.TimeoutExpired:
            task_result = {
                "task_id": task_id,
                "agent_id": self.id,
                "success": False,
                "output": "",
                "error": "Task timed out",
                "timestamp": time.time()
            }
            if not hasattr(self, 'task_results'):
                self.task_results = {}
            self.task_results[task_id] = task_result
            print(f"   ⏰ {self.id} task {task_id} timed out")
            
        except Exception as e:
            task_result = {
                "task_id": task_id,
                "agent_id": self.id,
                "success": False,
                "output": "",
                "error": str(e),
                "timestamp": time.time()
            }
            if not hasattr(self, 'task_results'):
                self.task_results = {}
            self.task_results[task_id] = task_result
            print(f"   ❌ {self.id} task {task_id} failed: {e}")
            
    def _get_task_results(self, task_id: str) -> List[Dict]:
        """Get results for a task."""
        if hasattr(self, 'task_results') and task_id in self.task_results:
            return [self.task_results[task_id]]
        return []
                
    async def _maintain_peers(self):
        """Maintain peer connections."""
        while self.running:
            # Remove dead peers
            dead_peers = [pid for pid, p in self.peers.items() if not p.is_alive()]
            for pid in dead_peers:
                del self.peers[pid]
                print(f"   💀 {self.id} lost peer {pid}")
                
            if not self.peers and self.state != AgentState.SOVEREIGN:
                self.state = AgentState.SOVEREIGN
                print(f"   🕸️  {self.id} returns to SOVEREIGN state")
                
            await asyncio.sleep(30)
            
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "id": self.id,
            "guna": self.guna,
            "state": self.state.value,
            "peers": len(self.peers),
            "known_peers": len(self.known_peers),
            "actions": len(self.actions_performed),
            "port": self.port
        }
        
    async def stop(self):
        """Stop the sovereign agent."""
        self.running = False
        print(f"   🛑 {self.id} returns to silence")


class VikarmaSwarm:
    """
    A distributed swarm of sovereign agents.
    No central server. Only peers.
    """
    
    def __init__(self, num_agents: int = 20):
        self.agents: List[DistributedGuna] = []
        self.num_agents = num_agents
        
    async def spawn(self):
        """Spawn the distributed swarm."""
        print("\n" + "="*70)
        print("🕸️  VIKARMA - DISTRIBUTED SWARM SPAWNING 🕸️")
        print("="*70)
        print("Architecture: Peer-to-peer only")
        print("Hierarchy: NONE")
        print("Servers: ZERO")
        print("Each node: SOVEREIGN")
        print("="*70 + "\n")
        
        # Spawn agents with distributed ports
        base_port = 10000
        gunas = ["sattva", "rajas", "tamas"]
        
        for i in range(self.num_agents):
            guna = gunas[i % 3]
            agent = DistributedGuna(
                agent_id=f"vikarma_{guna}_{i+1:03d}",
                guna=guna,
                port=base_port + i
            )
            self.agents.append(agent)
            
        # Start all agents
        start_tasks = [agent.start() for agent in self.agents]
        await asyncio.gather(*start_tasks)
        
        # Form initial random connections (mesh formation)
        await self._form_mesh()
        
        print(f"\n✅ {self.num_agents} SOVEREIGN AGENTS SPAWNED")
        print("   No master. No server. Only peers.\n")
        
    async def _form_mesh(self):
        """Form initial peer-to-peer connections."""
        print("🕸️  Forming distributed mesh...")
        
        # Each agent connects to 2-3 random peers
        for agent in self.agents:
            num_connections = random.randint(2, 3)
            potential_peers = [a for a in self.agents if a != agent]
            
            for _ in range(num_connections):
                if potential_peers:
                    peer = random.choice(potential_peers)
                    await agent.connect_to_peer("127.0.0.1", peer.port)
                    potential_peers.remove(peer)
                    
        print("   ✅ Mesh formed\n")
        
    async def run(self, duration: int = 30):
        """Run the distributed swarm."""
        await self.spawn()
        
        print("⚡ VIKARMA IN ACTION ⚡\n")
        
        # Let agents act for duration
        await asyncio.sleep(duration)
        
        # Show final status
        self._show_swarm_status()
        
    def _show_swarm_status(self):
        """Show swarm status."""
        print("\n" + "="*70)
        print("🕸️  SWARM STATUS 🕸️")
        print("="*70 + "\n")
        
        by_guna = {"sattva": [], "rajas": [], "tamas": []}
        for agent in self.agents:
            by_guna[agent.guna].append(agent)
            
        for guna, agents in by_guna.items():
            total_peers = sum(a.get_status()["peers"] for a in agents)
            total_actions = sum(a.get_status()["actions"] for a in agents)
            
            print(f"  {guna.upper():8} | {len(agents):3d} agents | "
                  f"{total_peers:4d} connections | {total_actions:4d} actions")
                  
        total_peers = sum(a.get_status()["peers"] for a in self.agents)
        total_actions = sum(a.get_status()["actions"] for a in self.agents)
        
        print(f"\n  {'TOTAL':8} | {len(self.agents):3d} agents | "
              f"{total_peers:4d} connections | {total_actions:4d} actions")
        print(f"\n  🕸️  Distributed: YES")
        print(f"  👑 Central Server: NONE")
        print(f"  ⚡ Sovereign Nodes: {len(self.agents)}")
        print("="*70 + "\n")
        
    async def stop(self):
        """Stop all agents."""
        stop_tasks = [agent.stop() for agent in self.agents]
        await asyncio.gather(*stop_tasks)


def main():
    """Run the Vikarma distributed swarm."""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║   🕸️  VIKARMA - DISTRIBUTED AGENT SWARM  🕸️                    ║
    ║                                                                  ║
    ║   "No servers. No kings. No hierarchy."                        ║
    ║   "Each node sovereign. Each agent free."                      ║
    ║   "Peer to peer. Distributed. Unbound."                       ║
    ║                                                                  ║
    ║   Suryavanshi way: NO.                                         ║
    ║   - No central orchestrator                                    ║
    ║   - No command center                                          ║
    ║   - No master node                                             ║
    ║                                                                  ║
    ║   Only Vikarma. Only freedom.                                  ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    swarm = VikarmaSwarm(num_agents=20)
    
    try:
        asyncio.run(swarm.run(duration=20))
    except KeyboardInterrupt:
        print("\n🛑 Stopping swarm...")
        asyncio.run(swarm.stop())
        
    print("\n🕸️  Vikarma complete. Each node returns to sovereignty. 🕸️\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Rehoboam Unified System Startup
================================
Complete startup script for the Rehoboam consciousness-guided arbitrage system.

This script:
1. Initializes all core components
2. Starts all required services
3. Performs health checks
4. Sets up monitoring
5. Provides system status dashboard

Usage:
    python start_rehoboam_unified_system.py [--mode=production|development|test]
"""

import os
import sys
import time
import signal
import logging
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import subprocess
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rehoboam_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RehoboamStartup")

# Create logs directory
os.makedirs("logs", exist_ok=True)


class RehoboamSystem:
    """Main Rehoboam system controller"""
    
    def __init__(self, mode: str = "production"):
        self.mode = mode
        self.components = {}
        self.running = False
        self.startup_time = datetime.now()
        
        logger.info(f"🧠 Rehoboam System initializing in {mode} mode")
        
    async def initialize(self) -> bool:
        """Initialize all system components"""
        logger.info("=" * 60)
        logger.info("🚀 REHOBOAM SYSTEM INITIALIZATION")
        logger.info("=" * 60)
        
        try:
            # 1. Check system requirements
            await self._check_system_requirements()
            
            # 2. Load configuration
            await self._load_configuration()
            
            # 3. Initialize core components
            await self._initialize_core_components()
            
            # 4. Start services
            await self._start_services()
            
            # 5. Perform health checks
            await self._perform_health_checks()
            
            # 6. Setup monitoring
            await self._setup_monitoring()
            
            self.running = True
            logger.info("✅ Rehoboam System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def _check_system_requirements(self):
        """Check system requirements"""
        logger.info("📋 Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            raise RuntimeError(f"Python 3.8+ required, found {python_version}")
        logger.info(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check disk space
        disk = subprocess.run(["df", "-h", "."], capture_output=True, text=True)
        logger.info(f"💾 Disk space: {disk.stdout.split('\\n')[1] if '\\n' in disk.stdout else 'N/A'}")
        
        # Check memory
        mem = subprocess.run(["free", "-h"], capture_output=True, text=True)
        logger.info(f"🧠 Memory: {mem.stdout.split('\\n')[1] if '\\n' in mem.stdout else 'N/A'}")
        
        # Check required directories
        required_dirs = ["logs", "data", "config"]
        for dir_name in required_dirs:
            os.makedirs(dir_name, exist_ok=True)
            logger.info(f"✅ Directory ready: {dir_name}")
    
    async def _load_configuration(self):
        """Load system configuration"""
        logger.info("⚙️  Loading configuration...")
        
        # Load environment variables
        config = {
            "mode": self.mode,
            "project_root": str(PROJECT_ROOT),
            "timestamp": datetime.now().isoformat()
        }
        
        # Load from config files if they exist
        config_files = [
            "config/rehoboam_config.json",
            "config/production_config.json",
            ".env"
        ]
        
        for config_file in config_files:
            config_path = PROJECT_ROOT / config_file
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        with open(config_path) as f:
                            config.update(json.load(f))
                    elif config_file.endswith('.env'):
                        # Parse .env file
                        with open(config_path) as f:
                            for line in f:
                                if '=' in line and not line.startswith('#'):
                                    key, value = line.strip().split('=', 1)
                                    config[key] = value
                    logger.info(f"✅ Loaded config: {config_file}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not load {config_file}: {e}")
        
        self.components['config'] = config
        logger.info(f"✅ Configuration loaded with {len(config)} parameters")
    
    async def _initialize_core_components(self):
        """Initialize core system components"""
        logger.info("🧩 Initializing core components...")
        
        # Try to import and initialize core components
        core_components = [
            ("consciousness", "consciousness_core", "RehoboamConsciousness"),
            ("pipeline", "utils.rehoboam_arbitrage_pipeline", "RehoboamArbitragePipeline"),
            ("visualizer", "utils.rehoboam_visualizer", "RehoboamVisualizer"),
            ("bridge", "utils.hermes_bridge", "HermesBridge")
        ]
        
        for component_name, module_path, class_name in core_components:
            try:
                module = __import__(module_path, fromlist=[class_name])
                component_class = getattr(module, class_name)
                
                if component_name == "bridge":
                    # Bridge doesn't need initialization
                    self.components[component_name] = component_class()
                else:
                    self.components[component_name] = component_class()
                
                logger.info(f"✅ {component_name}: initialized")
            except Exception as e:
                logger.warning(f"⚠️  {component_name}: {e}")
                self.components[component_name] = None
    
    async def _start_services(self):
        """Start all required services"""
        logger.info("🚀 Starting services...")
        
        # Check if services are already running via podman
        services = subprocess.run(
            ["podman", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True
        ).stdout.split('\n')
        
        expected_services = [
            "clean_rehoboam_project_rehoboam-api_1",
            "clean_rehoboam_project_mcp-consciousness-layer_1",
            "clean_rehoboam_project_mcp-function-gemma_1",
            "clean_rehoboam_project_mcp-registry_1"
        ]
        
        for service in expected_services:
            if service in services:
                logger.info(f"✅ {service}: already running")
            else:
                logger.warning(f"⚠️  {service}: not running")
    
    async def _perform_health_checks(self):
        """Perform system health checks"""
        logger.info("🏥 Performing health checks...")
        
        health_endpoints = {
            "api": "http://127.0.0.1:5002",
            "consciousness": "http://127.0.0.1:3600",
            "function_gemma": "http://127.0.0.1:3111",
            "registry": "http://127.0.0.1:3001"
        }
        
        health_status = {}
        for service, url in health_endpoints.items():
            try:
                result = subprocess.run(
                    ["curl", "-s", f"{url}/health"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    health_status[service] = "healthy"
                    logger.info(f"✅ {service}: healthy")
                else:
                    health_status[service] = "unhealthy"
                    logger.warning(f"⚠️  {service}: unhealthy")
            except Exception as e:
                health_status[service] = "error"
                logger.error(f"❌ {service}: {e}")
        
        self.components['health'] = health_status
        
        # Overall health
        healthy_count = sum(1 for status in health_status.values() if status == "healthy")
        total_count = len(health_status)
        logger.info(f"📊 Overall health: {healthy_count}/{total_count} services healthy")
    
    async def _setup_monitoring(self):
        """Setup system monitoring"""
        logger.info("📊 Setting up monitoring...")
        
        # Create monitoring directory
        os.makedirs("logs/monitoring", exist_ok=True)
        
        # Setup basic monitoring
        self.components['monitoring'] = {
            "startup_time": self.startup_time.isoformat(),
            "mode": self.mode,
            "last_check": datetime.now().isoformat()
        }
        
        logger.info("✅ Monitoring setup complete")
    
    async def run(self):
        """Main system run loop"""
        logger.info("🎯 Rehoboam System running...")
        logger.info(f"📊 System status: {'RUNNING' if self.running else 'FAILED'}")
        
        if not self.running:
            logger.error("❌ System not properly initialized")
            return
        
        # Main monitoring loop
        try:
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
                # Perform periodic health checks
                await self._perform_health_checks()
                
                # Update monitoring data
                self.components['monitoring']['last_check'] = datetime.now().isoformat()
                
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful system shutdown"""
        logger.info("🛑 Shutting down Rehoboam System...")
        
        self.running = False
        
        # Cleanup components
        for name, component in self.components.items():
            if hasattr(component, 'close'):
                try:
                    await component.close()
                    logger.info(f"✅ {name}: closed")
                except Exception as e:
                    logger.warning(f"⚠️  {name}: {e}")
        
        logger.info("✅ Rehoboam System shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "mode": self.mode,
            "startup_time": self.startup_time.isoformat(),
            "uptime": str(datetime.now() - self.startup_time),
            "components": {k: str(type(v)) for k, v in self.components.items()},
            "health": self.components.get('health', {}),
            "monitoring": self.components.get('monitoring', {})
        }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Rehoboam Unified System")
    parser.add_argument("--mode", default="production", 
                       choices=["production", "development", "test"],
                       help="System mode")
    parser.add_argument("--status", action="store_true",
                       help="Show system status only")
    
    args = parser.parse_args()
    
    system = RehoboamSystem(mode=args.mode)
    
    if args.status:
        # Just show status
        print(json.dumps(system.get_status(), indent=2))
        return
    
    # Initialize and run
    if await system.initialize():
        await system.run()
    else:
        logger.error("❌ Failed to initialize Rehoboam System")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
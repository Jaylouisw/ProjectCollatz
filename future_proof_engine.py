#!/usr/bin/env python3
"""
FUTURE-PROOFED DISTRIBUTED COLLATZ ENGINE
==========================================

This is the main integration that brings together all future-proofing
abstraction layers for maximum compatibility and adaptability.

Features:
- Protocol-agnostic networking (IPFS, libp2p, future protocols)
- Hardware-agnostic compute (CPU, CUDA, ROCm, future accelerators)  
- Version-aware configuration with migration
- Graceful degradation and fallback mechanisms
- Cross-platform compatibility (Windows, Linux, macOS)
- Flexible dependency management

Usage:
    python future_proof_engine.py [--config config.json] [--network auto] [--compute auto]
"""

import sys
import os
import json
import time
import logging
import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Future-proofed imports with fallbacks
try:
    from network_transport import create_network_transport, NetworkTransportFactory
    NETWORK_AVAILABLE = True
except ImportError:
    print("Warning: Network transport abstraction not available, using fallback")
    NETWORK_AVAILABLE = False

try:
    from compute_engine import create_compute_engine, ComputeEngineFactory
    COMPUTE_AVAILABLE = True
except ImportError:
    print("Warning: Compute engine abstraction not available, using fallback")
    COMPUTE_AVAILABLE = False

try:
    from config_manager import ConfigurationManager, CollatzConfig
    CONFIG_AVAILABLE = True
except ImportError:
    print("Warning: Configuration manager not available, using fallback")
    CONFIG_AVAILABLE = False

# Standard library imports (always available)
import threading
import queue
import hashlib
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass 
class FallbackConfig:
    """Fallback configuration when config_manager is not available."""
    network_transport: str = "auto"
    compute_engine: str = "auto"
    max_range: int = 1000000
    chunk_size: int = 10000
    verification_required: bool = True
    ipfs_endpoint: str = "/ip4/127.0.0.1/tcp/5001"


class FutureProofEngine:
    """
    Main engine class that integrates all future-proofing abstractions.
    
    Designed to work across different:
    - Operating systems (Windows, Linux, macOS)
    - Hardware configurations (CPU-only, NVIDIA, AMD, Intel GPU)
    - Network protocols (IPFS, libp2p, future protocols)
    - Python versions (3.8+)
    - Dependency versions (flexible ranges)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the future-proofed engine."""
        self.config_file = config_file or "collatz_config.json"
        self.config = None
        self.network_transport = None
        self.compute_engine = None
        self.is_running = False
        self.stats = {
            'ranges_computed': 0,
            'ranges_verified': 0,
            'total_numbers_checked': 0,
            'start_time': None,
            'uptime': 0
        }
        
        logger.info("Initializing Future-Proof Collatz Engine")
        self._load_configuration()
        self._initialize_components()
    
    def _load_configuration(self):
        """Load configuration using future-proofed config system."""
        if CONFIG_AVAILABLE:
            try:
                config_manager = ConfigurationManager(self.config_file)
                self.config = config_manager.load_config()
                logger.info(f"Loaded configuration version {self.config.version}")
                return
            except Exception as e:
                logger.warning(f"Config manager failed: {e}, using fallback")
        
        # Fallback configuration loading
        self.config = FallbackConfig()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Map known fields to fallback config
                if 'network' in config_data:
                    self.config.network_transport = config_data['network'].get('transport', 'auto')
                if 'compute' in config_data:
                    self.config.compute_engine = config_data['compute'].get('engine', 'auto')
                
                logger.info("Loaded configuration using fallback parser")
            except Exception as e:
                logger.warning(f"Could not load config file: {e}, using defaults")
        else:
            logger.info("No config file found, using default configuration")
    
    def _initialize_components(self):
        """Initialize network and compute components with fallbacks."""
        # Initialize network transport
        if NETWORK_AVAILABLE:
            try:
                transport_type = getattr(self.config, 'network_transport', 'auto')
                if hasattr(self.config, 'network') and hasattr(self.config.network, 'transport'):
                    transport_type = self.config.network.transport
                
                self.network_transport = create_network_transport(transport_type)
                logger.info(f"Initialized network transport: {type(self.network_transport).__name__}")
            except Exception as e:
                logger.warning(f"Network transport initialization failed: {e}")
        else:
            logger.info("Network transport abstraction not available")
        
        # Initialize compute engine
        if COMPUTE_AVAILABLE:
            try:
                engine_type = getattr(self.config, 'compute_engine', 'auto')
                if hasattr(self.config, 'compute') and hasattr(self.config.compute, 'engine'):
                    engine_type = self.config.compute.engine
                
                self.compute_engine = create_compute_engine(engine_type)
                
                # Initialize the engine
                compute_config = {}
                if hasattr(self.config, 'compute'):
                    compute_config = asdict(self.config.compute) if hasattr(self.config.compute, '__dict__') else {}
                
                if self.compute_engine.initialize(compute_config):
                    logger.info(f"Initialized compute engine: {type(self.compute_engine).__name__}")
                else:
                    logger.warning("Compute engine initialization failed, using fallback")
                    self.compute_engine = None
                    
            except Exception as e:
                logger.warning(f"Compute engine initialization failed: {e}")
        else:
            logger.info("Compute engine abstraction not available")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information for debugging."""
        import platform
        
        info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            },
            'components': {
                'network_available': NETWORK_AVAILABLE,
                'compute_available': COMPUTE_AVAILABLE,
                'config_available': CONFIG_AVAILABLE,
                'network_transport': type(self.network_transport).__name__ if self.network_transport else None,
                'compute_engine': type(self.compute_engine).__name__ if self.compute_engine else None
            },
            'configuration': {
                'config_file': self.config_file,
                'config_type': type(self.config).__name__
            }
        }
        
        # Add available transports and engines
        if NETWORK_AVAILABLE:
            try:
                info['available_transports'] = NetworkTransportFactory.get_available_transports()
            except:
                pass
        
        if COMPUTE_AVAILABLE:
            try:
                info['available_engines'] = ComputeEngineFactory.get_available_engines()
            except:
                pass
        
        return info
    
    def verify_collatz_range(self, start: int, end: int) -> tuple[bool, Dict[str, Any]]:
        """
        Verify Collatz conjecture for a range using the best available compute engine.
        
        Args:
            start: Starting number (inclusive)
            end: Ending number (exclusive)
            
        Returns:
            Tuple of (success, stats)
        """
        if self.compute_engine:
            try:
                return self.compute_engine.verify_collatz_range(start, end)
            except Exception as e:
                logger.warning(f"Compute engine failed: {e}, using fallback")
        
        # Fallback CPU implementation
        return self._fallback_cpu_verification(start, end)
    
    def _fallback_cpu_verification(self, start: int, end: int) -> tuple[bool, Dict[str, Any]]:
        """Fallback CPU-only Collatz verification."""
        start_time = time.time()
        
        def collatz_steps(n):
            """Count steps for single number."""
            if n <= 0:
                return 0
            steps = 0
            while n != 1:
                if n % 2 == 0:
                    n = n // 2
                else:
                    n = 3 * n + 1
                steps += 1
                if steps > 1000000:  # Prevent infinite loops
                    return -1
            return steps
        
        # Verify each number in range
        for n in range(start, end):
            steps = collatz_steps(n)
            if steps == -1:
                # Found potential counterexample
                return False, {
                    'backend': 'CPU_FALLBACK',
                    'counterexample': n,
                    'range_start': start,
                    'range_end': end,
                    'duration': time.time() - start_time
                }
        
        return True, {
            'backend': 'CPU_FALLBACK',
            'range_start': start,
            'range_end': end,
            'numbers_verified': end - start,
            'duration': time.time() - start_time
        }
    
    def start_distributed_computation(self):
        """Start distributed computation with network coordination."""
        if not self.network_transport:
            logger.warning("No network transport available, running in local mode")
            return self._start_local_computation()
        
        try:
            # Connect to network
            if not self.network_transport.connect():
                logger.error("Failed to connect to network")
                return False
            
            logger.info(f"Connected to network as node: {self.network_transport.get_node_id()}")
            
            # Start computation loop
            self.is_running = True
            self.stats['start_time'] = time.time()
            
            threading.Thread(target=self._computation_worker, daemon=True).start()
            threading.Thread(target=self._network_worker, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start distributed computation: {e}")
            return False
    
    def _start_local_computation(self):
        """Start local-only computation mode."""
        logger.info("Starting local computation mode")
        
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        # Simple local computation
        current_range = 1
        chunk_size = getattr(self.config, 'chunk_size', 10000)
        
        while self.is_running:
            try:
                start = current_range
                end = current_range + chunk_size
                
                logger.info(f"Verifying range {start}-{end}")
                success, stats = self.verify_collatz_range(start, end)
                
                if success:
                    self.stats['ranges_computed'] += 1
                    self.stats['total_numbers_checked'] += (end - start)
                    logger.info(f"Range {start}-{end} verified successfully")
                else:
                    logger.error(f"COUNTEREXAMPLE FOUND: {stats}")
                    break
                
                current_range = end
                time.sleep(0.1)  # Small delay to prevent 100% CPU usage
                
            except KeyboardInterrupt:
                logger.info("Computation stopped by user")
                break
            except Exception as e:
                logger.error(f"Computation error: {e}")
                break
        
        self.is_running = False
        return True
    
    def _computation_worker(self):
        """Background worker for distributed computation."""
        # Implementation would coordinate with network for work distribution
        # For now, delegate to local computation
        self._start_local_computation()
    
    def _network_worker(self):
        """Background worker for network communication."""
        # Implementation would handle network messages and coordination
        while self.is_running:
            try:
                # Placeholder for network coordination
                time.sleep(1)
            except Exception as e:
                logger.error(f"Network worker error: {e}")
                break
    
    def stop(self):
        """Stop the engine gracefully."""
        logger.info("Stopping Future-Proof Collatz Engine")
        self.is_running = False
        
        if self.compute_engine:
            try:
                self.compute_engine.cleanup()
            except:
                pass
        
        if self.network_transport:
            try:
                self.network_transport.disconnect()
            except:
                pass
        
        # Update final stats
        if self.stats['start_time']:
            self.stats['uptime'] = time.time() - self.stats['start_time']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current engine statistics."""
        current_stats = self.stats.copy()
        if self.stats['start_time'] and self.is_running:
            current_stats['uptime'] = time.time() - self.stats['start_time']
        
        return current_stats


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(description='Future-Proof Distributed Collatz Engine')
    parser.add_argument('--config', help='Configuration file path', default='collatz_config.json')
    parser.add_argument('--network', help='Network transport type', default='auto')
    parser.add_argument('--compute', help='Compute engine type', default='auto')
    parser.add_argument('--info', action='store_true', help='Show system information and exit')
    parser.add_argument('--test', action='store_true', help='Run basic functionality test')
    parser.add_argument('--local', action='store_true', help='Force local mode (no network)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  FUTURE-PROOF DISTRIBUTED COLLATZ ENGINE")
    print("=" * 60)
    print()
    
    # Create engine instance
    engine = FutureProofEngine(args.config)
    
    if args.info:
        # Show system information
        info = engine.get_system_info()
        print("System Information:")
        print(f"  Platform: {info['platform']['system']} {info['platform']['release']}")
        print(f"  Architecture: {info['platform']['machine']}")
        print(f"  Python: {info['platform']['python_version']}")
        print()
        
        print("Component Availability:")
        components = info['components']
        print(f"  Network Transport: {'✓' if components['network_available'] else '✗'} ({components['network_transport'] or 'None'})")
        print(f"  Compute Engine: {'✓' if components['compute_available'] else '✗'} ({components['compute_engine'] or 'None'})")
        print(f"  Configuration Manager: {'✓' if components['config_available'] else '✗'}")
        print()
        
        if 'available_transports' in info:
            print(f"  Available Transports: {', '.join(info['available_transports'])}")
        if 'available_engines' in info:
            print(f"  Available Engines: {', '.join(info['available_engines'])}")
        
        return
    
    if args.test:
        # Run basic functionality test
        print("Running basic functionality test...")
        
        # Test configuration
        print(f"✓ Configuration loaded: {type(engine.config).__name__}")
        
        # Test compute engine
        print("Testing compute verification...")
        start_time = time.time()
        success, stats = engine.verify_collatz_range(1, 100)
        duration = time.time() - start_time
        
        if success:
            print(f"✓ Verified range 1-100 in {duration:.3f}s using {stats.get('backend', 'unknown')}")
        else:
            print(f"✗ Verification failed: {stats}")
        
        # Test network if available
        if engine.network_transport:
            print("✓ Network transport available")
        else:
            print("⚠ Network transport not available (will run in local mode)")
        
        print("\nBasic functionality test completed!")
        return
    
    # Normal operation
    try:
        if args.local:
            print("Starting in local-only mode...")
            engine._start_local_computation()
        else:
            print("Starting distributed computation...")
            engine.start_distributed_computation()
        
        # Keep running until interrupted
        while engine.is_running:
            time.sleep(1)
            
            # Print periodic stats
            stats = engine.get_stats()
            if stats['ranges_computed'] > 0 and stats['ranges_computed'] % 10 == 0:
                print(f"Progress: {stats['ranges_computed']} ranges, "
                      f"{stats['total_numbers_checked']} numbers verified, "
                      f"uptime: {stats['uptime']:.1f}s")
    
    except KeyboardInterrupt:
        print("\nShutdown requested by user...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        engine.stop()
        
        # Print final stats
        final_stats = engine.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  Ranges computed: {final_stats['ranges_computed']}")
        print(f"  Numbers verified: {final_stats['total_numbers_checked']}")
        print(f"  Total uptime: {final_stats['uptime']:.1f}s")
        
        if final_stats['total_numbers_checked'] > 0 and final_stats['uptime'] > 0:
            rate = final_stats['total_numbers_checked'] / final_stats['uptime']
            print(f"  Verification rate: {rate:.0f} numbers/second")


if __name__ == "__main__":
    main()
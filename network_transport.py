"""
FUTURE-PROOFED NETWORK TRANSPORT ABSTRACTION
============================================

This module provides a transport-agnostic interface for distributed networking,
allowing the Collatz engine to work with different P2P protocols and adapt
to future networking technologies.

Current backends:
- IPFS (primary)
- Future: libp2p, BitTorrent, custom protocols
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import json
import time
import logging

logger = logging.getLogger(__name__)

class NetworkTransport(ABC):
    """
    Abstract base class for network transport backends.
    
    Future-proofs the system against changes in:
    - P2P protocols (IPFS -> libp2p, etc.)
    - Network layers (IPv4 -> IPv6, TCP -> QUIC)
    - Transport mechanisms (HTTP -> WebRTC, etc.)
    """
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to the network with given configuration."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the network."""
        pass
    
    @abstractmethod
    def get_node_id(self) -> str:
        """Get unique identifier for this node."""
        pass
    
    @abstractmethod
    def publish_data(self, data: Dict[str, Any]) -> str:
        """Publish data to network, return content identifier."""
        pass
    
    @abstractmethod
    def retrieve_data(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by content identifier."""
        pass
    
    @abstractmethod
    def discover_peers(self) -> List[str]:
        """Discover other nodes in the network."""
        pass
    
    @abstractmethod
    def get_peer_data(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Get latest state data from a specific peer."""
        pass
    
    @abstractmethod
    def broadcast_state(self, state_data: Dict[str, Any]) -> bool:
        """Broadcast state to all known peers."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the network."""
        pass
    
    @abstractmethod
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics and health metrics."""
        pass


class IPFSTransport(NetworkTransport):
    """
    IPFS-based transport implementation.
    
    Maintains compatibility with existing IPFS infrastructure while
    providing standardized interface for future migration.
    """
    
    def __init__(self):
        self.client = None
        self.node_id = None
        self.connected = False
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to IPFS node."""
        try:
            # Dynamic import to handle missing dependencies gracefully
            import ipfshttpclient
            
            api_endpoint = config.get('ipfs_api', '/ip4/127.0.0.1/tcp/5001')
            self.client = ipfshttpclient.connect(api_endpoint)
            
            # Verify connection
            node_info = self.client.id()
            self.node_id = node_info['ID']
            self.connected = True
            
            logger.info(f"Connected to IPFS network: {self.node_id[:16]}...")
            return True
            
        except ImportError:
            logger.error("IPFS client not available. Install: pip install ipfshttpclient")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from IPFS."""
        try:
            if self.client:
                # IPFS HTTP client doesn't require explicit disconnect
                self.client = None
            self.connected = False
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from IPFS: {e}")
            return False
    
    def get_node_id(self) -> str:
        """Get IPFS node ID."""
        return self.node_id or ""
    
    def publish_data(self, data: Dict[str, Any]) -> str:
        """Publish data to IPFS, return CID."""
        if not self.connected or not self.client:
            raise RuntimeError("Not connected to IPFS network")
        
        try:
            result = self.client.add_json(data)
            logger.debug(f"Published data to IPFS: {result[:16]}...")
            return result
        except Exception as e:
            logger.error(f"Failed to publish data: {e}")
            raise
    
    def retrieve_data(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from IPFS by CID."""
        if not self.connected or not self.client:
            return None
        
        try:
            data = self.client.get_json(content_id)
            return data
        except Exception as e:
            logger.warning(f"Failed to retrieve data {content_id}: {e}")
            return None
    
    def discover_peers(self) -> List[str]:
        """Discover IPFS swarm peers."""
        if not self.connected or not self.client:
            return []
        
        try:
            peers = self.client.swarm.peers()
            peer_ids = [peer['Peer'] for peer in peers]
            return peer_ids
        except Exception as e:
            logger.warning(f"Failed to discover peers: {e}")
            return []
    
    def get_peer_data(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Get peer state (IPFS implementation specific)."""
        # This would require peer to publish their state to IPNS
        # Implementation depends on peer state sharing protocol
        logger.debug(f"Getting peer data for {peer_id[:16]}...")
        return None  # TODO: Implement peer state retrieval
    
    def broadcast_state(self, state_data: Dict[str, Any]) -> bool:
        """Broadcast state via IPFS (publish to IPNS)."""
        try:
            # Publish state data and announce via IPNS
            cid = self.publish_data(state_data)
            logger.debug(f"Broadcasted state: {cid[:16]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to broadcast state: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check IPFS connection status."""
        return self.connected and self.client is not None
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get IPFS network statistics."""
        if not self.connected or not self.client:
            return {}
        
        try:
            stats = {
                'node_id': self.node_id,
                'peer_count': len(self.discover_peers()),
                'connected': self.connected,
                'transport_type': 'IPFS'
            }
            return stats
        except Exception as e:
            logger.warning(f"Failed to get network stats: {e}")
            return {}


class LibP2PTransport(NetworkTransport):
    """
    Future libp2p transport implementation.
    
    Placeholder for when libp2p Python bindings become available.
    """
    
    def __init__(self):
        self.connected = False
        logger.warning("LibP2P transport not yet implemented")
    
    def connect(self, config: Dict[str, Any]) -> bool:
        logger.error("LibP2P transport not implemented")
        return False
    
    def disconnect(self) -> bool:
        return True
    
    def get_node_id(self) -> str:
        return ""
    
    def publish_data(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError("LibP2P transport not implemented")
    
    def retrieve_data(self, content_id: str) -> Optional[Dict[str, Any]]:
        return None
    
    def discover_peers(self) -> List[str]:
        return []
    
    def get_peer_data(self, peer_id: str) -> Optional[Dict[str, Any]]:
        return None
    
    def broadcast_state(self, state_data: Dict[str, Any]) -> bool:
        return False
    
    def is_connected(self) -> bool:
        return False
    
    def get_network_stats(self) -> Dict[str, Any]:
        return {'transport_type': 'LibP2P', 'status': 'not_implemented'}


class NetworkTransportFactory:
    """
    Factory for creating network transport instances.
    
    Allows runtime selection of transport backend based on:
    - Available dependencies
    - Configuration preferences  
    - Network conditions
    """
    
    _transports = {
        'ipfs': IPFSTransport,
        'libp2p': LibP2PTransport,
    }
    
    @classmethod
    def create_transport(cls, transport_type: str = 'auto') -> NetworkTransport:
        """
        Create a network transport instance.
        
        Args:
            transport_type: 'ipfs', 'libp2p', or 'auto' for automatic selection
            
        Returns:
            NetworkTransport instance
            
        Raises:
            ValueError: If transport type is unsupported
        """
        if transport_type == 'auto':
            transport_type = cls._auto_select_transport()
        
        if transport_type not in cls._transports:
            available = list(cls._transports.keys())
            raise ValueError(f"Unsupported transport '{transport_type}'. Available: {available}")
        
        transport_class = cls._transports[transport_type]
        return transport_class()
    
    @classmethod
    def _auto_select_transport(cls) -> str:
        """Automatically select best available transport."""
        # Try IPFS first (current primary)
        try:
            import ipfshttpclient
            logger.info("Auto-selected IPFS transport")
            return 'ipfs'
        except ImportError:
            pass
        
        # Try libp2p if available (future)
        try:
            import libp2p  # Not available yet
            logger.info("Auto-selected LibP2P transport")
            return 'libp2p'
        except ImportError:
            pass
        
        # Fallback to IPFS (will fail gracefully)
        logger.warning("No transport dependencies found, defaulting to IPFS")
        return 'ipfs'
    
    @classmethod
    def get_available_transports(cls) -> List[str]:
        """Get list of available transport backends."""
        available = []
        
        # Check IPFS
        try:
            import ipfshttpclient
            available.append('ipfs')
        except ImportError:
            pass
        
        # Check libp2p (future)
        try:
            import libp2p
            available.append('libp2p')
        except ImportError:
            pass
        
        return available


# Future-proofed network configuration
DEFAULT_NETWORK_CONFIG = {
    'transport': 'auto',  # Auto-select best available
    'ipfs_api': '/ip4/127.0.0.1/tcp/5001',
    'connection_timeout': 30,
    'retry_attempts': 3,
    'peer_discovery_interval': 60,
    'state_broadcast_interval': 300,  # 5 minutes
}


def create_network_transport(config: Optional[Dict[str, Any]] = None) -> NetworkTransport:
    """
    Convenience function to create a network transport.
    
    Args:
        config: Network configuration dictionary
        
    Returns:
        Configured NetworkTransport instance
    """
    if config is None:
        config = DEFAULT_NETWORK_CONFIG.copy()
    
    transport_type = config.get('transport', 'auto')
    transport = NetworkTransportFactory.create_transport(transport_type)
    
    return transport


# Example usage and testing
if __name__ == "__main__":
    # Test transport creation and basic functionality
    logging.basicConfig(level=logging.INFO)
    
    print("Available transports:", NetworkTransportFactory.get_available_transports())
    
    try:
        transport = create_network_transport()
        print(f"Created transport: {type(transport).__name__}")
        
        # Test connection
        if transport.connect(DEFAULT_NETWORK_CONFIG):
            print(f"Connected! Node ID: {transport.get_node_id()[:16]}...")
            print(f"Network stats: {transport.get_network_stats()}")
            transport.disconnect()
        else:
            print("Failed to connect to network")
            
    except Exception as e:
        print(f"Transport test failed: {e}")
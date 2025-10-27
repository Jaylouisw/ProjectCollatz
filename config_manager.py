"""
FUTURE-PROOFED CONFIGURATION MANAGEMENT
=======================================

This module provides a flexible, version-aware configuration system that can
adapt to changing requirements, standards, and deployment environments.

Features:
- JSON Schema validation for config files
- Version migration for backward compatibility  
- Environment variable overrides
- Multi-environment support (dev, staging, prod)
- Forward-compatible config parsing
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import jsonschema
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Current configuration schema version
CONFIG_SCHEMA_VERSION = "2.0"

# Future-proofed configuration schema
CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "description": "Configuration schema version",
            "default": CONFIG_SCHEMA_VERSION
        },
        "network": {
            "type": "object",
            "properties": {
                "transport": {
                    "type": "string",
                    "enum": ["auto", "ipfs", "libp2p"],
                    "default": "auto",
                    "description": "Network transport backend"
                },
                "ipfs_api": {
                    "type": "string",
                    "default": "/ip4/127.0.0.1/tcp/5001",
                    "description": "IPFS API endpoint"
                },
                "connection_timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 30,
                    "description": "Network connection timeout (seconds)"
                },
                "peer_discovery_interval": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 3600,
                    "default": 60,
                    "description": "Peer discovery interval (seconds)"
                }
            },
            "additionalProperties": True  # Allow future network options
        },
        "compute": {
            "type": "object",
            "properties": {
                "engine": {
                    "type": "string",
                    "enum": ["auto", "cpu", "cuda", "rocm", "intel"],
                    "default": "auto",
                    "description": "Compute engine backend"
                },
                "max_steps": {
                    "type": "integer",
                    "minimum": 1000,
                    "maximum": 1000000,
                    "default": 100000,
                    "description": "Maximum Collatz steps before timeout"
                },
                "chunk_size": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 100000,
                    "default": 10000,
                    "description": "Processing chunk size"
                },
                "memory_limit_gb": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1024.0,
                    "default": 4.0,
                    "description": "Memory limit in GB"
                }
            },
            "additionalProperties": True  # Allow future compute options
        },
        "security": {
            "type": "object",
            "properties": {
                "consensus_requirements": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 3,
                    "description": "Minimum consensus confirmations"
                },
                "trust_levels_enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable trust-level restrictions"
                },
                "byzantine_tolerance": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable Byzantine fault tolerance"
                }
            },
            "additionalProperties": True  # Allow future security options
        },
        "deployment": {
            "type": "object",
            "properties": {
                "environment": {
                    "type": "string",
                    "enum": ["development", "staging", "production"],
                    "default": "development",
                    "description": "Deployment environment"
                },
                "log_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "default": "INFO",
                    "description": "Logging level"
                },
                "data_directory": {
                    "type": "string",
                    "default": "./data",
                    "description": "Data storage directory"
                }
            },
            "additionalProperties": True  # Allow future deployment options
        }
    },
    "required": ["version"],
    "additionalProperties": True  # Allow future top-level sections
}

@dataclass
class NetworkConfig:
    """Network configuration with future-proofing."""
    transport: str = "auto"
    ipfs_api: str = "/ip4/127.0.0.1/tcp/5001"
    connection_timeout: int = 30
    peer_discovery_interval: int = 60
    
    # Future-proofing: store unknown config options
    _extra_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self._extra_options is None:
            self._extra_options = {}

@dataclass
class ComputeConfig:
    """Compute configuration with future-proofing."""
    engine: str = "auto"
    max_steps: int = 100000
    chunk_size: int = 10000
    memory_limit_gb: float = 4.0
    
    # Future-proofing: store unknown config options
    _extra_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self._extra_options is None:
            self._extra_options = {}

@dataclass
class SecurityConfig:
    """Security configuration with future-proofing."""
    consensus_requirements: int = 3
    trust_levels_enabled: bool = True
    byzantine_tolerance: bool = True
    
    # Future-proofing: store unknown config options
    _extra_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self._extra_options is None:
            self._extra_options = {}

@dataclass
class DeploymentConfig:
    """Deployment configuration with future-proofing."""
    environment: str = "development"
    log_level: str = "INFO"
    data_directory: str = "./data"
    
    # Future-proofing: store unknown config options
    _extra_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self._extra_options is None:
            self._extra_options = {}

@dataclass
class CollatzConfig:
    """Main configuration class with version management."""
    version: str = CONFIG_SCHEMA_VERSION
    network: NetworkConfig = None
    compute: ComputeConfig = None  
    security: SecurityConfig = None
    deployment: DeploymentConfig = None
    
    # Future-proofing: store unknown config sections
    _extra_sections: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.network is None:
            self.network = NetworkConfig()
        if self.compute is None:
            self.compute = ComputeConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.deployment is None:
            self.deployment = DeploymentConfig()
        if self._extra_sections is None:
            self._extra_sections = {}

class ConfigurationManager:
    """
    Future-proofed configuration management system.
    
    Handles:
    - Config file loading with validation
    - Version migration for backward compatibility
    - Environment variable overrides
    - Default value management
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "collatz_config.json"
        self.config: Optional[CollatzConfig] = None
        
    def load_config(self, create_if_missing: bool = True) -> CollatzConfig:
        """
        Load configuration from file with validation and migration.
        
        Args:
            create_if_missing: Create default config if file doesn't exist
            
        Returns:
            CollatzConfig instance
        """
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            if create_if_missing:
                logger.info(f"Creating default config: {config_path}")
                self.config = CollatzConfig()
                self.save_config()
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")
        else:
            logger.info(f"Loading config from: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = json.load(f)
            
            # Validate against schema
            try:
                jsonschema.validate(raw_config, CONFIG_SCHEMA)
            except jsonschema.ValidationError as e:
                logger.warning(f"Config validation warning: {e.message}")
                # Continue with best-effort parsing
            
            # Check version and migrate if needed
            config_version = raw_config.get('version', '1.0')
            if config_version != CONFIG_SCHEMA_VERSION:
                logger.info(f"Migrating config from v{config_version} to v{CONFIG_SCHEMA_VERSION}")
                raw_config = self._migrate_config(raw_config, config_version)
            
            # Parse into structured config
            self.config = self._parse_raw_config(raw_config)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        return self.config
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        if not self.config:
            logger.error("No config to save")
            return False
        
        try:
            config_dict = self._config_to_dict(self.config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            
            logger.info(f"Config saved to: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _migrate_config(self, raw_config: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """
        Migrate configuration from older versions.
        
        This method handles backward compatibility by transforming
        old config formats to the current schema.
        """
        migrated = raw_config.copy()
        
        if from_version == "1.0":
            logger.info("Migrating from v1.0 to v2.0")
            
            # v1.0 -> v2.0 migrations:
            # - Renamed 'ipfs_endpoint' to 'ipfs_api'
            # - Added compute.engine selection
            # - Restructured security settings
            
            if 'ipfs_endpoint' in migrated:
                if 'network' not in migrated:
                    migrated['network'] = {}
                migrated['network']['ipfs_api'] = migrated.pop('ipfs_endpoint')
            
            # Add new sections with defaults
            if 'compute' not in migrated:
                migrated['compute'] = {'engine': 'auto'}
            
            if 'security' not in migrated:
                migrated['security'] = {
                    'consensus_requirements': 3,
                    'trust_levels_enabled': True,
                    'byzantine_tolerance': True
                }
        
        # Update version
        migrated['version'] = CONFIG_SCHEMA_VERSION
        
        return migrated
    
    def _parse_raw_config(self, raw_config: Dict[str, Any]) -> CollatzConfig:
        """Parse raw config dict into structured config objects."""
        
        # Extract known sections
        network_data = raw_config.get('network', {})
        compute_data = raw_config.get('compute', {})
        security_data = raw_config.get('security', {})
        deployment_data = raw_config.get('deployment', {})
        
        # Create config objects, preserving unknown options
        network_config = NetworkConfig(**{
            k: v for k, v in network_data.items() 
            if k in NetworkConfig.__annotations__
        })
        network_config._extra_options = {
            k: v for k, v in network_data.items()
            if k not in NetworkConfig.__annotations__
        }
        
        compute_config = ComputeConfig(**{
            k: v for k, v in compute_data.items()
            if k in ComputeConfig.__annotations__
        })
        compute_config._extra_options = {
            k: v for k, v in compute_data.items()
            if k not in ComputeConfig.__annotations__
        }
        
        security_config = SecurityConfig(**{
            k: v for k, v in security_data.items()
            if k in SecurityConfig.__annotations__
        })
        security_config._extra_options = {
            k: v for k, v in security_data.items()
            if k not in SecurityConfig.__annotations__
        }
        
        deployment_config = DeploymentConfig(**{
            k: v for k, v in deployment_data.items()
            if k in DeploymentConfig.__annotations__
        })
        deployment_config._extra_options = {
            k: v for k, v in deployment_data.items()
            if k not in DeploymentConfig.__annotations__
        }
        
        # Create main config
        main_config = CollatzConfig(
            version=raw_config.get('version', CONFIG_SCHEMA_VERSION),
            network=network_config,
            compute=compute_config,
            security=security_config,
            deployment=deployment_config
        )
        
        # Store unknown top-level sections
        known_sections = {'version', 'network', 'compute', 'security', 'deployment'}
        main_config._extra_sections = {
            k: v for k, v in raw_config.items()
            if k not in known_sections
        }
        
        return main_config
    
    def _config_to_dict(self, config: CollatzConfig) -> Dict[str, Any]:
        """Convert structured config back to dictionary for saving."""
        result = {
            'version': config.version,
            'network': {**asdict(config.network), **config.network._extra_options},
            'compute': {**asdict(config.compute), **config.compute._extra_options},
            'security': {**asdict(config.security), **config.security._extra_options},
            'deployment': {**asdict(config.deployment), **config.deployment._extra_options}
        }
        
        # Remove private attributes from serialization
        for section in result.values():
            if isinstance(section, dict):
                section.pop('_extra_options', None)
        
        # Add extra sections
        result.update(config._extra_sections)
        
        return result
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        if not self.config:
            return
        
        # Environment variable mappings
        env_mappings = {
            'COLLATZ_NETWORK_TRANSPORT': ('network', 'transport'),
            'COLLATZ_COMPUTE_ENGINE': ('compute', 'engine'),
            'COLLATZ_LOG_LEVEL': ('deployment', 'log_level'),
            'COLLATZ_DATA_DIR': ('deployment', 'data_directory'),
            'COLLATZ_IPFS_API': ('network', 'ipfs_api'),
            'COLLATZ_MAX_STEPS': ('compute', 'max_steps'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if key in ['max_steps', 'consensus_requirements', 'connection_timeout', 'peer_discovery_interval']:
                    value = int(value)
                elif key in ['memory_limit_gb']:
                    value = float(value)
                elif key in ['trust_levels_enabled', 'byzantine_tolerance']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                # Apply override
                section_obj = getattr(self.config, section)
                setattr(section_obj, key, value)
                
                logger.info(f"Applied env override: {env_var}={value}")
    
    def get_config(self) -> CollatzConfig:
        """Get current configuration, loading if necessary."""
        if self.config is None:
            self.load_config()
        return self.config


# Global configuration instance
_global_config_manager = None

def get_config_manager(config_file: Optional[str] = None) -> ConfigurationManager:
    """Get global configuration manager instance."""
    global _global_config_manager
    
    if _global_config_manager is None or config_file:
        _global_config_manager = ConfigurationManager(config_file)
    
    return _global_config_manager

def get_config() -> CollatzConfig:
    """Convenience function to get current configuration."""
    return get_config_manager().get_config()


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration management
    config_manager = ConfigurationManager("test_config.json")
    
    # Load/create config
    config = config_manager.load_config()
    print(f"Loaded config version: {config.version}")
    print(f"Network transport: {config.network.transport}")
    print(f"Compute engine: {config.compute.engine}")
    
    # Test environment overrides
    os.environ['COLLATZ_COMPUTE_ENGINE'] = 'cuda'
    config_manager._apply_env_overrides()
    print(f"After env override: {config.compute.engine}")
    
    # Save config
    config_manager.save_config()
    print("Configuration saved successfully")
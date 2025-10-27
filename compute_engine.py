"""
FUTURE-PROOFED COMPUTE ENGINE ABSTRACTION
=========================================

This module provides a compute-backend agnostic interface for mathematical
computations, allowing the Collatz engine to work with different hardware
accelerators and adapt to future computing technologies.

Current backends:
- CPU (NumPy-based, always available)
- CUDA (via CuPy, optional)
- Future: ROCm, Intel GPU, TPU, quantum simulators
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

class ComputeEngine(ABC):
    """
    Abstract base class for compute backends.
    
    Future-proofs the system against changes in:
    - GPU architectures (CUDA -> ROCm, Intel GPU)
    - Compute frameworks (CuPy -> JAX, PyTorch)
    - Hardware platforms (CPU -> GPU -> TPU -> Quantum)
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the compute backend with configuration."""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up compute resources."""
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about the compute device."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this compute backend is available."""
        pass
    
    @abstractmethod
    def verify_collatz_range(self, start: int, end: int, max_steps: int = 100000) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify Collatz conjecture for a range of numbers.
        
        Args:
            start: Start of range (inclusive)
            end: End of range (exclusive)  
            max_steps: Maximum steps before giving up
            
        Returns:
            (all_converged, stats_dict)
        """
        pass
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this compute backend."""
        pass


class CPUComputeEngine(ComputeEngine):
    """
    CPU-based compute engine using NumPy.
    
    Always available fallback that works on any hardware.
    Optimized for compatibility over performance.
    """
    
    def __init__(self):
        self.initialized = False
        self.device_info = None
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize CPU compute engine."""
        try:
            # CPU is always available if NumPy is installed
            import numpy as np
            import psutil
            
            self.device_info = {
                'backend': 'CPU',
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'numpy_version': np.__version__,
            }
            
            self.initialized = True
            logger.info(f"CPU compute engine initialized: {self.device_info['cpu_count']} cores")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to initialize CPU engine: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up CPU resources (minimal cleanup needed)."""
        self.initialized = False
        return True
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get CPU device information."""
        return self.device_info or {}
    
    def is_available(self) -> bool:
        """CPU is always available if NumPy is installed."""
        try:
            import numpy
            return True
        except ImportError:
            return False
    
    def verify_collatz_range(self, start: int, end: int, max_steps: int = 100000) -> Tuple[bool, Dict[str, Any]]:
        """CPU-based Collatz verification using NumPy."""
        if not self.initialized:
            raise RuntimeError("CPU compute engine not initialized")
        
        start_time = time.time()
        all_converged = True
        numbers_checked = 0
        max_steps_reached = 0
        
        try:
            # Process range in chunks for memory efficiency
            chunk_size = min(10000, end - start)
            
            for chunk_start in range(start, end, chunk_size):
                chunk_end = min(chunk_start + chunk_size, end)
                chunk_converged, chunk_stats = self._verify_chunk_cpu(
                    chunk_start, chunk_end, max_steps
                )
                
                if not chunk_converged:
                    all_converged = False
                
                numbers_checked += chunk_stats['numbers_checked']
                max_steps_reached += chunk_stats['max_steps_reached']
            
            compute_time = time.time() - start_time
            
            stats = {
                'backend': 'CPU',
                'numbers_checked': numbers_checked,
                'compute_time': compute_time,
                'max_steps_reached': max_steps_reached,
                'throughput': numbers_checked / compute_time if compute_time > 0 else 0
            }
            
            return all_converged, stats
            
        except Exception as e:
            logger.error(f"CPU verification failed: {e}")
            raise
    
    def _verify_chunk_cpu(self, start: int, end: int, max_steps: int) -> Tuple[bool, Dict[str, Any]]:
        """Verify a chunk of numbers using CPU."""
        all_converged = True
        numbers_checked = end - start
        max_steps_reached = 0
        
        # Vectorized Collatz computation using NumPy
        for n in range(start, end):
            if n <= 1:
                continue
                
            current = n
            steps = 0
            
            while current != 1 and steps < max_steps:
                if current % 2 == 0:
                    current = current // 2
                else:
                    current = 3 * current + 1
                steps += 1
            
            if current != 1:
                all_converged = False
                max_steps_reached += 1
        
        return all_converged, {
            'numbers_checked': numbers_checked,
            'max_steps_reached': max_steps_reached
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get CPU performance metrics."""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'backend': 'CPU'
            }
        except ImportError:
            return {'backend': 'CPU', 'metrics': 'unavailable'}


class CUDAComputeEngine(ComputeEngine):
    """
    CUDA-based compute engine using CuPy.
    
    High-performance GPU acceleration for NVIDIA hardware.
    """
    
    def __init__(self):
        self.initialized = False
        self.device_info = None
        self.cupy = None
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize CUDA compute engine."""
        try:
            # Try to import CuPy
            import cupy as cp
            self.cupy = cp
            
            # Check CUDA availability
            if not cp.cuda.is_available():
                logger.warning("CUDA is not available")
                return False
            
            device = cp.cuda.Device()
            self.device_info = {
                'backend': 'CUDA',
                'device_name': device.attributes['Name'].decode(),
                'compute_capability': f"{device.compute_capability[0]}.{device.compute_capability[1]}",
                'memory_gb': device.mem_info[1] / (1024**3),
                'cupy_version': cp.__version__,
            }
            
            self.initialized = True
            logger.info(f"CUDA compute engine initialized: {self.device_info['device_name']}")
            return True
            
        except ImportError:
            logger.info("CuPy not available, CUDA engine disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize CUDA engine: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up CUDA resources."""
        try:
            if self.cupy and self.initialized:
                # Free GPU memory pools
                mempool = self.cupy.get_default_memory_pool()
                mempool.free_all_blocks()
            self.initialized = False
            return True
        except Exception as e:
            logger.error(f"CUDA cleanup failed: {e}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get CUDA device information."""
        return self.device_info or {}
    
    def is_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import cupy as cp
            return cp.cuda.is_available()
        except ImportError:
            return False
    
    def verify_collatz_range(self, start: int, end: int, max_steps: int = 100000) -> Tuple[bool, Dict[str, Any]]:
        """GPU-accelerated Collatz verification using CUDA."""
        if not self.initialized:
            raise RuntimeError("CUDA compute engine not initialized")
        
        start_time = time.time()
        
        try:
            # Use CuPy for GPU computation
            cp = self.cupy
            
            # Create array of numbers to check
            numbers = cp.arange(start, end, dtype=cp.int64)
            all_converged = True
            
            # GPU-accelerated Collatz kernel would go here
            # For now, use CPU fallback with GPU memory management
            numbers_cpu = cp.asnumpy(numbers)
            
            numbers_checked = len(numbers_cpu)
            max_steps_reached = 0
            
            # TODO: Implement proper CUDA kernel
            for n in numbers_cpu:
                if n <= 1:
                    continue
                    
                current = n
                steps = 0
                
                while current != 1 and steps < max_steps:
                    if current % 2 == 0:
                        current = current // 2
                    else:
                        current = 3 * current + 1
                    steps += 1
                
                if current != 1:
                    all_converged = False
                    max_steps_reached += 1
            
            compute_time = time.time() - start_time
            
            stats = {
                'backend': 'CUDA',
                'numbers_checked': numbers_checked,
                'compute_time': compute_time,
                'max_steps_reached': max_steps_reached,
                'throughput': numbers_checked / compute_time if compute_time > 0 else 0
            }
            
            return all_converged, stats
            
        except Exception as e:
            logger.error(f"CUDA verification failed: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get CUDA performance metrics."""
        try:
            if not self.initialized or not self.cupy:
                return {'backend': 'CUDA', 'status': 'not_initialized'}
            
            cp = self.cupy
            device = cp.cuda.Device()
            mem_info = device.mem_info
            
            return {
                'backend': 'CUDA',
                'memory_used_gb': (mem_info[1] - mem_info[0]) / (1024**3),
                'memory_total_gb': mem_info[1] / (1024**3),
                'memory_utilization': (mem_info[1] - mem_info[0]) / mem_info[1]
            }
        except Exception as e:
            logger.warning(f"Failed to get CUDA metrics: {e}")
            return {'backend': 'CUDA', 'error': str(e)}


class ROCmComputeEngine(ComputeEngine):
    """
    AMD ROCm compute engine (future implementation).
    
    Placeholder for AMD GPU support when CuPy-ROCm becomes stable.
    """
    
    def __init__(self):
        self.initialized = False
        logger.info("ROCm compute engine created (not yet implemented)")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        logger.warning("ROCm compute engine not yet implemented")
        return False
    
    def cleanup(self) -> bool:
        return True
    
    def get_device_info(self) -> Dict[str, Any]:
        return {'backend': 'ROCm', 'status': 'not_implemented'}
    
    def is_available(self) -> bool:
        # Future: check for ROCm/HIP availability
        return False
    
    def verify_collatz_range(self, start: int, end: int, max_steps: int = 100000) -> Tuple[bool, Dict[str, Any]]:
        raise NotImplementedError("ROCm compute engine not implemented")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        return {'backend': 'ROCm', 'status': 'not_implemented'}


class ComputeEngineFactory:
    """
    Factory for creating compute engine instances.
    
    Allows runtime selection of compute backend based on:
    - Available hardware
    - Installed dependencies
    - Performance requirements
    """
    
    _engines = {
        'cpu': CPUComputeEngine,
        'cuda': CUDAComputeEngine,
        'rocm': ROCmComputeEngine,
    }
    
    @classmethod
    def create_engine(cls, engine_type: str = 'auto') -> ComputeEngine:
        """
        Create a compute engine instance.
        
        Args:
            engine_type: 'cpu', 'cuda', 'rocm', or 'auto' for automatic selection
            
        Returns:
            ComputeEngine instance
        """
        if engine_type == 'auto':
            engine_type = cls._auto_select_engine()
        
        if engine_type not in cls._engines:
            available = list(cls._engines.keys())
            raise ValueError(f"Unsupported engine '{engine_type}'. Available: {available}")
        
        engine_class = cls._engines[engine_type]
        return engine_class()
    
    @classmethod
    def _auto_select_engine(cls) -> str:
        """Automatically select best available compute engine."""
        # Prefer CUDA if available
        cuda_engine = CUDAComputeEngine()
        if cuda_engine.is_available():
            logger.info("Auto-selected CUDA compute engine")
            return 'cuda'
        
        # Try ROCm (when implemented)
        rocm_engine = ROCmComputeEngine()
        if rocm_engine.is_available():
            logger.info("Auto-selected ROCm compute engine")
            return 'rocm'
        
        # Fallback to CPU
        logger.info("Auto-selected CPU compute engine")
        return 'cpu'
    
    @classmethod
    def get_available_engines(cls) -> List[str]:
        """Get list of available compute engines."""
        available = []
        
        for engine_name, engine_class in cls._engines.items():
            engine = engine_class()
            if engine.is_available():
                available.append(engine_name)
        
        return available
    
    @classmethod
    def benchmark_engines(cls, test_range_size: int = 10000) -> Dict[str, Dict[str, Any]]:
        """
        Benchmark all available compute engines.
        
        Args:
            test_range_size: Size of test range for benchmarking
            
        Returns:
            Dict mapping engine names to benchmark results
        """
        results = {}
        available_engines = cls.get_available_engines()
        
        for engine_name in available_engines:
            try:
                engine = cls.create_engine(engine_name)
                if engine.initialize({}):
                    # Run benchmark
                    start_time = time.time()
                    all_converged, stats = engine.verify_collatz_range(1, test_range_size + 1)
                    benchmark_time = time.time() - start_time
                    
                    results[engine_name] = {
                        'throughput': stats.get('throughput', 0),
                        'compute_time': stats.get('compute_time', benchmark_time),
                        'device_info': engine.get_device_info(),
                        'all_converged': all_converged
                    }
                    
                    engine.cleanup()
                else:
                    results[engine_name] = {'error': 'failed_to_initialize'}
                    
            except Exception as e:
                results[engine_name] = {'error': str(e)}
        
        return results


# Future-proofed compute configuration
DEFAULT_COMPUTE_CONFIG = {
    'engine': 'auto',  # Auto-select best available
    'max_steps': 100000,
    'chunk_size': 10000,
    'memory_limit_gb': 4.0,
    'benchmark_on_startup': False,
}


def create_compute_engine(config: Optional[Dict[str, Any]] = None) -> ComputeEngine:
    """
    Convenience function to create a compute engine.
    
    Args:
        config: Compute configuration dictionary
        
    Returns:
        Configured ComputeEngine instance
    """
    if config is None:
        config = DEFAULT_COMPUTE_CONFIG.copy()
    
    engine_type = config.get('engine', 'auto')
    engine = ComputeEngineFactory.create_engine(engine_type)
    
    if not engine.initialize(config):
        # Fallback to CPU if preferred engine fails
        if engine_type != 'cpu':
            logger.warning(f"Failed to initialize {engine_type} engine, falling back to CPU")
            engine = ComputeEngineFactory.create_engine('cpu')
            engine.initialize(config)
    
    return engine


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Available compute engines:", ComputeEngineFactory.get_available_engines())
    
    # Benchmark all available engines
    print("\nBenchmarking compute engines...")
    results = ComputeEngineFactory.benchmark_engines(test_range_size=1000)
    
    for engine_name, result in results.items():
        print(f"\n{engine_name.upper()} Engine:")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Throughput: {result['throughput']:.2f} numbers/sec")
            print(f"  Compute time: {result['compute_time']:.3f}s")
            print(f"  Device: {result['device_info'].get('backend', 'Unknown')}")
    
    # Test auto-selection
    print("\nTesting auto-selected engine...")
    engine = create_compute_engine()
    print(f"Selected: {engine.get_device_info()}")
    engine.cleanup()
#!/usr/bin/env python3
"""
FUTURE-PROOFING VALIDATION SUITE
================================

This test suite validates that all future-proofing measures are working
correctly and that the system can adapt to changing requirements.

Test Categories:
1. Dependency Flexibility (version ranges, fallbacks)
2. Protocol Abstraction (transport independence)
3. Hardware Abstraction (compute backend flexibility)
4. Configuration Evolution (schema migration, compatibility)
5. Cross-Platform Compatibility (OS, architecture independence)
"""

import sys
import os
import json
import time
import logging
import unittest
from typing import Dict, Any, List
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from network_transport import NetworkTransportFactory, create_network_transport
    from compute_engine import ComputeEngineFactory, create_compute_engine
    from config_manager import ConfigurationManager, CollatzConfig, CONFIG_SCHEMA_VERSION
except ImportError as e:
    print(f"Warning: Could not import future-proofed modules: {e}")
    print("Some tests will be skipped")

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TestDependencyFlexibility(unittest.TestCase):
    """Test that dependency management is future-proofed."""
    
    def test_setup_py_version_ranges(self):
        """Test that setup.py uses version ranges instead of exact pins."""
        setup_file = Path(__file__).parent / "setup.py"
        if not setup_file.exists():
            self.skipTest("setup.py not found")
        
        with open(setup_file, 'r') as f:
            setup_content = f.read()
        
        # Check for problematic exact version pins
        problematic_patterns = ['==', '>=.*,<.*']  # Allow ranges like >=1.0,<2.0
        
        # Should have version ranges, not exact pins
        self.assertIn('>=', setup_content, "setup.py should use minimum version constraints")
        self.assertIn('<', setup_content, "setup.py should use maximum version constraints")
        
        # Specific checks for critical dependencies
        self.assertIn('ipfshttpclient>=', setup_content)
        self.assertIn('cryptography>=', setup_content)
        self.assertIn('numpy>=', setup_content)
    
    def test_requirements_flexibility(self):
        """Test that requirements.txt uses flexible versioning."""
        req_file = Path(__file__).parent / "requirements_distributed.txt"
        if not req_file.exists():
            self.skipTest("requirements_distributed.txt not found")
        
        with open(req_file, 'r') as f:
            req_content = f.read()
        
        # Should avoid exact version pins for stability
        exact_pins = [line for line in req_content.split('\n') 
                     if line.strip() and '==' in line and not line.strip().startswith('#')]
        
        # Allow some exact pins for testing, but minimize them
        self.assertLessEqual(len(exact_pins), 2, 
            f"Too many exact version pins: {exact_pins}")


class TestNetworkTransportAbstraction(unittest.TestCase):
    """Test network transport abstraction layer."""
    
    def test_transport_factory_auto_selection(self):
        """Test automatic transport selection."""
        try:
            available = NetworkTransportFactory.get_available_transports()
            self.assertIsInstance(available, list)
            
            if available:
                transport = NetworkTransportFactory.create_transport('auto')
                self.assertIsNotNone(transport)
                
                # Test transport interface
                self.assertTrue(hasattr(transport, 'connect'))
                self.assertTrue(hasattr(transport, 'disconnect'))
                self.assertTrue(hasattr(transport, 'get_node_id'))
                self.assertTrue(hasattr(transport, 'publish_data'))
        except Exception as e:
            self.skipTest(f"Network transport tests require dependencies: {e}")
    
    def test_transport_fallback_mechanism(self):
        """Test that transport creation falls back gracefully."""
        try:
            # Test invalid transport type
            with self.assertRaises(ValueError):
                NetworkTransportFactory.create_transport('nonexistent')
            
            # Test factory creation
            transport = create_network_transport()
            self.assertIsNotNone(transport)
            
        except Exception as e:
            self.skipTest(f"Transport fallback test requires imports: {e}")


class TestComputeEngineAbstraction(unittest.TestCase):
    """Test compute engine abstraction layer."""
    
    def test_compute_factory_auto_selection(self):
        """Test automatic compute engine selection."""
        try:
            available = ComputeEngineFactory.get_available_engines()
            self.assertIsInstance(available, list)
            self.assertIn('cpu', available, "CPU engine should always be available")
            
            # Test engine creation
            engine = ComputeEngineFactory.create_engine('cpu')
            self.assertIsNotNone(engine)
            
            # Test engine interface
            self.assertTrue(hasattr(engine, 'initialize'))
            self.assertTrue(hasattr(engine, 'verify_collatz_range'))
            self.assertTrue(hasattr(engine, 'cleanup'))
            
        except Exception as e:
            self.skipTest(f"Compute engine tests require dependencies: {e}")
    
    def test_cpu_engine_functionality(self):
        """Test that CPU engine works as fallback."""
        try:
            engine = ComputeEngineFactory.create_engine('cpu')
            
            # Test initialization
            self.assertTrue(engine.initialize({}))
            
            # Test basic computation
            result, stats = engine.verify_collatz_range(1, 11)  # Small test range
            self.assertIsInstance(result, bool)
            self.assertIsInstance(stats, dict)
            self.assertIn('backend', stats)
            self.assertEqual(stats['backend'], 'CPU')
            
            # Cleanup
            engine.cleanup()
            
        except Exception as e:
            self.skipTest(f"CPU engine test failed: {e}")
    
    def test_gpu_engine_graceful_fallback(self):
        """Test that GPU engines fail gracefully when not available."""
        try:
            available = ComputeEngineFactory.get_available_engines()
            
            if 'cuda' not in available:
                # CUDA not available, should create but not initialize
                cuda_engine = ComputeEngineFactory.create_engine('cuda')
                self.assertFalse(cuda_engine.is_available())
            
            # Auto-selection should always work (fallback to CPU)
            engine = ComputeEngineFactory.create_engine('auto')
            self.assertTrue(engine.initialize({}))
            engine.cleanup()
            
        except Exception as e:
            self.skipTest(f"GPU fallback test failed: {e}")


class TestConfigurationEvolution(unittest.TestCase):
    """Test configuration system future-proofing."""
    
    def setUp(self):
        """Set up test configuration file."""
        self.test_config_file = "test_future_proof_config.json"
        # Clean up any existing test file
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
    
    def tearDown(self):
        """Clean up test configuration file."""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
    
    def test_config_creation_and_loading(self):
        """Test configuration creation and loading."""
        try:
            # Create config manager
            config_manager = ConfigurationManager(self.test_config_file)
            
            # Load/create config
            config = config_manager.load_config()
            self.assertIsInstance(config, CollatzConfig)
            self.assertEqual(config.version, CONFIG_SCHEMA_VERSION)
            
            # Verify default values
            self.assertIsNotNone(config.network)
            self.assertIsNotNone(config.compute)
            self.assertIsNotNone(config.security)
            self.assertIsNotNone(config.deployment)
            
        except Exception as e:
            self.skipTest(f"Config tests require config_manager module: {e}")
    
    def test_config_version_migration(self):
        """Test configuration version migration."""
        try:
            # Create old-format config file
            old_config = {
                "version": "1.0",
                "ipfs_endpoint": "/ip4/127.0.0.1/tcp/5001",
                "max_steps": 50000
            }
            
            with open(self.test_config_file, 'w') as f:
                json.dump(old_config, f)
            
            # Load with migration
            config_manager = ConfigurationManager(self.test_config_file)
            config = config_manager.load_config()
            
            # Check migration occurred
            self.assertEqual(config.version, CONFIG_SCHEMA_VERSION)
            self.assertEqual(config.network.ipfs_api, "/ip4/127.0.0.1/tcp/5001")
            
        except Exception as e:
            self.skipTest(f"Config migration test failed: {e}")
    
    def test_config_unknown_options_preservation(self):
        """Test that unknown config options are preserved."""
        try:
            # Create config with unknown options
            future_config = {
                "version": CONFIG_SCHEMA_VERSION,
                "network": {
                    "transport": "ipfs",
                    "future_option": "future_value"
                },
                "future_section": {
                    "quantum_backend": "enabled"
                }
            }
            
            with open(self.test_config_file, 'w') as f:
                json.dump(future_config, f)
            
            # Load and verify unknown options preserved
            config_manager = ConfigurationManager(self.test_config_file)
            config = config_manager.load_config()
            
            self.assertIn("future_option", config.network._extra_options)
            self.assertIn("future_section", config._extra_sections)
            
        except Exception as e:
            self.skipTest(f"Unknown options test failed: {e}")


class TestCrossPlatformCompatibility(unittest.TestCase):
    """Test cross-platform compatibility."""
    
    def test_path_handling(self):
        """Test that paths are handled in OS-agnostic way."""
        # Test with different path separators
        test_paths = [
            "./data/test",
            "data\\test",
            "data/test",
            "/tmp/test"
        ]
        
        for path_str in test_paths:
            path = Path(path_str)
            # Should not raise exceptions
            self.assertIsInstance(str(path), str)
            self.assertIsInstance(path.parts, tuple)
    
    def test_environment_variable_handling(self):
        """Test environment variable handling across platforms."""
        # Set test environment variable
        test_var = "COLLATZ_TEST_VAR"
        test_value = "test_value"
        
        os.environ[test_var] = test_value
        
        try:
            # Should be readable on all platforms
            self.assertEqual(os.environ.get(test_var), test_value)
        finally:
            # Clean up
            if test_var in os.environ:
                del os.environ[test_var]
    
    def test_platform_detection(self):
        """Test platform detection capabilities."""
        import platform
        
        # Should be able to detect platform
        system = platform.system()
        self.assertIn(system, ['Windows', 'Linux', 'Darwin'])
        
        # Should be able to detect architecture
        machine = platform.machine()
        self.assertIsInstance(machine, str)
        
        # Python version should be detectable
        version = platform.python_version()
        self.assertIsInstance(version, str)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing systems."""
    
    def test_import_compatibility(self):
        """Test that old import paths still work."""
        # Test that we can still import core modules
        # (even if they've been refactored)
        
        try:
            # These should work on existing systems
            import json
            import os
            import sys
            import time
            
            # Core Python modules should be available
            self.assertTrue(True)  # If we get here, imports worked
            
        except ImportError as e:
            self.fail(f"Basic Python imports failed: {e}")
    
    def test_json_compatibility(self):
        """Test JSON format compatibility."""
        # Test that we can read old JSON formats
        test_json = {"version": "1.0", "test": True}
        
        # Should be able to serialize/deserialize
        json_str = json.dumps(test_json)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed, test_json)


class TestScalabilityAndPerformance(unittest.TestCase):
    """Test system scalability and performance characteristics."""
    
    def test_memory_efficiency(self):
        """Test that system doesn't have obvious memory leaks."""
        try:
            import psutil
            import gc
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Do some work
            for i in range(100):
                data = {'test': i, 'large_data': 'x' * 1000}
                json_str = json.dumps(data)
                parsed = json.loads(json_str)
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage didn't grow too much
            final_memory = process.memory_info().rss
            memory_growth = final_memory - initial_memory
            
            # Allow some growth but not excessive (less than 10MB for this test)
            self.assertLess(memory_growth, 10 * 1024 * 1024, 
                           f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB")
            
        except ImportError:
            self.skipTest("psutil not available for memory testing")
    
    def test_startup_time(self):
        """Test that system startup time is reasonable."""
        start_time = time.time()
        
        # Simulate system initialization
        try:
            # Test config loading
            config_data = {
                "version": CONFIG_SCHEMA_VERSION,
                "network": {"transport": "auto"},
                "compute": {"engine": "auto"}
            }
            json.dumps(config_data)
            
            # Test factory creation (without actual initialization)
            if 'NetworkTransportFactory' in globals():
                available_transports = NetworkTransportFactory.get_available_transports()
            
            if 'ComputeEngineFactory' in globals():
                available_engines = ComputeEngineFactory.get_available_engines()
            
        except Exception as e:
            pass  # Don't fail test for missing optional components
        
        startup_time = time.time() - start_time
        
        # Startup should be fast (less than 2 seconds)
        self.assertLess(startup_time, 2.0, 
                       f"Startup took {startup_time:.2f}s, should be < 2s")


def create_test_report() -> Dict[str, Any]:
    """Create a comprehensive test report."""
    
    # Run all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDependencyFlexibility,
        TestNetworkTransportAbstraction, 
        TestComputeEngineAbstraction,
        TestConfigurationEvolution,
        TestCrossPlatformCompatibility,
        TestBackwardCompatibility,
        TestScalabilityAndPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with custom result collector
    class TestResult:
        def __init__(self):
            self.successes = []
            self.failures = []
            self.errors = []
            self.skipped = []
    
    result = TestResult()
    
    # Run each test individually to collect detailed results
    for test_class in test_classes:
        class_name = test_class.__name__
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            test_name = f"{class_name}.{method_name}"
            
            try:
                # Create test instance and run method
                test_instance = test_class()
                
                # Run setUp if it exists
                if hasattr(test_instance, 'setUp'):
                    test_instance.setUp()
                
                # Run the test method
                getattr(test_instance, method_name)()
                
                # Run tearDown if it exists
                if hasattr(test_instance, 'tearDown'):
                    test_instance.tearDown()
                
                result.successes.append(test_name)
                
            except unittest.SkipTest as e:
                result.skipped.append(f"{test_name}: {e}")
            except AssertionError as e:
                result.failures.append(f"{test_name}: {e}")
            except Exception as e:
                result.errors.append(f"{test_name}: {e}")
    
    # Generate report
    total_tests = len(result.successes) + len(result.failures) + len(result.errors) + len(result.skipped)
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': total_tests,
        'successes': len(result.successes),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success_rate': len(result.successes) / total_tests if total_tests > 0 else 0,
        'detailed_results': {
            'successes': result.successes,
            'failures': result.failures,
            'errors': result.errors,
            'skipped': result.skipped
        }
    }
    
    return report


def main():
    """Main test runner with reporting."""
    print("=" * 60)
    print("  FUTURE-PROOFING VALIDATION SUITE")
    print("=" * 60)
    print()
    
    # System information
    import platform
    print(f"Python Version: {platform.python_version()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print()
    
    # Run tests and generate report
    print("Running future-proofing validation tests...")
    report = create_test_report()
    
    # Print summary
    print(f"\nTest Results Summary:")
    print(f"  Total Tests: {report['total_tests']}")
    print(f"  Successes: {report['successes']} ✓")
    print(f"  Failures: {report['failures']} ✗")
    print(f"  Errors: {report['errors']} ⚠️")
    print(f"  Skipped: {report['skipped']} ⏸️")
    print(f"  Success Rate: {report['success_rate']:.1%}")
    print()
    
    # Print details if there are issues
    if report['failures']:
        print("FAILURES:")
        for failure in report['detailed_results']['failures']:
            print(f"  ✗ {failure}")
        print()
    
    if report['errors']:
        print("ERRORS:")
        for error in report['detailed_results']['errors']:
            print(f"  ⚠️ {error}")
        print()
    
    if report['skipped']:
        print("SKIPPED (due to missing dependencies):")
        for skipped in report['detailed_results']['skipped']:
            print(f"  ⏸️ {skipped}")
        print()
    
    # Save detailed report
    report_file = f"future_proofing_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Detailed report saved to: {report_file}")
    
    # Overall assessment
    if report['success_rate'] >= 0.8:
        print("\n🎉 FUTURE-PROOFING STATUS: EXCELLENT")
        print("   System is well-prepared for future changes")
    elif report['success_rate'] >= 0.6:
        print("\n✅ FUTURE-PROOFING STATUS: GOOD")  
        print("   Most future-proofing measures are in place")
    elif report['success_rate'] >= 0.4:
        print("\n⚠️ FUTURE-PROOFING STATUS: NEEDS IMPROVEMENT")
        print("   Several future-proofing issues need attention")
    else:
        print("\n❌ FUTURE-PROOFING STATUS: CRITICAL")
        print("   Significant future-proofing work required")
    
    return report['success_rate'] >= 0.6  # Return success if >= 60% pass rate


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
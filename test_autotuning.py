"""Test GPU auto-tuning functionality."""
import os

print("\n=== Testing GPU Auto-Tuning ===\n")

# Remove existing tuning file to force auto-tune
if os.path.exists('gpu_tuning.json'):
    os.remove('gpu_tuning.json')
    print("✓ Removed existing tuning file\n")

print("[Test] Triggering auto-tuning...")
try:
    from CollatzEngine import get_gpu_config
    
    config = get_gpu_config()
    
    print("✓ Auto-tuning completed successfully\n")
    print("Configuration:")
    print(f"  Batch size: {config.get('batch_size')}")
    print(f"  Threads per block: {config.get('threads_per_block')}")
    print(f"  Blocks per grid: {config.get('blocks_per_grid')}")
    print(f"\n✓ GPU auto-tuning works automatically")
    
except Exception as e:
    print(f"✗ Auto-tuning failed: {e}")
    import traceback
    traceback.print_exc()

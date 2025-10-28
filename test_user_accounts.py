"""Test user account system."""
import time
from user_account import UserAccountManager

def test_user_accounts():
    print("\n=== Testing User Account System ===\n")
    
    # Initialize manager
    mgr = UserAccountManager()
    print("✓ Account manager initialized\n")
    
    # Test 1: Create new account
    print("[Test 1] Creating new account...")
    username = f'test_user_{int(time.time())}'
    private_key_file = f'test_{username}_key.pem'
    try:
        account, private_key = mgr.create_user_account(username, private_key_file)
        print(f"✓ Created account: {username}")
        print(f"  User ID: {account.user_id[:16]}...")
        print(f"  Workers: {account.registered_nodes}\n")
    except Exception as e:
        print(f"✗ Account creation failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Load account
    print("[Test 2] Loading account...")
    try:
        loaded, _ = mgr.load_user_account(private_key_file)
        if loaded and loaded.username == username:
            print(f"✓ Loaded account: {loaded.username}\n")
        else:
            print(f"✗ Account load mismatch\n")
            return False
    except Exception as e:
        print(f"✗ Account load failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Try to create duplicate username
    print("[Test 3] Testing username uniqueness...")
    try:
        mgr.create_user_account(username, 'test_worker_2')
        print(f"✗ Should not allow duplicate username\n")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected duplicate: {e}\n")
    except Exception as e:
        print(f"✗ Unexpected error: {e}\n")
        return False
    
    # Test 4: Add another node to same account
    print("[Test 4] Adding second worker to account...")
    try:
        mgr.register_node(account.user_id, 'test_worker_2')
        updated = mgr.get_account_by_user_id(account.user_id)
        if updated and 'test_worker_2' in updated.registered_nodes:
            print(f"✓ Added second worker")
            print(f"  Workers: {updated.registered_nodes}\n")
        else:
            print(f"✗ Worker not added\n")
            return False
    except Exception as e:
        print(f"✗ Failed to add worker: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    print("✓ All user account tests passed")
    print("=" * 60)
    return True

if __name__ == '__main__':
    import sys
    sys.exit(0 if test_user_accounts() else 1)

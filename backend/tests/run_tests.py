import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import test functions
try:
    from backend.tests.test_backend import (
        test_text_chunking,
        test_mock_embeddings,
        test_auth_endpoints,
        test_export_endpoints
    )
    HAS_TESTS = True
except ImportError as e:
    HAS_TESTS = False
    print(f"Warning: Could not import test suite functions: {e}")

try:
    from backend.app.services.database import init_db
    HAS_DB = True
except ImportError as e:
    HAS_DB = False
    init_db = None
    print(f"Warning: Database module not imported: {e}")

def run():
    print("=" * 50)
    print("ResearchPilot AI - Standalone Test Suite")
    print("=" * 50)
    
    # Initialize DB for testing
    if HAS_DB and init_db:
        try:
            init_db()
            print("[INIT] Database initialized successfully.")
        except Exception as e:
            print(f"[FAIL] Database initialization failed: {e}")
            return False
    else:
        print("[INIT] Database initialization skipped (Dependencies not available).")
        
    if not HAS_TESTS:
        print("[FAIL] Testing suite cannot run because imports are missing.")
        return False

    tests = [
        ("Text Chunking Heuristics", test_text_chunking),
        ("Mock Vector Store Embeddings", test_mock_embeddings),
        ("User Auth Registration & Login", test_auth_endpoints),
        ("Report Export System (MD, PDF)", test_export_endpoints)
    ]
    
    passed_count = 0
    for name, test_func in tests:
        try:
            print(f"[RUN]  Running: {name}...")
            test_func()
            print(f"[PASS] {name} completed successfully.")
            passed_count += 1
        except Exception as e:
            print(f"[FAIL] {name} failed: {e}")
            import traceback
            traceback.print_exc()
            
    print("=" * 50)
    print(f"Test Summary: {passed_count}/{len(tests)} passed.")
    print("=" * 50)
    
    return passed_count == len(tests)

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)

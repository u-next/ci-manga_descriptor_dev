#!/usr/bin/env python3
"""
Test Runner for Manga Descriptor Development

Convenient script to run all tests from the main directory.
Usage: python run_tests.py [test_name]
"""

import sys
import os
import subprocess

def run_test(test_name="all"):
    """Run specific test or all tests"""
    main_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(main_dir, "tests")
    
    if test_name == "all":
        print("🧪 Running all tests...")
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        
        for test_file in sorted(test_files):
            print(f"\n{'='*60}")
            print(f"Running {test_file}")
            print('='*60)
            
            result = subprocess.run([
                sys.executable, 
                os.path.join(tests_dir, test_file)
            ], cwd=main_dir)
            
            if result.returncode != 0:
                print(f"❌ {test_file} failed")
                return False
            else:
                print(f"✅ {test_file} passed")
    
    else:
        test_file = f"test_{test_name}.py"
        test_path = os.path.join(tests_dir, test_file)
        
        if not os.path.exists(test_path):
            print(f"❌ Test file {test_file} not found")
            return False
        
        print(f"🧪 Running {test_file}...")
        result = subprocess.run([sys.executable, test_path], cwd=main_dir)
        return result.returncode == 0
    
    return True

if __name__ == "__main__":
    test_name = sys.argv[1] if len(sys.argv) > 1 else "all"
    success = run_test(test_name)
    sys.exit(0 if success else 1)
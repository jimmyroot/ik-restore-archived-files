#!/usr/bin/env python3
"""
Test script to demonstrate the path construction functionality
"""

import os
import sys

# Add the current directory to the path so we can import from restore-files
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the function we want to test
# Note: We need to handle the hyphen in the filename
import importlib.util
spec = importlib.util.spec_from_file_location("restore_files", "restore-files.py")
restore_files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore_files)
construct_archive_path = restore_files.construct_archive_path

def test_path_construction():
    """Test the path construction with various inputs"""
    
    print("=== Testing Path Construction ===\n")
    
    # Test cases
    test_cases = [
        # Windows-style paths
        ("C:\\Users\\John\\Documents", "D", "Windows drive letter"),
        ("C:\\Users\\John\\Documents", "D:", "Windows drive letter with colon"),
        ("C:\\Users\\John\\Documents", "E:\\Archive", "Windows full path"),
        
        # Unix-style paths (macOS/Linux)
        ("/Users/jimmy/Documents", "/Users/jimmy/egnyte-archive", "macOS mount point"),
        ("/home/user/documents", "/mnt/archive", "Linux mount point"),
        ("/Users/jimmy/Projects", "/Volumes/External/Backup", "macOS external volume"),
    ]
    
    for target_dir, archive_input, description in test_cases:
        print(f"Test: {description}")
        print(f"  Target: {target_dir}")
        print(f"  Archive input: {archive_input}")
        
        try:
            result = construct_archive_path(target_dir, archive_input)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
    
    # Test error cases
    print("=== Testing Error Cases ===\n")
    
    error_cases = [
        ("/Users/jimmy/Documents", "D", "Drive letter on Unix system"),
        ("/Users/jimmy/Documents", "D:", "Drive letter with colon on Unix system"),
    ]
    
    for target_dir, archive_input, description in error_cases:
        print(f"Test: {description}")
        print(f"  Target: {target_dir}")
        print(f"  Archive input: {archive_input}")
        
        try:
            result = construct_archive_path(target_dir, archive_input)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Expected Error: {e}")
        
        print()

if __name__ == "__main__":
    test_path_construction()
